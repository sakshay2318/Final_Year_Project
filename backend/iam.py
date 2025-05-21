import json
import requests
from config import IPFS_API_URL
import os

EMPLOYEE_FILE = "employees.json"

def get_employees():
    """Fetch all employee data."""
    try:
        with open(EMPLOYEE_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    
# In iam.py
def get_employee_by_id(employee_id):
    """Retrieve employee details by employee ID."""
    employees = get_employees()
    for employee in employees:
        if employee["employee_id"] == employee_id:
            # Validate if 'securityLevel' exists
            if 'securityLevel' not in employee:
                raise ValueError(f"Employee record for {employee_id} is missing the 'securityLevel' field.")
            return employee
    return None

def add_employee(employee_data):
    """Add a new employee to the list if the employee ID is unique."""
    employees = get_employees()
    if any(emp.get("employee_id") == employee_data.get("employee_id") for emp in employees):
        raise ValueError(f"Employee ID {employee_data['employee_id']} already exists.")
    employees.append(employee_data)
    with open(EMPLOYEE_FILE, "w") as file:
        json.dump(employees, file)

def update_employee_file():
    """Store the aggregated employee file in IPFS."""
    with open(EMPLOYEE_FILE, "rb") as file:
        response = requests.post(f"{IPFS_API_URL}/add", files={"file": file})
        if response.status_code == 200:
            ipfs_hash = response.json().get("Hash")
            print(f"File uploaded to IPFS with hash: {ipfs_hash}")
        else:
            raise Exception(f"Failed to upload file to IPFS: {response.text}")
        
def delete_employee_from_list(employee_id):
    """Delete an employee from the list."""
    employees = get_employees()
    filtered_employees = [emp for emp in employees if emp.get("employee_id") != employee_id]
    
    if len(filtered_employees) < len(employees):
        with open(EMPLOYEE_FILE, "w") as file:
            json.dump(filtered_employees, file)
        return True
    return False

# iam.py (append at bottom)

LOCKED_FILE = "locked_users.json"

def enroll_mfa(employee_id):
    """Mark an employee as requiring MFA on next login."""
    data = get_employees()
    for emp in data:
        if emp["employee_id"] == employee_id:
            emp["require_mfa"] = True
    with open(EMPLOYEE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    update_employee_file()  # push to IPFS

def lock_employee(employee_id):
    """Lock an employee's account temporarily."""
    try:
        locked = []
        if os.path.exists(LOCKED_FILE):
            locked = json.load(open(LOCKED_FILE))
        if employee_id not in locked:
            locked.append(employee_id)
            with open(LOCKED_FILE, "w") as f:
                json.dump(locked, f, indent=2)
            # Optionally notify front-end or write to blockchain
    except Exception as e:
        print(f"Failed to lock {employee_id}: {e}")
        
def set_security_level(employee_id, level):
    """Update an employee’s securityLevel and persist via IPFS."""
    emps = get_employees()
    for e in emps:
        if e["employee_id"] == employee_id:
            e["securityLevel"] = level
    with open(EMPLOYEE_FILE, "w") as f:
        json.dump(emps, f)
    update_employee_file()




