import os                                               # This library will provide functions to interact with the operating system, such as checking for file existence.
import pickle                                           # This library will be used for saving and loading Python objects, like storing credentials
from sqlite3 import DataError
import time                                             # Provides time-related functions like sleeping for a specific duration
from urllib.request import Request                      # Handles HTTP requests and indirectly used for refreshing tokens.
import serial                                           # This library provides functions to communicate with serial devices
import csv                                              # Provides functionality for reading and writing CSV

from google.auth.transport.requests import Request      # Correct import for Request
from google_auth_oauthlib.flow import InstalledAppFlow  # Handles OAuth 2.0 authorization for accessing Google APIs
from googleapiclient.discovery import build             # This will interact with Google APIs (Drive, Sheets) by building the service object
from googleapiclient.http import MediaFileUpload        # Used for uploading files to Google Drive via the API


# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive.file'] # Scope to allow file creation and access in Google Drive
creds = None                                            # Variable to store the credentials


# Check if we have stored credentials (token.pickle), this will avoid re-authenticating every time
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)            # Load stored credentials from the pickle file


# If no credentials, let the user log in (you will be prompted to log in the first time the program is run)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())           # Refresh the credentials if expired
    else:
        # Create an OAuth2 flow to authenticate and get credentials
        flow = InstalledAppFlow.from_client_secrets_file(
            '/credentials.json',                                    # Path to the credentials file
            scopes=['https://www.googleapis.com/auth/drive.file']   # Required permissions for Google Drive
        )
        creds = flow.run_local_server(port=0)  # Open a local server for authentication


    # Save the credentials for future use (this will avoid re-authenticating)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)       # Save credentials as a pickle file


# Build the Google Drive API client using the obtained credentials
service = build('drive', 'v3', credentials=creds)



# Define serial port
serial_port = 'COM5'  # Port where Arduino is connected (This will be changed for Raspi)
baud_rate = 9600      # Communication baud rate

# Attempt to connect via serial port
try:
    arduino = serial.Serial(serial_port, baud_rate)
    print("Connected to Arduino successfully!")
except serial.SerialException as e:
    print(f"Error: Could not open port {serial_port}. {e}") # This handles connection errors
    exit()


csv_filename = 'sensor_data.csv'    # Filename for the CSV file where sensor data will be logged


# Check if file exists and if it is empty
file_exists = os.path.exists(csv_filename)

# Open the file in append mode to keep adding data
with open(csv_filename, mode='a', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)      # Initialize the CSV writer

    # Write header if the file is empty
    if not file_exists or os.path.getsize(csv_filename) == 0:
        csv_writer.writerow(["Timestamp", "Light Level (%)", "Gas Concentration (MQ135)", "Humidity (%)", "Temperature (°C)"])

    # Define a maximum time limit for data collection  
    # The 20 seconds is for uploading to google drive testing purposes
    start_time = time.time()
    max_duration = 20  

    try:
        while True:
            # Check if the maximum time duration has passed
            elapsed_time = time.time() - start_time
            if elapsed_time > max_duration:
                print("20 seconds reached, stopping data collection.")
                break  # Exit the loop after 20 seconds

            # Read line from Arduino
            data = arduino.readline().decode('utf-8').strip()
            print(f"Raw data received: '{data}'")

            # Skip the data if there is an error message and try the next one
            if "Error" in data:
                print("Sensor error, skipping entry.")
                continue


            # Split the data into values
            values = data.split(",")
            if len(values) == 5:  # We expect 5 values: timestamp and 4 sensor readings
                csv_writer.writerow(values)
                csv_file.flush()
                print(f"Logged data: {values}")

            # Check time and exit if over 20 seconds
            elapsed_time = time.time() - start_time
            if elapsed_time >= max_duration:
                print("Max time reached. Stopping data collection.")
                break


    except KeyboardInterrupt:
        print("Data collection stopped.")   # If user interrupts, stop the data collection
    

# Upload the CSV file to Google Drive (before closing Arduino connection)
try:
    # This will search for an existing file by name in Google Drive (I dont want 5000 csv files in my google drive and this makes sense anyways)
    file_metadata = {'name': 'sensor_data.csv'}
    query = f"name = 'sensor_data.csv'"  # Search for the file by name
    results = service.files().list(q=query, fields="files(id, name)").execute()

    files = results.get('files', [])
    if not files:
        # If the file doesn't exist, upload a new file  
        media = MediaFileUpload(csv_filename, mimetype='text/csv')
        request = service.files().create(media_body=media, body=file_metadata, fields='id')
        file = request.execute()
        print(f"File uploaded successfully with ID: {file['id']}")
    else:
        # If the file exists, update the existing file
        file_id = files[0]['id']  # Use the ID of the existing file
        media = MediaFileUpload(csv_filename, mimetype='text/csv', resumable=True)
        request = service.files().update(fileId=file_id, media_body=media).execute()
        print(f"File updated successfully with ID: {file_id}")


except DataError as error:
    print(f"An error occurred: {error}")    # For debugging even though this should never happen 


finally:
    arduino.close()  # Ensure Arduino connection is closed after the upload
