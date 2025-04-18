import json
import requests
from config import IPFS_API_URL

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


