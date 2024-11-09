import serial       # Import the pySerial library for serial communication
import csv          # Import the CSV library for writing data to CSV files
import os           # Import the os library for checking file existence and file properties


# Serial Port Configuration
serial_port = 'COM5'     # Define the COM port that the Arduino is connected to (change this for pi)
baud_rate = 9600         # Define the baud rate for serial communication (This will match Arduino)


# Initialize serial connection to Arduino
try:
    arduino = serial.Serial(serial_port, baud_rate) # Open the serial connection
    print("Connected to Arduino successfully!")     # Confirm successful connection

except serial.SerialException as e:
    # Handle errors if the serial connection cannot be established
    print(f"Error: Could not open port {serial_port}. {e}")
    exit()


# CSV file where the sensor data will be saved
csv_filename = 'sensor_data.csv'


# Check if file exists
file_exists = os.path.exists(csv_filename)


# Open the CSV file in append mode to continuously add new data without overwriting
with open(csv_filename, mode='a', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)

    # Write header if the file is empty (i.e., new file or no data)
    if not file_exists or os.path.getsize(csv_filename) == 0:  # Check if file is empty
        csv_writer.writerow(["Timestamp", "Light Level (%)", "Gas Concentration (MQ135)", "Humidity (%)", "Temperature (°C)"])

    # Continuously read data from serial and write to CSV
    try:
        while True:
            # Read line from Arduino
            data = arduino.readline().decode('utf-8').strip()
            print(f"Raw data received: '{data}'")  # Debugging line to show raw data

            if "Error" in data:
                print("Sensor error, skipping entry.")
                continue

            # Split the data into values
            values = data.split(",")
            if len(values) == 5:                # Expect 5 values
                # Write the row to CSV
                csv_writer.writerow(values)
                csv_file.flush()                # Ensure data is written to disk
                print(f"Logged data: {values}") # Print the logged data to the console for monitoring
            else:
                print("Incomplete or malformed data received, skipping entry.")

    
    except KeyboardInterrupt:
        # Handle user interrupt (Ctrl+C) to stop the data collection loop
        print("Data collection stopped.")

    
    finally:
        # Ensure the serial connection is properly closed
        arduino.close()
