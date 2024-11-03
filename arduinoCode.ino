#include <DHT.h> // Include DHT library

// Define sensor pins
const int photoResistorPin = A0; // Photoresistor connected to analog pin A0
const int mq135Pin = A5;         // MQ135 connected to analog pin A5
const int dhtPin = 4;            // DHT11 connected to digital pin 4

// Define LED pins
const int photoResistorLEDPin = 7; // LED for photoresistor
const int mq135LEDPin = 5;         // LED for MQ135
const int dhtLEDPin = 6;           // LED for DHT11

// Define LED brightness level (0-255)
const int ledBrightness = 200;     // Adjust this value for desired brightness

// Define DHT sensor type
#define DHTTYPE DHT11
DHT dht(dhtPin, DHTTYPE); // Create DHT object

void setup() {
    Serial.begin(9600);                   // Initialize serial communication
    dht.begin();                          // Initialize DHT sensor
    pinMode(photoResistorLEDPin, OUTPUT); // Set photoresistor LED as output
    pinMode(mq135LEDPin, OUTPUT);         // Set MQ135 LED as output
    pinMode(dhtLEDPin, OUTPUT);           // Set DHT LED as output
    delay(1000);                          // Wait for sensors to stabilize
}

void loop() {
    // Read data from sensors
    int lightValue = analogRead(photoResistorPin);
    float lightLevel = lightValue / 1023.0 * 100;
    int mq135Value = analogRead(mq135Pin);
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();

    // Print data in CSV format
    if (!isnan(humidity) && !isnan(temperature)) {
        Serial.print(lightLevel);
        Serial.print(",");
        Serial.print(mq135Value);
        Serial.print(",");
        Serial.print(humidity);
        Serial.print(",");
        Serial.println(temperature);
    } else {
        Serial.println("Error reading DHT11 sensor!");
    }

    delay(20000); // Delay between readings
}
