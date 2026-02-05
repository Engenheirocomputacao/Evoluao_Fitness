/*
 * ESP32 Fitness Monitor - Monitor de Frequência Cardíaca
 * 
 * Este código conecta o ESP32 ao WiFi e MQTT broker, lê dados de um sensor
 * de frequência cardíaca (MAX30102) e envia para o sistema Django.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

// ========== CONFIGURAÇÕES - EDITE AQUI ==========
const char* ssid = "SEU_WIFI_SSID";           
const char* password = "SUA_SENHA_WIFI";       
const char* mqtt_server = "192.168.1.100";     
const int mqtt_port = 1883;                     
const char* mqtt_user = "";                     
const char* mqtt_password = "";                 

const char* device_id = "ESP32_HEART_001";      
const char* device_name = "Monitor Cardíaco 1"; 
const int user_id = 1;                          

const int SEND_INTERVAL = 10000;                
// ==================================================

WiFiClient espClient;
PubSubClient client(espClient);
MAX30105 particleSensor;

const byte RATE_SIZE = 4; 
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;
float beatsPerMinute;
int beatAvg;

unsigned long lastSend = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Fitness Monitor - Iniciando...");
  
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("ERRO: Sensor MAX30102 não encontrado!");
    while (1);
  }
  
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeGreen(0);
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando ao WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi conectado!");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  // Callback placeholder
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Conectando ao MQTT...");
    boolean connected;
    if (strlen(mqtt_user) > 0) {
      connected = client.connect(device_id, mqtt_user, mqtt_password);
    } else {
      connected = client.connect(device_id);
    }
    
    if (connected) {
      Serial.println("conectado!");
      String commandTopic = "fitness/device/" + String(device_id) + "/command";
      client.subscribe(commandTopic.c_str());
    } else {
      Serial.print("falhou, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}

void sendHeartRate(int bpm, String quality) {
  StaticJsonDocument<300> doc;
  
  doc["device_id"] = device_id;
  doc["device_name"] = device_name;
  doc["user_id"] = user_id;
  doc["timestamp"] = getTimestamp();
  doc["value"] = bpm;
  doc["unit"] = "bpm";
  
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["signal_quality"] = quality;
  metadata["battery"] = 100;
  metadata["sensor_type"] = "MAX30102";
  
  char buffer[300];
  serializeJson(doc, buffer);
  
  String topic = "fitness/device/" + String(device_id) + "/heartrate";
  client.publish(topic.c_str(), buffer);
}

String getTimestamp() {
  // Simplificado, ideal usar NTP
  return "2026-01-23T12:00:00Z"; 
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  long irValue = particleSensor.getIR();
  
  if (checkForBeat(irValue) == true) {
    long delta = millis() - lastBeat;
    lastBeat = millis();
    beatsPerMinute = 60 / (delta / 1000.0);
    
    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      rates[rateSpot++] = (byte)beatsPerMinute;
      rateSpot %= RATE_SIZE;
      beatAvg = 0;
      for (byte x = 0; x < RATE_SIZE; x++) beatAvg += rates[x];
      beatAvg /= RATE_SIZE;
    }
  }
  
  if (millis() - lastSend > SEND_INTERVAL) {
    lastSend = millis();
    if (irValue > 50000) {
      String quality = (irValue > 100000) ? "excellent" : "good";
      sendHeartRate(beatAvg, quality);
    }
  }
}
