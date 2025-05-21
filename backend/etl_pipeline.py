import requests
import base64
from cryptography.fernet import Fernet
from blockchain import store_to_blockchain, get_data_from_blockchain
from config import IPFS_API_URL, SECURITY_KEYS
import json
import uuid

PIPELINES_FILE = "pipelines.json"

def save_pipeline(pipeline_data):
    """Save a new pipeline to the JSON file."""
    pipelines = get_pipelines()  # Ensure this returns a list
    if not isinstance(pipelines, list):  # Add safeguard
        pipelines = []
    # Generate a unique record_id (serial number) for each pipeline
    record_id = str(uuid.uuid4())  # Create a unique ID
    pipeline_data['record_id'] = record_id  # Add the record ID to the pipeline data
    pipelines.append(pipeline_data)
    with open(PIPELINES_FILE, "w") as file:
        json.dump(pipelines, file, indent=4)
    return record_id  # Return the serial number of the new pipeline

def get_pipelines():
    """Retrieve all pipelines from the JSON file."""
    try:
        with open(PIPELINES_FILE, "r") as file:
            pipelines = json.load(file)
            if not isinstance(pipelines, list):  # Safeguard for data corruption
                raise ValueError("Pipelines data is not a valid list.")
            return pipelines
    except(FileNotFoundError, ValueError) as e:
        return []

def encrypt_data(data, security_level):
    """Encrypt binary data based on the security level."""
    key = SECURITY_KEYS[security_level - 1]
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)  # Encrypt using Fernet
    encoded_data = base64.b64encode(encrypted_data).decode('utf-8')  # Base64 encode
    return encoded_data  # Return as base64 string

def decrypt_data(encrypted_data, security_level):
    """Decrypt binary data based on the security level."""
    key = SECURITY_KEYS[security_level - 1]
    fernet = Fernet(key)
    try:
        # Decode from base64 and then decrypt using Fernet
        encrypted_data_bytes = base64.b64decode(encrypted_data)
        decrypted_data = fernet.decrypt(encrypted_data_bytes)
        return decrypted_data
    except Exception as e:
        print(f"Decryption error: {e}")
        raise ValueError("Failed to decrypt the data. Check encryption/decryption consistency.")

def upload_to_ipfs(data):
    """Upload binary data to IPFS."""
    response = requests.post(f"{IPFS_API_URL}/add", files={"file": data})
    if response.status_code == 200:
        return response.json().get("Hash")
    raise Exception(f"Failed to upload to IPFS: {response.text}")

def extract_data(file):
    """Extract binary data from the uploaded file."""
    return file.read()

def transform_data(data, security_level):
    """Encrypt data and upload to IPFS."""
    encrypted_data = encrypt_data(data, security_level)
    ipfs_hash = upload_to_ipfs(encrypted_data)
    print(f"Data uploaded to IPFS with hash: {ipfs_hash}")
    return ipfs_hash


# In etl_pipeline.py
def load_data(ipfs_hash, security_level):
    """Store IPFS hash and security level in the blockchain."""
    store_to_blockchain(ipfs_hash, security_level)  # Pass both IPFS hash and security level

def run_etl_pipeline(file, security_level):
    """Run the ETL pipeline with filename and content type."""
    filename = file.filename
    mimetype = file.mimetype
    data = extract_data(file)
    ipfs_hash = transform_data(data, security_level)
    load_data(ipfs_hash, security_level)
    return {
        "ipfs_hash": ipfs_hash,
        "filename": filename,
        "mimetype": mimetype
    }


# def retrieve_from_pipeline(record_id):
#     """Retrieve and decrypt data."""
#     blockchain_data = get_data_from_blockchain(record_id)
#     ipfs_hash, security_level = blockchain_data[1], int(blockchain_data[2])

#     response = requests.get(f"{IPFS_API_URL}/cat?arg={ipfs_hash}")
#     if response.status_code == 200:
#         encrypted_data = response.content
#         decrypted_data = decrypt_data(encrypted_data, security_level)
#         return decrypted_data.decode('utf-8')  # Assuming the decrypted data is text.
#     raise Exception("Failed to retrieve data from IPFS")
