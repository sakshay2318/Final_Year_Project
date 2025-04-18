import io
import json
import logging
import os
import subprocess
from datetime import datetime

import pandas as pd  # Add this for processing log data
import requests
from blockchain import get_data_from_blockchain
from config import IPFS_API_URL, IPFS_RETRIEVE_URL, SECURITY_KEYS
from etl_pipeline import (decrypt_data, encrypt_data, get_pipelines,
                          run_etl_pipeline, save_pipeline)
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from iam import (add_employee, delete_employee_from_list, get_employee_by_id,
                 get_employees, update_employee_file)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder='../client/build', static_url_path='/')
CORS(app)

@app.route('/upload', methods=['POST'])
def upload():
    """Upload investigation document."""
    file = request.files.get('file')
    employee_id = request.form.get('employee_id')
    pipeline_name = request.form.get('pipeline_name')

    if not file or not employee_id or not pipeline_name:
        return jsonify({"error": "File, Employee ID, and Pipeline Name are required."}), 400

    try:
        employee = get_employee_by_id(employee_id)
        if not employee:
            return jsonify({"error": "Invalid Employee ID."}), 400

        security_level = employee.get('securityLevel')
        if security_level is None:
            return jsonify({"error": f"Employee {employee_id} is missing 'securityLevel'."}), 400

        transformed_data = run_etl_pipeline(file, security_level)

        # Ensure transformed_data is a dictionary
        ipfs_hash = transformed_data.get('ipfs_hash')
        if not ipfs_hash:
            raise Exception("ETL pipeline did not return a valid IPFS hash.")

        # Save the new pipeline with a unique record_id
        pipeline_data = {
            "pipelineName": pipeline_name,
            "employee_id": employee_id,
            "ipfsHash": ipfs_hash
        }
        record_id = save_pipeline(pipeline_data)

        return jsonify({
            "message": "Upload and encryption successful.",
            "pipeline_name": pipeline_name,
            "employee_id": employee_id,
            "ipfs_hash": ipfs_hash,
            "record_id": record_id  # Include the unique record ID in the response
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pipelines', methods=['GET'])
def get_all_pipelines():
    """Retrieve all pipelines."""
    try:
        pipelines = get_pipelines()
        return jsonify(pipelines)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pipelines', methods=['POST'])
def create_pipeline():
    """Create a new pipeline."""
    try:
        data = request.json
        pipeline_name = data.get("pipelineName")
        employee_id = data.get("employee_id")
        ipfs_hash = data.get("ipfsHash")

        if not pipeline_name or not employee_id or not ipfs_hash:
            return jsonify({"error": "Pipeline Name, Employee ID, and IPFS Hash are required."}), 400

        pipeline_data = {
            "pipelineName": pipeline_name,
            "employee_id": employee_id,
            "ipfsHash": ipfs_hash
        }
        save_pipeline(pipeline_data)
        
        return jsonify({
            "message": "Upload and encryption successful.",
            "pipeline_name": pipeline_name,
            "employee_id": employee_id,
            "ipfs_hash": ipfs_hash
        })
        
        return jsonify({"message": "Pipeline created successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/retrieve', methods=['POST'])
def retrieve():
    """Retrieve and decrypt data from IPFS."""
    employee_id = request.json.get('employee_id')
    security_level = request.json.get('security_level')
    record_id = request.json.get('record_id')
    ipfs_hash = request.json.get('ipfs_hash')

    try:
        logging.info(f"Received retrieve request: employee_id={employee_id}, "
                    f"security_level={security_level}, record_id={record_id}, ipfs_hash={ipfs_hash}")

        # Validate input
        if not employee_id or security_level is None or not record_id or not ipfs_hash:
            raise ValueError("Employee ID, Security Level, Record ID, and IPFS Hash are required.")

        # Validate employee and security level
        employee = get_employee_by_id(employee_id)
        if not employee or int(employee['securityLevel']) != int(security_level):
            raise PermissionError("Invalid Employee ID or Security Level mismatch.")

        # Retrieve from IPFS
        ipfs_url = f"{IPFS_RETRIEVE_URL}/{ipfs_hash}"
        logging.info(f"Retrieving data from IPFS URL: {ipfs_url}")
        response = requests.get(ipfs_url)

        if response.status_code != 200:
            raise ConnectionError(f"Failed to retrieve data from IPFS: {response.status_code} - {response.text}")

        encrypted_data = response.content
        logging.info(f"Retrieved {len(encrypted_data)} bytes of encrypted data from IPFS.")

        # Decrypt data
        decrypted_data = decrypt_data(encrypted_data, security_level)
        logging.info("Data decrypted successfully.")

        try:
            decoded_data = decrypted_data.decode('utf-8')
            return jsonify({
                "message": "Data retrieved and decrypted successfully.",
                "data": decoded_data
            })
        except UnicodeDecodeError:
            logging.info("Decrypted data is binary, sending as a file.")
            return send_file(
                io.BytesIO(decrypted_data),
                mimetype='application/octet-stream',
                as_attachment=True,
                download_name="retrieved_file"
            )
    except Exception as e:
        logging.error(f"Error in /retrieve: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/employees', methods=['GET'])
def fetch_employees():
    """Retrieve all employees from the aggregated IPFS file."""
    try:
        # Load the current employee file from IPFS
        employees = get_employees()
        return jsonify(employees)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/employees', methods=['POST'])
def add_new_employee():
    try:
        logging.info("Received employee addition request: %s", request.json)
        data = request.json
        add_employee(data)
        update_employee_file()
        return jsonify({"message": "Employee added successfully."}), 201
    except ValueError as ve:
        logging.error("Validation error: %s", ve)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/employees/<string:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Delete an employee by employee ID."""
    try:
        delete_status = delete_employee_from_list(employee_id)
        if delete_status:
            update_employee_file()  # Reflect changes in IPFS
            return jsonify({"message": "Employee deleted successfully."}), 200
        else:
            return jsonify({"error": "Employee not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

TRAINING_IMAGES_DIR = './face_recognition/training-images'
LOG_FILE = './face_recognition/lock_file.log'

@app.route('/uploadimages', methods=['POST'])
def upload_images():
    if 'name' not in request.form or 'images' not in request.files:
        return jsonify({'error': 'Invalid input'}), 400
    name = request.form['name'].strip()
    images = request.files.getlist('images')
    person_dir = os.path.join(TRAINING_IMAGES_DIR, name)

    # Create a directory for the person if it doesn't exist
    os.makedirs(person_dir, exist_ok=True)

    for image in images:
        image.save(os.path.join(person_dir, image.filename))

    # Run the create_encodings script to generate the necessary CSV and pkl files
    try:
        subprocess.run(['python', './face_recognition/create_encodings.py'], check=True)  # Ensure this completes first
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Error in creating encodings: {e}'}), 500

    # Now run the training script
    try:
        subprocess.run(['python', './face_recognition/train.py'], check=True)  # Only runs if create_encodings.py is successful
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Error during training: {e}'}), 500

    return jsonify({'message': f'Images for {name} uploaded and trained successfully!'}), 200

@app.route('/log', methods=['GET'])
def fetch_log():
    if not os.path.exists(LOG_FILE):
        return jsonify({'error': 'Log file not found'}), 404

    with open(LOG_FILE, 'r') as f:
        logs = f.read()

    return jsonify({'logs': logs}), 200


# New function: Parse log file and fetch unique daily recognition entries
def parse_recognition_log():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, 'r') as f:
        logs = f.readlines()

    # Parse logs into a DataFrame
    data = []
    for log in logs:
        if "recognized at" in log:
            name, timestamp = log.split(" recognized at ")
            date = timestamp.split(" ")[0]
            data.append({"name": name.strip(), "date": date})

    df = pd.DataFrame(data)
    if df.empty:
        return []

    # Drop duplicates: Ensure only one entry per name per day
    df_unique = df.drop_duplicates(subset=["name", "date"])
    return df_unique.to_dict(orient="records")

@app.route('/recognition_data', methods=['GET'])
def get_recognition_data():
    try:
        data = parse_recognition_log()
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/start_webcam', methods=['POST'])
def start_webcam():
    try:
        # Run the webcam.py script in a separate process
        subprocess.Popen(['python', './face_recognition/webcam.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify({'message': 'Webcam started successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)