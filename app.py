import os
import socket
import cv2
from datetime import datetime
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import face_recognition
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2 import OperationalError,sql,Error

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection parameters
DB_PARAMS = {
    'dbname': 'VVSDB',
    'user': 'postgres',
    'password': '123',
    'host': '192.168.1.69',
    'port': '5432'
}

# Create a database connection pool
connection_pool = SimpleConnectionPool(1, 10, **DB_PARAMS)


@app.teardown_appcontext
def close_connection(exception=None):
    """Close the connection at the end of the request."""
    connection = connection_pool.getconn()
    connection.commit()
    connection_pool.putconn(connection)

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
    date_str = datetime.today().strftime("%Y-%m-%d")
    filename = f"{date_str}_{name}.jpg"
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
                send_data_to_receiver(action, amount, account_number)
                displayed_data = f"Deposited amount: {amount}"
                print(displayed_data)
                return displayed_data
            except Exception as e:
                error_message = f"An error occurred while sending data: {e}"
                print(error_message)
                return error_message, 500  # Return error message with status code 500 (Internal Server Error)
        else:
            return "Amount not provided", 400  # Return error message with status code 400 (Bad Request)

    return render_template('deposit.html')


def send_data_to_receiver(action, amount, account_number):
    connection = None
    cursor = None
    try:
        # Connect to your PostgreSQL database
        connection = connection_pool.getconn()  # Get connection from the pool
        cursor = connection.cursor()

        # Get current timestamp with timezone
        timestamp = datetime.now().astimezone()

        # Update the balance directly
        update_balance_query = sql.SQL(
            "UPDATE transactions SET amount = amount + %s WHERE accountnumber = %s"
        ).format(sql.Identifier('Accounts'))
        cursor.execute(update_balance_query, (amount, account_number))

        # Insert the transaction into the Transactions table
        insert_transaction_query = sql.SQL(
            "INSERT INTO transactions (action, amount, accountnumber, timestamp) VALUES (%s, %s, %s, %s)"
        ).format(sql.Identifier('Transactions'))
        cursor.execute(insert_transaction_query, (action, amount, account_number, timestamp))

        # Commit the transaction
        connection.commit()

    except (Exception) as error:
        print("Error while processing the transaction", error)
        if connection:
            connection.rollback()  # Roll back the transaction in case of error
        raise

    finally:
        # Close the cursor and connection to avoid memory leaks
        if cursor:
            cursor.close()
        if connection:
            connection.close()
##########################################_WITHDRAW_####################################
@app.route('/withdraw', methods=['POST', 'GET'])
def withdraw():
    if request.method == 'POST':
        action = "withdraw"
        amount = request.form.get('amount')  # Use .get() to handle if 'amount' is not in form data
        account_number = session.get('user_name')

        if amount:  # Check if 'amount' is not empty
            try:
                send_withdraw_data_to_receiver(action, amount, account_number)
                message = f"Withdrawn amount: {amount}"
                print(message)
                return message
            except Exception as e:
                error_message = f"An error occurred while processing the withdrawal: {e}"
                print(error_message)
                return error_message, 500  # Return error message with status code 500 (Internal Server Error)
        else:
            return "Amount not provided", 400  # Return error message with status code 400 (Bad Request)

    return render_template('withdraw.html')

def send_withdraw_data_to_receiver(action, amount, account_number):
    connection = None
    cursor = None
    try:
        # Connect to your PostgreSQL database
        connection = connection_pool.getconn()  # Get connection from the pool
        cursor = connection.cursor()

        # Get current timestamp with timezone
        timestamp = datetime.now().astimezone()

        # Check if the withdrawal amount is valid
        cursor.execute("SELECT amount FROM transactions WHERE accountnumber = %s", (account_number,))
        balance = float(cursor.fetchone()[0]) 
        balance = float(balance)  # Convert balance to float
        if float(balance) < float(amount):
            raise ValueError("Insufficient balance")

        # Update the balance directly
        update_balance_query = sql.SQL(
            "UPDATE transactions SET amount = amount - %s WHERE accountnumber = %s"
        ).format(sql.Identifier('Accounts'))
        cursor.execute(update_balance_query, (amount, account_number))

        # Insert the transaction into the Transactions table
        insert_transaction_query = sql.SQL(
            "INSERT INTO transactions (action, amount, accountnumber, timestamp) VALUES (%s, %s, %s, %s)"
        ).format(sql.Identifier('Transactions'))
        cursor.execute(insert_transaction_query, (action, amount, account_number,  timestamp))

        # Commit the transaction
        connection.commit()

    except (Exception) as error:
        print("Error while processing the withdrawal", error)
        if connection:
            connection.rollback()  # Roll back the transaction in case of error
        raise

    finally:
        # Close the cursor and connection to avoid memory leaks
        if cursor:
            cursor.close()
        if connection:
            connection.close()
########################################_SEND_CASH_###########################################
@app.route('/sendcash', methods=['POST', 'GET'])
def sendcash():
    if request.method == 'POST':
        action = "sendcash"
        amount = request.form.get('amount')
        from_account = request.form.get('from_account')
        to_account = request.form.get('to_account')

        if amount and from_account and to_account:
            try:
                # Update the database
                send_cash_data_to_db(action, amount, from_account, to_account)

                # Prepare the message
                message = f"Sending amount: R{amount} \nTO THIS ACCOUNT: ****{to_account}**** \nFROM THIS ACCOUNT: ****{from_account}****"
                print(message)
                
                return message
            except Exception as e:
                error_message = f"An error occurred while processing the transaction: {e}"
                print(error_message)
                return error_message, 500  # Internal Server Error
        else:
            return "Incomplete data provided", 400  # Bad Request

    return render_template('sendcash.html')

def send_cash_data_to_db(action, amount, from_account, to_account):
    
    connection = None
    cursor = None
    try:
        # Convert amount to a float
        amount = float(amount)
        
        # Get current timestamp with timezone
        timestamp = datetime.now().astimezone()
        
        # Connect to the database
        connection = connection_pool.getconn()
        cursor = connection.cursor()

        # Check if the `from_account` has enough balance
        cursor.execute("SELECT amount FROM transactions WHERE accountnumber = %s", (from_account,))
        from_account_balance = float(cursor.fetchone()[0])

        if from_account_balance < amount:
            raise ValueError("Insufficient balance in the sender's account")

        # Update the balance for `from_account`
        cursor.execute("UPDATE transactions SET amount = amount - %s WHERE accountnumber = %s", (amount, from_account))

        # Update the balance for `to_account`
        cursor.execute("UPDATE transactions SET amount = amount + %s WHERE accountnumber = %s", (amount, to_account))

        # Insert the transaction record for `from_account` with timestamp
        cursor.execute("INSERT INTO transactions (accountnumber, action, amount, timestamp) VALUES (%s, %s, %s, %s)", (from_account, action, -amount, timestamp))

        # Insert the transaction record for `to_account` with timestamp
        cursor.execute("INSERT INTO transactions (accountnumber, action, amount, timestamp) VALUES (%s, %s, %s, %s)", (to_account, action, amount, timestamp))

        # Commit the transaction
        connection.commit()
    except (Exception, psycopg2.Error) as error:
        if connection:
            connection.rollback()  # Roll back the transaction in case of error
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection_pool.putconn(connection)

############################################_CHECK_BALANCE_#########################################
@app.route('/checkbalance', methods=['POST', 'GET'])
def checkbalance():
    print("checkbalance route accessed")
    
    if request.method == 'POST':
        print("POST request received")
        
        try:
            # Get the account number from the session
            account_number = session.get('user_name')
            print(f"Account Number from session: {account_number}")

            if account_number is None:
                error_message = "No account number in session."
                print(error_message)
                return render_template('error.html', error_message=error_message), 400

            # Connect to the database
            connection = connection_pool.getconn()
            cursor = connection.cursor()
            print("Database connection established")

            # Query to get the total balance for the account number
            query = sql.SQL("SELECT SUM(amount) FROM transactions WHERE accountnumber = %s")
            cursor.execute(query, (account_number,))
            print("Query executed")

            # Fetch the balance
            balance = cursor.fetchone()[0]
            if balance is None:
                balance = 0  # If no transactions, set balance to 0

            print(f"Balance fetched: {balance}")

            # Close the cursor and return the connection to the pool
            cursor.close()
            connection_pool.putconn(connection)
            print("Database connection closed")

            # Display the balance information
            displayed_data = f"Total Balance: {balance}\nAccount Number: {account_number}"
            print(f"Displayed Data: {displayed_data}")

            return render_template('checkbalance.html', displayed_data=displayed_data)

        except Exception as e:
            # Handle exceptions and rollback if needed
            error_message = f"Error occurred while checking balance: {e}"
            print(error_message)
            return render_template('error.html', error_message=error_message), 500

    # For GET requests, render the page with an empty displayed_data
    print("GET request received")
    return render_template('checkbalance.html', displayed_data='')

####################################_STATEMENT_##########################################
@app.route('/statement', methods=['POST', 'GET'])
def print_statement():
    account_number = session.get('user_name')
    print("Attempting to connect")
    
    if request.method == 'POST':
        try:
            # Connect to the database
            connection = connection_pool.getconn()  # Get connection from the pool
            cursor = connection.cursor()
            print("Connected")
            
            # Fetch names for the account number
            fetch_name = sql.SQL("SELECT name,surname,address FROM users WHERE accountnumber = %s")
            cursor.execute(fetch_name, (account_number))
            names = cursor.fetchall()
            # Fetch statement data for the specified account number
            fetch_query = sql.SQL("SELECT * FROM transactions WHERE accountnumber = %s")
            cursor.execute(fetch_query, (account_number,))
            
            # Fetch all rows from the executed query
            records = cursor.fetchall()
            print(records)
            
            # Close cursor and connection
            cursor.close()
            connection_pool.putconn(connection)
            print("Connection closed")
            
            # Pass the statement data to the template for rendering
            return render_template('statement.html', statement_data=records)

        except Exception as e:
            error_message = f"An error occurred while fetching statement data: {e}"
            return render_template('error.html', error_message=error_message), 500
    
    return render_template('statement.html', statement_data=[] )

if __name__ == "__main__":
    app.run(debug=True, port=1014)
