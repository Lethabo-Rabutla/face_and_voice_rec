import os
import cv2
import datetime
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import face_recognition
import psycopg2
from psycopg2 import OperationalError

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Create a variable register
register_data = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")

    # Get photo uploads
    photo = request.files['photo']

    # Save the photo to uploads folder during registration
    upload_folder = os.path.join(os.getcwd(), "static", "uploads")

    # Create the uploads folder if not exists
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Save the photo image with the file name containing the current date
    filename = f"{datetime.date.today()}_{name}.jpg"
    photo_path = os.path.join(upload_folder, filename)
    photo.save(photo_path)
    register_data[name] = filename

    # Send success response
    response = {"success": True, 'name': name}
    return jsonify(response)

@app.route("/login", methods=["POST"])
def login():
    photo = request.files['photo']

    # Save the photo to the uploads folder
    uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)

    login_filename = os.path.join(uploads_folder, "login_face.jpg")
    photo.save(login_filename)

    # Load the login image
    login_image = face_recognition.load_image_file(login_filename)
    login_face_encodings = face_recognition.face_encodings(login_image)

    if not login_face_encodings:
        response = {"success": False}
        return jsonify(response)

    login_face_encoding = login_face_encodings[0]

    for name, filename in register_data.items():
        registered_image = face_recognition.load_image_file(os.path.join(uploads_folder, filename))
        registered_face_encodings = face_recognition.face_encodings(registered_image)

        if not registered_face_encodings:
            continue

        registered_face_encoding = registered_face_encodings[0]
        matches = face_recognition.compare_faces([registered_face_encoding], login_face_encoding)

        if any(matches):
            session['user_name'] = name  # Store the user's name in the session
            return jsonify({"success": True, "name": name})

    response = {"success": False}
    return jsonify(response)

@app.route("/success")
def success():
    user_name = session.get('user_name')
    if not user_name:
        return redirect(url_for('index'))
    return render_template("success.html", user_name=user_name)

@app.route('/recognize', methods=['POST'])
def recognize():
    text = request.form['text']
    print("Recognized text:", text)
    return text

#UPDATE ACCOUNT SET BALANCE amount 
@app.route('/deposit', methods=['POST', 'GET'])
def deposit():
    if request.method == 'POST':
        amount = request.form['amount']
        conn = connect()
        if conn:
            try:
                cursor = conn.cursor()
                # Example: Update account balance
                # cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, account_number))
                conn.commit()
                print(f"Deposited amount: {amount}")
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                cursor.close()
                conn.close()
        return "Deposit successful!"
    return render_template('deposit.html')



@app.route('/withdraw', methods=['POST', 'GET'])
def withdraw():
    if request.method == 'POST':
        amount = request.form['amount']
        conn = connect()
        if conn:
            try:
                cursor = conn.cursor()
                # Example: Update account balance
                # cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, account_number))
                conn.commit()
                print(f"Withdrawn amount: {amount}")
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                cursor.close()
                conn.close()
        return "Withdraw successful!"
    return render_template('withdraw.html')

@app.route('/sendcash', methods=['POST', 'GET'])
def sendcash():
    if request.method == 'POST':
        amount = request.form['amount']
        account_handler = request.form['accounthandler']
        account_number = request.form['accountnumber']
        conn = connect()
        if conn:
            try:
                cursor = conn.cursor()
                # Example: Transfer amount to another account
                # cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_number = %s", (amount, sender_account_number))
                # cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, account_number))
                conn.commit()
                print(f"Sending amount: {amount} to {account_handler} {account_number}")
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                cursor.close()
                conn.close()
        return f"Sending to: {account_handler} {account_number}"
    return render_template('sendcash.html')

@app.route('/checkbalance', methods=['POST', 'GET'])
def checkbalance():
    account_number = "1234567890"
    balance = 5000.00  # Example balance
    return render_template('checkbalance.html', account_number=account_number, balance=balance)

def connect():
    try:
        conn = psycopg2.connect(
            dbname="testingDB",
            user="postgres",
            password="123",
            host="localhost",
            port="5432"
        )
        print("Connected to the database")
        return conn
    except OperationalError as e:
        print(f"Error connecting to database: {e}")
        return None

if __name__ == "__main__":
    app.run(debug=True, port=1003)
