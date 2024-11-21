import os                                               # Provides functions for interacting with the operating system (file handling)
import pickle                                           # Used for storing the credentials
import serial                                           # Used for serial communication with the Arduino
import csv                                              # Provides reading and writing CSV files
from google.auth.transport.requests import Request      # For sending requests to authenticate with Google API
from google_auth_oauthlib.flow import InstalledAppFlow  # Handles OAuth2 flow for user authentication
from googleapiclient.discovery import build             # Provides a way to interact with Google APIs (Google Drive)
from googleapiclient.http import MediaFileUpload        # Used for uploading media files to Google Drive (CSV)



SCOPES = ['https://www.googleapis.com/auth/drive.file']     # Required scope for Google Drive file access
CSV_FILENAME = 'sensor_data.csv'                            # Name of the CSV file where sensor data will be stored
SERIAL_PORT = '/dev/ttyACM0'                                # Serial port to communicate with the Arduino
BAUD_RATE = 9600                                            # Baud rate for the serial communication with the Arduino
CREDENTIALS_FILE = 'credentials.json'                       # Path to Google credentials file


def authenticate_google_drive():
    """
    This handles the authentication process for the Google Drive API.
    It checks if valid credentials are stored in the 'token.pickle' file.
    If the credentials are expired or invalid, it attempts to refresh them.
    If refreshing fails, it prompts the user to authenticate via OAuth2 and saves the 
    new credentials for future use.
    
    Returns:
        service (Resource): an authenticated Google Drive service object for file operations.
    """
    creds = None  # Stores the credentials

    # Checks if the token file exists and load the stored credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # This will initiate authentication if credentials are invalid or expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())   # Refresh expired credentials
        else:
            # Prompts user to authenticate via OAuth2 if no valid credentials exist
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, scopes=SCOPES)
            creds = flow.run_local_server(port=0)  # Starts the local server for OAuth2 authentication
        
        # Saves the credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Return an authenticated Google Drive service
    return build('drive', 'v3', credentials=creds)


def connect_to_arduino():
    """
    Attempts to establish a serial connection to the Arduino board using the specified port and baud rate.
    If the connection is successful, it returns the serial object to interact with Arduino.
    If it fails, an error message is printed, and the program exits.
    
    Returns:
        arduino (Serial): A serial object for communication with the Arduino.
    
    Raises:
        SerialException: If unable to open the specified serial port.
    """
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE)         # Opens the serial connection to Arduino
        print("Connected to Arduino successfully!")
        return arduino
    except serial.SerialException as e:
        print(f"Error: Could not open port {SERIAL_PORT}. {e}") # Feedback for opening error
        raise


def initialize_csv():
    """
    Initializes the CSV file where sensor data will be stored. If the file doesn't exist or is empty,
    it writes the header row with the column names.
    
    Returns:
        csv_writer (csv.writer): A CSV writer object to write data to the file.
    """
    # Checks if the CSV file already exists
    file_exists = os.path.exists(CSV_FILENAME)
    
    # Opens the CSV file in append mode
    with open(CSV_FILENAME, mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        
        # Writes the header if the file doesn't exist or is empty
        if not file_exists or os.path.getsize(CSV_FILENAME) == 0:
            csv_writer.writerow(["Timestamp", "Light Level (%)", "Gas Concentration (MQ135)", "Humidity (%)", "Temperature (°C)"])
    
    return csv_writer


def upload_to_drive(service, csv_filename):
    """
    Uploads or updates the CSV file to Google Drive.
    It checks if the file already exists in the Google Drive. If it doesn't, it uploads the new file.
    If the file already exists, it updates the existing file with new data.
    
    Args:
        service (Resource): The authenticated Google Drive API service object.
        csv_filename (str): The name of the CSV file to upload or update.
    """
    # Metadata for the file being uploaded
    file_metadata = {'name': csv_filename}
    media = MediaFileUpload(csv_filename, mimetype='text/csv')  # Prepares the CSV file for upload

    # Checks if the file already exists on Google Drive
    query = f"name = '{csv_filename}'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        # Uploads file if it doesnt exist
        request = service.files().create(media_body=media, body=file_metadata, fields='id')
        file = request.execute()
        print(f"File uploaded successfully with ID: {file['id']}")
    else:
        # Updates the file if it exists
        file_id = files[0]['id']
        request = service.files().update(fileId=file_id, media_body=media).execute()
        print(f"File updated successfully with ID: {file_id}")


def main():
    """
    Main function to handle the process of data collection, logging, and uploading.
    This function:
        - Authenticates with the Google Drive
        - Connects to the Arduino
        - Initializes the CSV file for storing data
        - Continuously reads data from the Arduino and logs it to the CSV file
        - Uploads the CSV file to Google Drive after each data entry
    """
    # Authenticates and gets the Google Drive service
    service = authenticate_google_drive()
    
    # Connects to Arduino and get the serial object
    arduino = connect_to_arduino()
    
    # Initializes the CSV file and get the CSV writer
    csv_writer = initialize_csv()

    try:
        # Loop for continuously collecting and logging data
        while True:
            # Read a line of data from the Arduino and decode it
            data = arduino.readline().decode('utf-8').strip()
            print(f"Raw data received: '{data}'")

            # Skip bad data (primarily sensor errors)
            if "Error" in data:
                print("Sensor error, skipping entry.")
                continue

            # Split the received data into separate values (assumed to be comma-separated)
            values = data.split(",")
            
            # If the data contains the expected number of values (5), log it to the CSV
            if len(values) == 5:
                with open(CSV_FILENAME, mode='a', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow(values)  # Write the data to the CSV file
                    csv_file.flush()             # Ensure the data is written immediately
                    print(f"Logged data: {values}")
                
                try:
                    # Upload the updated CSV file to Google Drive
                    upload_to_drive(service, CSV_FILENAME)
                except Exception as error:
                    print(f"An error occurred during file upload: {error}")

    except KeyboardInterrupt:
        # Handle user interruption
        print("Data collection stopped by user.")

if __name__ == "__main__":
    main()
