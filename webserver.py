from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Paths to JSON files
email_data_path = "email_data.json"
sent_data_path = "sent.json"
log_file_path = "app.log"
upload_folder = "resume/"

# Ensure upload folder exists
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

# Allowable file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

# Configure logging to handle both Flask and custom logs
logging.basicConfig(
    filename=log_file_path, 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Log to console as well
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to read JSON data
def read_json(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        return json.load(f).get("emails", [])

# Helper function to write data to JSON
def write_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump({"emails": data}, f, indent=4)

# Route to view logs
@app.route('/logs')
def view_logs():
    with open(log_file_path, 'r') as f:
        log_content = f.read()
    return f"<pre>{log_content}</pre>"

# Route to view sent emails
@app.route('/sent')
def view_sent_emails():
    sent_emails = read_json(sent_data_path)
    return render_template('view_sent.html', emails=sent_emails)

# Route to view email data records (email_data.json)
@app.route('/email_data')
def view_email_data():
    email_data = read_json(email_data_path)
    return render_template('view_email_data.html', emails=email_data)

# Route to add a new record to email_data.json
@app.route('/add_email', methods=['GET', 'POST'])
def add_email():
    if request.method == 'POST':
        # Retrieve form data
        to_address = request.form['to_address']
        subject = request.form['subject']
        body = request.form['body']
        send_time = request.form['send_time']
        file_path = ""

        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                file_dir = os.path.join(upload_folder, f"{timestamp}_{filename}")
                os.makedirs(file_dir, exist_ok=True)
                file_path = os.path.join(file_dir, filename)
                file.save(file_path)
                logging.info(f"File uploaded and saved to {file_path}")
        
        # Read the current email data
        email_data = read_json(email_data_path)

        # Create a new record
        new_email = {
            "to_address": to_address,
            "subject": subject,
            "body": body,
            "file_path": file_path,
            "time": send_time
        }

        # Append the new record and save to file
        email_data.append(new_email)
        write_json(email_data_path, email_data)

        # Log the addition of the new record
        logging.info(f"New email record added: {new_email}")
        return redirect(url_for('view_email_data'))
    
    return render_template('add_email.html')

# Route to edit a record in email_data.json
@app.route('/edit_email/<int:email_index>', methods=['GET', 'POST'])
def edit_email(email_index):
    email_data = read_json(email_data_path)
    
    if request.method == 'POST':
        # Retrieve form data
        to_address = request.form['to_address']
        subject = request.form['subject']
        body = request.form['body']
        send_time = request.form['send_time']
        file_path = email_data[email_index].get('file_path', "")

        # Handle file upload (optional)
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                file_dir = os.path.join(upload_folder, f"{timestamp}_{filename}")
                os.makedirs(file_dir, exist_ok=True)
                file_path = os.path.join(file_dir, filename)
                file.save(file_path)
                logging.info(f"File uploaded and saved to {file_path}")

        # Update the existing record
        email_data[email_index] = {
            "to_address": to_address,
            "subject": subject,
            "body": body,
            "file_path": file_path,
            "time": send_time
        }

        # Save updated data
        write_json(email_data_path, email_data)
        logging.info(f"Email record updated: {email_data[email_index]}")
        return redirect(url_for('view_email_data'))

    # Render the edit form with the current data
    return render_template('edit_email.html', email=email_data[email_index], email_index=email_index)

# Route to delete a record from email_data.json
@app.route('/delete_email/<int:email_index>')
def delete_email(email_index):
    email_data = read_json(email_data_path)
    
    if email_index < len(email_data):
        removed_email = email_data.pop(email_index)
        write_json(email_data_path, email_data)
        logging.info(f"Email record deleted: {removed_email}")

    return redirect(url_for('view_email_data'))

# Main entry point to run the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
