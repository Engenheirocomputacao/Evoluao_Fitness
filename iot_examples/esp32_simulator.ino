/*
 * ESP32 - Simulador IoT
 * Código para demonstração sem sensores
 */
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "SEU_WIFI_SSID";
const char* password = "SUA_SENHA_WIFI";
const char* mqtt_server = "192.168.1.100";
const int mqtt_port = 1883;

const char* device_id = "ESP32_SIM_001";
const char* device_name = "Simulador IoT";

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastSend = 0;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  client.setServer(mqtt_server, mqtt_port);
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect(device_id)) {
      client.subscribe((String("fitness/device/") + device_id + "/command").c_str());
    } else {
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
  
  if (millis() - lastSend > 5000) {
    lastSend = millis();
    
    StaticJsonDocument<200> doc;
    doc["device_id"] = device_id;
    doc["value"] = random(60, 160);
    doc["unit"] = "bpm";
    doc["timestamp"] = "2026-01-23T12:00:00Z";
    
    char buffer[200];
    serializeJson(doc, buffer);
    client.publish((String("fitness/device/") + device_id + "/heartrate").c_str(), buffer);
  }
}
