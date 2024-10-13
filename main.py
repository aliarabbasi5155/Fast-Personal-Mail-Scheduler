import smtplib
import json
import time
import logging
from logging import StreamHandler
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate, formataddr
import os

# Configure logging to log both to file and console
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler (logs to file)
file_handler = logging.FileHandler('email_script.log')
file_handler.setLevel(logging.INFO)

# Console handler (logs to console)
console_handler = StreamHandler()
console_handler.setLevel(logging.INFO)

# Logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Function to read configurations from config.json
def read_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        return config_data
    except Exception as e:
        logging.error(f"Failed to read config file: {e}")
        return None

# Function to send email
def send_email(to_address, subject, message, file_path=None, config=None):
    msg = MIMEMultipart()
    msg['From'] = formataddr((config['your_name'], config['username']))  # Display name and email
    msg['To'] = to_address
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)  # Add the Date header

    # Attach the message body
    msg.attach(MIMEText(message, 'plain'))

    # If a file path is provided, attach the corresponding file
    if file_path:
        try:
            with open(file_path, 'rb') as f:
                file_name = os.path.basename(file_path)  # Extract file name from path
                part = MIMEApplication(f.read(), Name=file_name)
            part['Content-Disposition'] = f'attachment; filename="{file_name}"'
            msg.attach(part)
            logging.info(f"Attached file: {file_path}")
        except Exception as e:
            logging.error(f"Failed to attach file {file_path}: {e}")
            return False

    try:
        # Connect to the server
        server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        server.login(config['username'], config['password'])
        # Send the email
        server.send_message(msg)
        server.quit()

        logging.info(f"Email sent successfully to {to_address}")
        return True

    except Exception as e:
        logging.error(f"Failed to send email to {to_address}. Error: {e}")
        return False

# Function to read email details from a JSON file
def read_email_details_from_json(json_file):
    try:
        with open(json_file, 'r') as f:
            email_data = json.load(f)
        return email_data
    except Exception as e:
        logging.error(f"Failed to read JSON file: {e}")
        return None

# Function to write the updated email data back to JSON file after removing sent emails
def update_email_data_json(json_file, updated_data):
    try:
        with open(json_file, 'w') as f:
            json.dump(updated_data, f, indent=4)
        logging.info(f"Updated {json_file} successfully")
    except Exception as e:
        logging.error(f"Failed to update {json_file}: {e}")

# Function to append sent email details to sent.json with the sent time
def log_sent_email(email_entry, sent_file):
    # Add the sent time to the email entry
    email_entry['sent_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if sent.json exists, if not create an empty file
    if not os.path.exists(sent_file):
        with open(sent_file, 'w') as f:
            json.dump({"emails": []}, f, indent=4)
    
    try:
        with open(sent_file, 'r') as f:
            sent_data = json.load(f)

        sent_data['emails'].append(email_entry)

        with open(sent_file, 'w') as f:
            json.dump(sent_data, f, indent=4)

        logging.info(f"Logged email sent to {email_entry['to_address']} in {sent_file} with sent time {email_entry['sent_time']}")

    except Exception as e:
        logging.error(f"Failed to update {sent_file}: {e}")

# Main function that continuously runs the script
def run_script_continuously(config):
    while True:
        try:
            logging.info("Script started")
            # Read the email details from the JSON file
            email_data = read_email_details_from_json(config['json_file'])
            if email_data and "emails" in email_data:
                remaining_emails = []  # To store emails that are not yet sent

                for email_entry in email_data['emails']:
                    to_address = email_entry['to_address']
                    subject = email_entry['subject']
                    body = email_entry['body']
                    file_path = email_entry.get('file_path')
                    email_time_str = email_entry['time']

                    # Convert the email time from string to a datetime object
                    email_time = datetime.strptime(email_time_str, "%Y-%m-%d %H:%M:%S")
                    current_time = datetime.now()

                    # Check if the current time is equal to or later than the specified time
                    if current_time >= email_time:
                        logging.info(f"Sending email to {to_address} at {current_time}")
                        success = send_email(to_address, subject, body, file_path, config)
                        
                        if success:
                            # Log sent email to sent.json with sent time
                            log_sent_email(email_entry, config['sent_file'])
                        else:
                            # If email sending failed, retain in the list
                            remaining_emails.append(email_entry)
                    else:
                        # If the email time is in the future, retain in the list
                        remaining_emails.append(email_entry)

                # Update the email_data.json with only the remaining emails
                update_email_data_json(config['json_file'], {"emails": remaining_emails})

            # Sleep for a minute before checking again
            time.sleep(60)

        except Exception as e:
            logging.error(f"Script crashed due to error: {e}")
            # Wait a bit before restarting to avoid immediate crash loops
            time.sleep(5)  # Sleep for 5 seconds before retrying

if __name__ == "__main__":
    # Read the configurations from config.json
    config = read_config('config.json')
    if config:
        run_script_continuously(config)
    else:
        logging.error("Failed to start the script. Invalid or missing configuration.")
