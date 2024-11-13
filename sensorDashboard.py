# Import required libraries
import pandas as pd                                     # For handling data and CSV files
from dash import Dash, dcc, html                        # For creating the Dash app and its components
import plotly.express as px                             # For creating plots and graphs
import pickle                                           # For saving and loading the credentials
import os                                               # For checking file existence and path manipulations
from google_auth_oauthlib.flow import InstalledAppFlow  # For Google OAuth authentication
from google.auth.transport.requests import Request      # For handling requests during OAuth authentication
from googleapiclient.discovery import build             # For building Google Drive API client
from googleapiclient.http import MediaIoBaseDownload    # For downloading files from Google Drive
import io                                               # For handling byte data streams (for downloaded files)

# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']  # Scope for accessing Google Drive files
creds = None                                             # Initializing credentials to None

# Check if credentials are stored in token.pickle
if os.path.exists('token.pickle'):  # If the credentials file exists, load the token
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

# If there are no valid credentials, authenticate and save them
if not creds or not creds.valid:  
    if creds and creds.expired and creds.refresh_token:  
        creds.refresh(Request())  
    else: 
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',  # Path to the Google API client
            scopes=SCOPES        # Specify the required scopes for Google Drive API access
        )
        creds = flow.run_local_server(port=0)  # Run a local server for OAuth authentication and get credentials
    # Save the credentials for future runs to avoid repeated login
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

# Initialize the Google Drive API client using the obtained credentials
drive_service = build('drive', 'v3', credentials=creds)

# Define the function to download the CSV from Google Drive
def download_csv(file_id, filename='sensor_data.csv'):
    # Create a request to get the media (file content) from Google Drive using the file ID
    request = drive_service.files().get_media(fileId=file_id)
    file = io.BytesIO()  # Create an in-memory byte stream to store the file content
    downloader = MediaIoBaseDownload(file, request)  # Prepare the file download
    done = False
    while not done:  # Continue downloading in chunks until the entire file is downloaded
        status, done = downloader.next_chunk()
    file.seek(0)  # Rewind the file to the beginning
    with open(filename, 'wb') as f:  # Write the content to a file on disk
        f.write(file.read())
    return filename  # Return the downloaded filename

# Define the CSV file ID
file_id = '1y6PWTviufN4LdqYNTW_BFDaa6OnVc7_1'  

# Download the CSV file using the above function
csv_filename = download_csv(file_id)

# Load the data from the downloaded CSV file into a pandas DataFrame
df = pd.read_csv(csv_filename, encoding='utf-8')  # Load CSV file and handle encoding

# Fix the column name with the degree symbol for Temperature
df.columns = df.columns.str.replace('Temperature (�C)', 'Temperature (°C)', regex=False)

print(df.columns)  # This will display the correct column names in the console

# Initialize Dash app for the dashboard
app = Dash(__name__)

# Define the layout of the Dash app with separate graphs for each measurement over time
app.layout = html.Div([
    html.H1("Sensor Data Dashboard"),  # Title of the dashboard
    
    # Graph 1: Light Level Over Time
    dcc.Graph(id='light-level-over-time',
              figure=px.line(df, x='Timestamp', y='Light Level (%)',  # Line plot for Light Level
                             title="Light Level Over Time")),
    
    # Graph 2: Temperature Over Time
    dcc.Graph(id='temperature-over-time',
              figure=px.line(df, x='Timestamp', y='Temperature (°C)',  # Line plot for Temperature
                             title="Temperature Over Time")),
    
    # Graph 3: Humidity Over Time
    dcc.Graph(id='humidity-over-time',
              figure=px.line(df, x='Timestamp', y='Humidity (%)',  # Line plot for Humidity
                             title="Humidity Over Time")),
    
    # Graph 4: Gas Concentration Over Time
    dcc.Graph(id='gas-concentration-over-time',
              figure=px.line(df, x='Timestamp', y='Gas Concentration (MQ135)',  # Line plot for Gas Concentration
                             title="Gas Concentration Over Time"))
])

# Run the dashboard
if __name__ == '__main__':
    app.run_server(debug=True)  # Start the Dash app with debugging enabled
