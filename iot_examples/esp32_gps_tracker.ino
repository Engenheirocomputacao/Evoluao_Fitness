/*
 * ESP32 GPS Tracker - Rastreador GPS para Corridas
 * 
 * Este código conecta o ESP32 ao WiFi e MQTT broker, lê dados de um módulo GPS
 * (NEO-6M ou NEO-7M) e envia coordenadas para o sistema Django.
 * 
 * Hardware necessário:
 * - ESP32
 * - Módulo GPS NEO-6M/NEO-7M
 * - Conexões: GPS TX -> ESP32 RX (GPIO16), GPS RX -> ESP32 TX (GPIO17)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>

// ========== CONFIGURAÇÕES - EDITE AQUI ==========
const char* ssid = "SEU_WIFI_SSID";           
const char* password = "SUA_SENHA_WIFI";       
const char* mqtt_server = "192.168.1.100";     
const int mqtt_port = 1883;                     
const char* mqtt_user = "";                     
const char* mqtt_password = "";                 

const char* device_id = "ESP32_GPS_001";        
const char* device_name = "GPS Watch Pro";      
const int user_id = 1;                          

const int SEND_INTERVAL = 5000;  // Enviar a cada 5 segundos durante movimento
// ==================================================

// GPS Serial (usar Serial2 do ESP32)
HardwareSerial gpsSerial(2);
TinyGPSPlus gps;

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastSend = 0;
double lastLat = 0, lastLng = 0;
float totalDistance = 0;  // Distância total em metros

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 GPS Tracker - Iniciando...");
  
  // Inicializar GPS Serial (RX=16, TX=17)
  gpsSerial.begin(9600, SERIAL_8N1, 16, 17);
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  Serial.println("GPS Tracker pronto. Aguardando sinal GPS...");
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
  // Callback para comandos (pausar tracking, resetar distância, etc)
  String command = "";
  for (unsigned int i = 0; i < length; i++) {
    command += (char)payload[i];
  }
  
  if (command == "reset_distance") {
    totalDistance = 0;
    Serial.println("Distância resetada!");
  }
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

float calculateDistance(double lat1, double lon1, double lat2, double lon2) {
  // Fórmula de Haversine para calcular distância entre coordenadas
  const float R = 6371000; // Raio da Terra em metros
  float dLat = (lat2 - lat1) * DEG_TO_RAD;
  float dLon = (lon2 - lon1) * DEG_TO_RAD;
  
  float a = sin(dLat/2) * sin(dLat/2) +
            cos(lat1 * DEG_TO_RAD) * cos(lat2 * DEG_TO_RAD) *
            sin(dLon/2) * sin(dLon/2);
  
  float c = 2 * atan2(sqrt(a), sqrt(1-a));
  return R * c;
}

void sendGPSData() {
  if (!gps.location.isValid()) {
    Serial.println("Aguardando sinal GPS válido...");
    return;
  }
  
  double currentLat = gps.location.lat();
  double currentLng = gps.location.lng();
  float speed = gps.speed.kmph();
  float altitude = gps.altitude.meters();
  int satellites = gps.satellites.value();
  
  // Calcular distância desde último ponto
  if (lastLat != 0 && lastLng != 0) {
    float distance = calculateDistance(lastLat, lastLng, currentLat, currentLng);
    if (distance > 1 && distance < 100) { // Filtrar ruído GPS
      totalDistance += distance;
    }
  }
  
  lastLat = currentLat;
  lastLng = currentLng;
  
  // Criar payload JSON
  StaticJsonDocument<400> doc;
  
  doc["device_id"] = device_id;
  doc["device_name"] = device_name;
  doc["user_id"] = user_id;
  doc["timestamp"] = getTimestamp();
  doc["value"] = totalDistance;  // Distância total em metros
  doc["unit"] = "meters";
  
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["latitude"] = currentLat;
  metadata["longitude"] = currentLng;
  metadata["speed"] = speed;
  metadata["altitude"] = altitude;
  metadata["satellites"] = satellites;
  metadata["signal_quality"] = satellites >= 6 ? "excellent" : (satellites >= 4 ? "good" : "fair");
  metadata["battery"] = 100;  // Implementar leitura real de bateria
  
  char buffer[400];
  serializeJson(doc, buffer);
  
  String topic = "fitness/device/" + String(device_id) + "/gps";
  client.publish(topic.c_str(), buffer);
  
  // Log no Serial
  Serial.printf("GPS: Lat=%.6f, Lng=%.6f, Speed=%.1f km/h, Dist=%.0fm, Sats=%d\n",
                currentLat, currentLng, speed, totalDistance, satellites);
}

String getTimestamp() {
  // Simplificado - ideal usar NTP para timestamp real
  if (gps.date.isValid() && gps.time.isValid()) {
    char timestamp[30];
    sprintf(timestamp, "%04d-%02d-%02dT%02d:%02d:%02dZ",
            gps.date.year(), gps.date.month(), gps.date.day(),
            gps.time.hour(), gps.time.minute(), gps.time.second());
    return String(timestamp);
  }
  return "2026-01-25T12:00:00Z";
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Ler dados do GPS
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
  
  // Enviar dados periodicamente
  if (millis() - lastSend > SEND_INTERVAL) {
    lastSend = millis();
    sendGPSData();
  }
  
  // Display de diagnóstico
  if (millis() % 10000 < 100) {
    Serial.printf("Status: Sats=%d, Lat=%.6f, Lng=%.6f, Distance=%.0fm\n",
                  gps.satellites.value(), 
                  gps.location.lat(), 
                  gps.location.lng(),
                  totalDistance);
  }
}
