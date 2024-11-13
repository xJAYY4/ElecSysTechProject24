import pandas as pd
from dash import Dash, dcc, html
from dash.dependencies import Output, Input
import plotly.express as px
import pickle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
creds = None

# Check if credentials are stored in token.pickle
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

# If there are no valid credentials, authenticate and save them
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES
        )
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

# Initialize the Google Drive API client
drive_service = build('drive', 'v3', credentials=creds)

# Define the function to download the CSV from Google Drive
def download_csv(file_id, filename='sensor_data.csv'):
    request = drive_service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    file.seek(0)
    with open(filename, 'wb') as f:
        f.write(file.read())
    return filename

# CSV file ID and interval for updates
file_id = '1y6PWTviufN4LdqYNTW_BFDaa6OnVc7_1'
csv_filename = download_csv(file_id)

# Load data into DataFrame
df = pd.read_csv(csv_filename, encoding='utf-8')
df.columns = df.columns.str.replace('Temperature (�C)', 'Temperature (°C)', regex=False)

# Initialize Dash app
app = Dash(__name__)

# App layout with separate graphs for each measurement over time
app.layout = html.Div([
    html.H1("Sensor Data Dashboard"),
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0),  # Update every 60 seconds

    # Graph 1: Light Level Over Time
    dcc.Graph(id='light-level-over-time'),
    
    # Graph 2: Temperature Over Time
    dcc.Graph(id='temperature-over-time'),
    
    # Graph 3: Humidity Over Time
    dcc.Graph(id='humidity-over-time'),
    
    # Graph 4: Gas Concentration Over Time
    dcc.Graph(id='gas-concentration-over-time')
])

# Callback function to update the data and graphs
@app.callback(
    [Output('light-level-over-time', 'figure'),
     Output('temperature-over-time', 'figure'),
     Output('humidity-over-time', 'figure'),
     Output('gas-concentration-over-time', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    # Re-download the CSV file to get the latest data
    download_csv(file_id, csv_filename)
    df = pd.read_csv(csv_filename, encoding='utf-8')
    df.columns = df.columns.str.replace('Temperature (�C)', 'Temperature (°C)', regex=False)

    # Update each graph with the new data
    light_fig = px.line(df, x='Timestamp', y='Light Level (%)', title="Light Level Over Time")
    temp_fig = px.line(df, x='Timestamp', y='Temperature (°C)', title="Temperature Over Time")
    humidity_fig = px.line(df, x='Timestamp', y='Humidity (%)', title="Humidity Over Time")
    gas_fig = px.line(df, x='Timestamp', y='Gas Concentration (MQ135)', title="Gas Concentration Over Time")

    return light_fig, temp_fig, humidity_fig, gas_fig

# Run the dashboard
if __name__ == '__main__':
    app.run_server(debug=True, host="127.0.0.1")
