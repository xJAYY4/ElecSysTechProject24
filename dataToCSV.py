import serial
import csv
import time

# Serial Port Config
serial_port = 'COM5'
baud_rate = 9600

try:
    # Initialize serial connection
    arduino = serial.Serial(serial_port, baud_rate)
    print("Connected to Arduino successfully!")

    # Catch for Failed Connection
except serial.SerialException as e:
    print(f"Error: Could not open port {serial_port}. {e}")
    exit()

csv_filename = 'sensor_data.csv'

# Open the file in append mode to keep adding data
with open(csv_filename, mode='a', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)

    # Write header if file is empty
    csv_file.seek(0, 2)  # Go to end of file
    if csv_file.tell() == 0:  # Check if the file is empty
        csv_writer.writerow(["Light Level (%)", "Gas Concentration (MQ135)", "Humidity (%)", "Temperature (°C)"])

    # Continuously read data from serial and write to CSV
    try:
        while True:
            # Read line from Arduino
            data = arduino.readline().decode('utf-8').strip()
            if "Error" in data:
                print("Sensor error, skipping entry.")
                continue

            # Split the data into values
            values = data.split(",")
            if len(values) == 4:  # Ensure all fields are present
                csv_writer.writerow(values)
                csv_file.flush()  # Ensure data is written to disk
                print(f"Logged data: {values}")
            else:
                print("Incomplete data received")

            time.sleep(5)
    except KeyboardInterrupt:
        print("Data collection stopped.")
    finally:
        arduino.close()