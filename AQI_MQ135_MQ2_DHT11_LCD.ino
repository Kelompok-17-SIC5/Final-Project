#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>

// Pin configuration for sensors
#define DHTPIN 13
#define DHTTYPE DHT11
#define MQ135PIN 34 // ADC pin
#define MQ2PIN 35   // ADC pin

DHT dht(DHTPIN, DHTTYPE);

// Network credentials
const char* ssid = "Hiro";
const char* password = "12345678900";
const char* mqtt_server = "test.mosquitto.org";
const int port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

const char* topic_temperature = "/sensor/data/temperature";
const char* topic_humidity = "/sensor/data/humidity";
const char* topic_air_quality = "/sensor/data/air_quality";
const char* topic_smoke_value = "/sensor/data/smoke_value";
const char* topic_command = "/sic/command/mqtt";

// TFT configuration
#define TFT_DC   5
#define TFT_CS   15
#define TFT_MOSI 4
#define TFT_CLK  2
#define TFT_RST  0

Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_MOSI, TFT_CLK, TFT_RST);

// Smoke levels thresholds for MQ-2
#define NO_SMOKE_THRESHOLD 300
#define LOW_SMOKE_THRESHOLD 500

void setup_wifi() {
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  if ((char)payload[0] == '1') {
    digitalWrite(2, LOW);
  } else {
    digitalWrite(2, HIGH);
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println("Connected");
      client.publish("/sic/mqtt", "Hello!");
      client.subscribe(topic_command);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  pinMode(2, OUTPUT);
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, port);
  client.setCallback(callback);
  dht.begin();

  tft.initR(INITR_BLACKTAB);  // Initialize ST7735S chip
  tft.setRotation(1);         // Rotate display if needed
  tft.fillScreen(ST77XX_BLACK); // Clear display
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 2000) {
    lastMsg = now;

    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    int mq135_value = analogRead(MQ135PIN);
    float air_quality = (mq135_value > 0) ? calculateAQI(mq135_value) : NAN;
    int mq2_value = analogRead(MQ2PIN);

    publishData(topic_temperature, temperature, 2);
    publishData(topic_humidity, humidity, 1);
    publishData(topic_air_quality, air_quality, 2);
    publishData(topic_smoke_value, mq2_value, 2);

    displayData(temperature, humidity, air_quality, mq2_value);

    Serial.print("Temperature: ");
    Serial.println(temperature);
    Serial.print("Humidity: ");
    Serial.println(humidity);
    Serial.print("Air Quality (AQI): ");
    if (isnan(air_quality)) {
      Serial.println("nan");
    } else {
      Serial.println(air_quality);
    }
    Serial.print("MQ-2 Value: ");
    Serial.println(mq2_value);
  }
}

void publishData(const char* topic, float value, int precision) {
  String valueString = isnan(value) ? "nan" : String(value, precision);
  client.publish(topic, valueString.c_str());
}

float calculateAQI(int mq135_value) {
  float concentration = (mq135_value / 4095.0) * 1000; 

  if (concentration <= 50) {
    return concentration * 50.0 / 50.0; 
  } else if (concentration <= 100) {
    return ((concentration - 50) * 50.0 / 50.0) + 50;
  } else if (concentration <= 150) {
    return ((concentration - 100) * 50.0 / 50.0) + 100;
  } else if (concentration <= 200) {
    return ((concentration - 150) * 50.0 / 50.0) + 150;
  } else if (concentration <= 300) {
    return ((concentration - 200) * 100.0 / 100.0) + 200;
  } else {
    return ((concentration - 300) * 100.0 / 100.0) + 300;
  }
}

void displayData(float temperature, float humidity, float air_quality, int mq2_value) {
  tft.fillScreen(ST77XX_BLACK);
  tft.setCursor(0, 0);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.print("Temp: ");
  tft.print(temperature);
  tft.println(" C");

  tft.print("Humidity: ");
  tft.print(humidity);
  tft.println(" %");

  tft.print("Air Quality (AQI): ");
  if (isnan(air_quality)) {
    tft.print("nan");
  } else {
    tft.print(air_quality);
  }

  tft.println();

  tft.print("Smoke Level: ");
  if (mq2_value < NO_SMOKE_THRESHOLD) {
    tft.setTextColor(ST77XX_GREEN);
    tft.print("No Smoke");
  } else if (mq2_value < LOW_SMOKE_THRESHOLD) {
    tft.setTextColor(ST77XX_YELLOW);
    tft.print("Low Smoke");
  } else {
    tft.setTextColor(ST77XX_RED);
    tft.print("High Smoke");
  }
}
