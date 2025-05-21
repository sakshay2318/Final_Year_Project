import threading
import time
import logging
from iam import get_employees
from etl_pipeline import get_pipelines, save_pipeline, upload_to_ipfs
from blockchain import get_data_from_blockchain, store_to_blockchain
from config import IPFS_API_URL, IPFS_RETRIEVE_URL, SECURITY_KEYS
from security_policy import decrypt_data, encrypt_data
import requests
import threading, time, json, logging, os
from datetime import datetime, timedelta
from iam import enroll_mfa, lock_employee
from etl_pipeline import get_pipelines

log = logging.getLogger("AI_AGENTS")
log.setLevel(logging.INFO)
LOG_FILE = "access_log.jsonl"

class IntrusionDetector(threading.Thread):
    """
    Monitors access_log.jsonl for:
    1) >3 failures in 5min by same user → enroll_mfa
    2) cross-account attempts → lock_employee
    """
    WINDOW = timedelta(minutes=5)
    MAX_FAILS = 3

    def run(self):
        while True:
            now = datetime.utcnow()
            events = []
            try:
                with open(LOG_FILE) as f:
                    for line in f:
                        evt = json.loads(line)
                        evt_time = datetime.utcfromtimestamp(evt["timestamp"])
                        if now - evt_time <= self.WINDOW:
                            events.append(evt)
            except FileNotFoundError:
                pass

            # 1) repeated failures → enroll in MFA
            fails = {}
            for evt in events:
                if not evt["success"]:
                    fails.setdefault(evt["employee_id"], set()).add(evt["record_id"])
            for uid, recs in fails.items():
                if len(recs) > self.MAX_FAILS:
                    log.warning(f"[Intrusion] {uid} had {len(recs)} failures; enrolling MFA")
                    enroll_mfa(uid)

            # 2) cross-account fails → lock account
            owner_map = {p["record_id"]: p["employee_id"] for p in get_pipelines()}
            for evt in events:
                if not evt["success"]:
                    rid, uid = evt["record_id"], evt["employee_id"]
                    owner = owner_map.get(rid)
                    if owner and owner != uid:
                        log.warning(f"[CrossAuth] {uid} tried {rid} owned by {owner}; locking account")
                        lock_employee(uid)

            time.sleep(30)

def send_alert(record_id, old_hash, new_hash):
    """Placeholder: send an email or webhook alert."""
    log.error(f"[IntegrityAlert] Record {record_id}: IPFS hash rotated " f"{old_hash} → {new_hash}")
    # e.g. requests.post(ALERT_WEBHOOK_URL, json={...})


class IntegrityValidator(threading.Thread):
    """
    Every 10 minutes:
    1) Fetch encrypted blob from IPFS
    2) Decrypt → re-encrypt → re-upload
    3) If new CID ≠ stored CID:
        • update pipelines.json
        • update blockchain metadata
        • send_alert
    """

    INTERVAL = 600  # seconds

    def run(self):
        while True:
            pipelines = get_pipelines()
            for p in pipelines:
                rec_id = p["record_id"]
                old_cid = p["ipfsHash"]
                sec_level = p.get("security_level") or p.get("securityLevel")
                try:
                    # 1) fetch encrypted payload
                    res = requests.get(f"{IPFS_API_URL}/cat?arg={old_cid}")
                    res.raise_for_status()
                    encrypted_b64 = res.text.encode()

                    # 2) decrypt/re-encrypt
                    data = decrypt_data(encrypted_b64, sec_level)
                    new_b64 = encrypt_data(data, sec_level)

                    # 3) upload back to IPFS
                    new_cid = upload_to_ipfs(new_b64)
                    if new_cid != old_cid:
                        log.warning(f"[IntegrityFix] {rec_id}: CID changed")
                        # update local JSON
                        p["ipfsHash"] = new_cid
                        save_pipeline(p)
                        # update blockchain metadata
                        store_to_blockchain(new_cid, sec_level)
                        # alert ops
                        send_alert(rec_id, old_cid, new_cid)
                    else:
                        log.info(f"[Integrity] {rec_id} OK")
                except Exception as e:
                    log.error(f"[IntegrityErr] {rec_id} failed: {e}")
            time.sleep(self.INTERVAL)



class UsageBasedLevelAdjuster(threading.Thread):
    """
    Every 24h:
    • Count successful retrieves of pipelines with securityLevel ≥ SENSITIVITY_CUTOFF.
    • If count > USAGE_THRESHOLD, bump user’s securityLevel by +1 (max len(SECURITY_KEYS)).
    """
    WINDOW = timedelta(hours=24)
    USAGE_THRESHOLD = 10
    SENSITIVITY_CUTOFF = 4

    def run(self):
        while True:
            now = datetime.utcnow()
            # load events
            events = []
            try:
                with open(LOG_FILE) as f:
                    for line in f:
                        evt = json.loads(line)
                        t = datetime.utcfromtimestamp(evt["timestamp"])
                        if now - t <= self.WINDOW and evt["success"]:
                            events.append(evt)
            except FileNotFoundError:
                pass

            # build record→sensitivity map
            record_sens = {
                p["record_id"]: int(p.get("security_level", p.get("securityLevel", 1)))
                for p in get_pipelines()
            }
            counts = {}
            for e in events:
                lvl = record_sens.get(e["record_id"], 0)
                if lvl >= self.SENSITIVITY_CUTOFF:
                    counts[e["employee_id"]] = counts.get(e["employee_id"], 0) + 1

            for uid, cnt in counts.items():
                if cnt > self.USAGE_THRESHOLD:
                    emp = next((e for e in get_employees() if e["employee_id"] == uid), None)
                    if emp:
                        cur = int(emp["securityLevel"])
                        if cur < len(SECURITY_KEYS):
                            new = cur + 1
                            set_security_level(uid, new)
                            log.info(f"[RiskAdjust] {uid}: usage {cnt}, level {cur}→{new}")
            time.sleep(24*3600)


class DormancyMonitor(threading.Thread):
    """
    Every 24h:
    • Lock any account with no successful access in last 30 days.
    """
    WINDOW = timedelta(days=30)

    def run(self):
        while True:
            now = datetime.utcnow()
            active = set()
            try:
                with open(LOG_FILE) as f:
                    for line in f:
                        evt = json.loads(line)
                        t = datetime.utcfromtimestamp(evt["timestamp"])
                        if now - t <= self.WINDOW and evt["success"]:
                            active.add(evt["employee_id"])
            except FileNotFoundError:
                pass

            for emp in get_employees():
                uid = emp["employee_id"]
                if uid not in active:
                    log.warning(f"[Dormancy] {uid} inactive → locking account")
                    lock_employee(uid)
            time.sleep(24*3600)




def start_all_agents():
    IntrusionDetector(daemon=True).start()
    IntegrityValidator(daemon=True).start()
    UsageBasedLevelAdjuster(daemon=True).start()
    DormancyMonitor(daemon=True).start()
    log.info("All AI agents started.")
