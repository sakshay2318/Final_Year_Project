import face_recognition_api
import cv2
import os
import pickle
import numpy as np
import warnings
from datetime import datetime

# Basic performance tweaks to make things run faster:
video_capture = cv2.VideoCapture(0)

# Load Face Recognizer classifier
fname = 'classifier.pkl'
if os.path.isfile(fname):
    with open(fname, 'rb') as f:
        (le, clf) = pickle.load(f)
else:
    print(f"Classifier '{fname}' does not exist")
    quit()

# Initialize variables
face_locations = []
face_encodings = []
process_this_frame = True
log_file = './lock_file.log'

def log_recognition(name):
    """Log recognized face with timestamp."""
    with open(log_file, 'a') as f:
        log_entry = f"{name} recognized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f.write(log_entry)
        print(log_entry)  # Also print to the console for debugging

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    while True:
        # Capture a single frame of video
        ret, frame = video_capture.read()

        if not ret:
            print("Failed to capture frame from video source.")
            break

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        if process_this_frame:
            # Detect faces and generate encodings
            face_locations = face_recognition_api.face_locations(small_frame)
            face_encodings = face_recognition_api.face_encodings(small_frame, face_locations)

            predictions = []
            if len(face_encodings) > 0:
                # Get the closest distances and check recognition threshold
                closest_distances = clf.kneighbors(face_encodings, n_neighbors=1)
                is_recognized = [closest_distances[0][i][0] <= 0.5 for i in range(len(face_locations))]

                predictions = [
                    (le.inverse_transform([int(pred)])[0].title(), loc) if rec else ("Unknown", loc)
                    for pred, loc, rec in zip(clf.predict(face_encodings), face_locations, is_recognized)
                ]

                # Log recognized faces
                for name, _ in predictions:
                    if name != "Unknown":
                        log_recognition(name)
                    else:
                        print("Unrecognized face detected.")

        process_this_frame = not process_this_frame

        # Draw boxes around faces and display names
        for name, (top, right, bottom, left) in predictions:
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # Show video feed with faces
        cv2.imshow('Video', frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting webcam feed.")
            break

    # Release the webcam and close windows
    video_capture.release()
    cv2.destroyAllWindows()
