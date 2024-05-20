import cv2
import face_recognition
import numpy as np
import os

# Load known faces
def load_known_faces(known_faces_dir):
    known_faces = []
    known_names = []
    for filename in os.listdir(known_faces_dir):
        image = face_recognition.load_image_file(os.path.join(known_faces_dir, filename))
        encoding = face_recognition.face_encodings(image)[0]
        known_faces.append(encoding)
        known_names.append(os.path.splitext(filename)[0])
    return known_faces, known_names

# Capture an image from the webcam
def capture_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    return frame

# Recognize faces in the captured image
def recognize_faces(frame, known_faces, known_names):
    rgb_frame = frame[:, :, ::-1]
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    recognized_faces = []
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_faces, face_encoding)
        face_distances = face_recognition.face_distance(known_faces, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            recognized_faces.append(known_names[best_match_index])
        else:
            recognized_faces.append("Unknown")

    return recognized_faces, face_locations

# Main function
def main():
    known_faces_dir = 'known_faces'
    known_faces, known_names = load_known_faces(known_faces_dir)
    
    print("Press 'c' to capture an image.")
    while True:
        key = input()
        if key == 'c':
            frame = capture_image()
            recognized_faces, face_locations = recognize_faces(frame, known_faces, known_names)
            for name, (top, right, bottom, left) in zip(recognized_faces, face_locations):
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)
            cv2.imshow('Face Recognition', frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
