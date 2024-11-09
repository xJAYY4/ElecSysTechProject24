#include <DHT.h>                    // Include DHT library for DHT11 Module
#include <Wire.h>                   // Include Wire library for I2C communication
#include <RTClib.h>                 // Include RTClib library for DS1307 RTC module

// Define sensor pins
const int photoResistorPin = A0;    // Photoresistor connected to analog pin A0
const int mq135Pin = A2;            // MQ135 connected to analog pin A2
const int dhtPin = 4;               // DHT11 connected to digital pin 4

// Define LED pins
const int photoResistorLEDPin = 7;  // LED for photoresistor
const int mq135LEDPin = 5;          // LED for MQ135
const int dhtLEDPin = 6;            // LED for DHT11


// Define LED brightness level (0-255)
const int ledBrightness = 200;      // This value adjusts the LED's brightness


// Define DHT sensor type
#define DHTTYPE DHT11
DHT dht(dhtPin, DHTTYPE);    // Create DHT object


// Create an RTC object
RTC_DS1307 rtc;   // This object will allow us to interact with the RTC


void setup() {
    Serial.begin(9600);                   // Initialize serial communication for data transmission
    dht.begin();                          // Initialize DHT sensor (for reading temperature and humidity)
    pinMode(photoResistorLEDPin, OUTPUT); // Set photoresistor LED as output
    pinMode(mq135LEDPin, OUTPUT);         // Set MQ135 LED as output
    pinMode(dhtLEDPin, OUTPUT);           // Set DHT LED as output
    delay(1000);                          // Delay for 1 second to allow the sensors to stabilize

    // Initialize the DS1307 RTC module if available
    if (!rtc.begin()) {
        rtc.begin();
    } else {
        // This will update the RTC time to the current time for each upload
        rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    }
}


void loop() {
    // Read data from sensors
    int lightValue = analogRead(photoResistorPin);
    float lightLevel = lightValue / 1023.0 * 100;  // Convert light value to percentage
    int mq135Value = analogRead(mq135Pin);
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();

    
    // If RTC is available, get the current date and time
    DateTime now;
    if (rtc.begin()) {
        now = rtc.now();   // Fetch the current time and date from the DS1307 RTC module
    }


    // Check if the DHT11 readings are valid (DHT sensor might occasionally fail to read)
    if (!isnan(humidity) && !isnan(temperature)) {
        // Send the timestamp from RTC along with the sensor data
        Serial.print(now.year(), DEC);
        Serial.print("/");
        Serial.print(now.month(), DEC);
        Serial.print("/");
        Serial.print(now.day(), DEC);
        Serial.print(" ");
        Serial.print(now.hour(), DEC);
        Serial.print(":");
        Serial.print(now.minute(), DEC);
        Serial.print(":");
        Serial.print(now.second(), DEC);
        Serial.print(",");
        
        // Print the sensor readings in CSV-like format
        Serial.print(lightLevel); Serial.print(",");
        Serial.print(mq135Value); Serial.print(",");
        Serial.print(humidity); Serial.print(",");
        Serial.println(temperature);
        
    } else {
        Serial.println("Error reading DHT11 sensor!");
    }

    delay(20000); // Delay between readings 20 seconds
}
