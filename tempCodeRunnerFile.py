import os
import socket
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
####################################_FACE_RECOGNITION_HERE_####################################

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    session['user_name'] = name

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
        registered_image_path = os.path.join(uploads_folder, filename)
        
        # Check if the file exists
        if not os.path.exists(registered_image_path):
            print(f"File not found: {registered_image_path}")
            continue
        
        registered_image = face_recognition.load_image_file(registered_image_path)
        registered_face_encodings = face_recognition.face_encodings(registered_image)

        if not registered_face_encodings:
            print(f"No faces found in the registered image: {registered_image_path}")
            continue

        registered_face_encoding = registered_face_encodings[0]
        matches = face_recognition.compare_faces([registered_face_encoding], login_face_encoding)

        if any(matches):
            session['user_name'] = name  # Store the user's name in the session
            return jsonify({"success": True, "name": name})

    response = {"success": False}
    return jsonify(response)

####################################_SUCCESS_TEMPLATE_###################################################
@app.route("/success")
def success():
    user_name = session.get('user_name')
    if not user_name:
        return redirect(url_for('index'))
    return render_template("success.html", user_name=user_name)
###########################################_RECONIZED_TEXT_#####################################################
@app.route('/recognize', methods=['POST'])
def recognize():
    text = request.form['text']
    print("Recognized text:", text)
    return text
###########################################_DEPOSIT_##################################################################
#UPDATE ACCOUNT SET BALANCE amount 
@app.route('/deposit', methods=['POST', 'GET'])
def deposit():
    if request.method == 'POST':
        action = "deposit"
        amount = request.form.get('amount')  # Use .get() to handle if 'amount' is not in form data
        account_number = session.get('user_name')

        if amount:  # Check if 'amount' is not empty
            try:
                send_data_to_receiver(action, amount,account_number)
                message = f"Deposited amount: {amount}"
                print(message)
                return message
            except Exception as e:
                error_message = f"An error occurred while sending data: {e}"
                print(error_message)
                return error_message, 500  # Return error message with status code 500 (Internal Server Error)
        else:
            return "Amount not provided", 400  # Return error message with status code 400 (Bad Request)
        
    return render_template('deposit.html')

def send_data_to_receiver(action, amount, account_number):
    try:
        # IP address and port of the receiver
        receiver_ip = '10.2.36.37'
        receiver_port = 1003

        # Data to be sent
        data = f"{action},{account_number},{amount}".encode('utf-8')

        # Create a socket object
        sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the receiver
        sender_socket.connect((receiver_ip, receiver_port))

        # Send data
        sender_socket.sendall(data)

        # Close the socket
        sender_socket.close()

    except Exception as e:
        raise RuntimeError(f"An error occurred while sending data to the receiver: {e}")  # Raise exception with error message


#######################################_WITHDRAW_################################################
@app.route('/withdraw', methods=['POST', 'GET'])
def withdraw():
    if request.method == 'POST':
        action = "withdraw"
        amount = request.form.get('amount')  # Use .get() to handle if 'amount' is not in form data
        account_number = session.get('user_name')

        if amount:  # Check if 'amount' is not empty
            try:
                message = f"Withdrawn amount: {amount}"
                print(message)
                send_withdraw_data_to_receiver(action, amount, account_number)
                return message
            except Exception as e:
                error_message = f"An error occurred while sending data: {e}"
                print(error_message)
                return error_message, 500  # Return error message with status code 500 (Internal Server Error)
        else:
            return "Amount not provided", 400  # Return error message with status code 400 (Bad Request)

    return render_template('withdraw.html')

def send_withdraw_data_to_receiver(action, amount, account_number):
    try:
        # IP address and port of the receiver
        receiver_ip = '10.2.41.195'
        receiver_port = 5000

        # Data to be sent
        data = f"{action},{amount},{account_number}".encode('utf-8')

        # Create a socket object
        sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the receiver
        sender_socket.connect((receiver_ip, receiver_port))

        # Send data
        sender_socket.sendall(data)

        # Close the socket
        sender_socket.close()

    except Exception as e:
        raise RuntimeError(f"An error occurred while sending data to the receiver: {e}")  # Raise exception with error message


########################################_SEND_CASH_###########################################
@app.route('/sendcash', methods=['POST', 'GET'])
def sendcash():
    if request.method == 'POST':
        action = "sendcash"
        amount = request.form.get('amount')  # Use .get() to handle if 'amount' is not in form data
        from_account = request.form.get('from_account')  # Use .get() to handle if 'from_account' is not in form data
        to_account = request.form.get('to_account')  # Use .get() to handle if 'to_account' is not in form data

        if amount and from_account and to_account:  # Check if all required data is provided
            try:
                message = f"Sending amount: R{amount} \nTO THIS ACCOUNT: ****{to_account}**** \nFROM THIS ACCOUNT: ****{from_account}****"
                print(message)
                send_cash_data_to_receiver(action, amount, from_account, to_account)
                return message
            except Exception as e:
                error_message = f"An error occurred while sending data: {e}"
                print(error_message)
                return error_message, 500  # Return error message with status code 500 (Internal Server Error)
        else:
            return "Incomplete data provided", 400  # Return error message with status code 400 (Bad Request)

    return render_template('sendcash.html')

def send_cash_data_to_receiver(action, amount, from_account, to_account):
    try:
        # IP address and port of the receiver
        receiver_ip = '10.2.41.195'
        receiver_port = 5000

        # Data to be sent
        data = f"{action},{amount},{from_account},{to_account}".encode('utf-8')

        # Create a socket object
        sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the receiver
        sender_socket.connect((receiver_ip, receiver_port))

        # Send data
        sender_socket.sendall(data)

        # Close the socket
        sender_socket.close()

    except Exception as e:
        raise RuntimeError(f"An error occurred while sending data to the receiver: {e}")  # Raise exception with error message


############################################_CHECK_BALANCE_#########################################
@app.route('/checkbalance', methods=['POST', 'GET'])
def checkbalance():
    action = "checkbalance"
    account_number = session.get('user_name')
    data_received = send_data_read_to_receiver(action,account_number)

    if data_received is not None:
        try:
            data_parts = data_received.split(',')
            if len(data_parts) >= 5:  # Check if received data has at least 5 parts
                transaction_id, transaction_type, amount, account_type, account = data_parts[:5]
                displayed_data = f"Amount: {amount}\nAccount Type: {account_type}\nAccount Number: {account}"
                return render_template('checkbalance.html', data=displayed_data)
            else:
                return "Incomplete data received"
        except Exception as e:
            return f"Error occurred while processing received data: {e}"  # Return error message with details
    else:
        return "An error occurred while sending/receiving data. Either data does not exist"

def send_data_read_to_receiver(action,account_number):
    try:
        # IP address and port of the receiver
        receiver_ip = '192.168.198.67'
        receiver_port = 5000

        # Data to be sent
        data = f"{action},{account_number}".encode('utf-8')

        # Create a socket object
        sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the receiver
        sender_socket.connect((receiver_ip, receiver_port))

        # Send data
        sender_socket.sendall(data)

        # Receive response from the receiver
        received_data = sender_socket.recv(1024)  # Receive up to 1024 bytes of data
        received_data = received_data.decode('utf-8')

        # Close the socket
        sender_socket.close()

        return received_data

    except Exception as e:
        raise RuntimeError(f"An error occurred while sending/receiving data: {e}")  # Raise exception with error message
####################################_STATEMENT_##########################################
@app.route('/statement', methods=['POST', 'GET'])
def print_Statement():
    action = "statement"
    account_number = session.get('user_name')
    data_received = send_data_read_to_receiver(action,account_number)

    if data_received is not None:
        try:
            data_parts = data_received.split(',')
            if len(data_parts) >= 5:  # Check if received data has at least 5 parts
                transaction_id, transaction_type, amount, account_type, account = data_parts[:5]
                displayed_data = f"Transaction ID: {transaction_id}\nTransaction type: {transaction_type}\nAmount: {amount}\nAccount Type: {account_type}\nAccount Number: {account}"
                return render_template('statement.html', data=displayed_data)
            else:
                return "Incomplete data received"
        except Exception as e:
            return f"Error occurred while processing received data: {e}"  # Return error message with details
    else:
        return "An error occurred while sending/receiving data. Either data does not exist"


def send_data_read_to_receiver(action,account_number):
    try:
        # IP address and port of the receiver
        receiver_ip = '192.168.198.67'
        receiver_port = 5000

        # Data to be sent
        data = f"{action},{account_number}".encode('utf-8')

        # Create a socket object
        sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the receiver
        sender_socket.connect((receiver_ip, receiver_port))

        # Send data
        sender_socket.sendall(data)

        # Receive response from the receiver
        received_data = sender_socket.recv(1024)  # Receive up to 1024 bytes of data
        received_data = received_data.decode('utf-8')

        # Close the socket
        sender_socket.close()

        return received_data

    except Exception as e:
        raise RuntimeError(f"An error occurred while sending/receiving data: {e}")  # Raise exception with error message


if __name__ == "__main__":
    app.run(debug=True, port=1003)
