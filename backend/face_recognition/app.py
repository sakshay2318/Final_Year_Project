import os
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

TRAINING_IMAGES_DIR = './training-images'
LOG_FILE = './lock_file.log'

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
        subprocess.run(['python', 'create_encodings.py'], check=True)  # Ensure this completes first
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Error in creating encodings: {e}'}), 500

    # Now run the training script
    try:
        subprocess.run(['python', 'train.py'], check=True)  # Only runs if create_encodings.py is successful
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

@app.route('/start_webcam', methods=['POST'])
def start_webcam():
    try:
        # Run the webcam.py script in a separate process
        subprocess.Popen(['python', './webcam.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify({'message': 'Webcam started successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
