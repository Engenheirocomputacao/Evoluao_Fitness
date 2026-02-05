/*
 * ESP32 Step Counter - Pedômetro Inteligente
 * 
 * Este código usa um acelerômetro MPU6050 para contar passos
 * e calcular distância percorrida.
 * 
 * Hardware necessário:
 * - ESP32
 * - MPU6050 (Acelerômetro/Giroscópio)
 * - Conexões I2C: SDA=GPIO21, SCL=GPIO22
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ========== CONFIGURAÇÕES - EDITE AQUI ==========
const char* ssid = "SEU_WIFI_SSID";           
const char* password = "SUA_SENHA_WIFI";       
const char* mqtt_server = "192.168.1.100";     
const int mqtt_port = 1883;                     
const char* mqtt_user = "";                     
const char* mqtt_password = "";                 

const char* device_id = "ESP32_STEPS_001";      
const char* device_name = "Pedômetro Smart";    
const int user_id = 1;                          

const int SEND_INTERVAL = 30000;  // Enviar a cada 30 segundos
const float STEP_LENGTH = 0.75;   // Comprimento médio do passo em metros
// ==================================================

Adafruit_MPU6050 mpu;
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastSend = 0;
int stepCount = 0;
float distanceMeters = 0;

// Parâmetros para detecção de passo
const float STEP_THRESHOLD = 1.2;  // m/s² acima da gravidade
const unsigned long STEP_COOLDOWN = 300;  // ms entre passos
unsigned long lastStepTime = 0;
float lastAccel = 0;
bool peakDetected = false;

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Pedômetro - Iniciando...");
  
  // Inicializar MPU6050
  if (!mpu.begin()) {
    Serial.println("ERRO: MPU6050 não encontrado!");
    while (1) {
      delay(10);
    }
  }
  
  Serial.println("MPU6050 inicializado!");
  
  // Configurar MPU6050
  mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
  mpu.setGyroRange(MPU6050_RANGE_250_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  Serial.println("Pedômetro pronto. Comece a caminhar!");
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
  String command = "";
  for (unsigned int i = 0; i < length; i++) {
    command += (char)payload[i];
  }
  
  if (command == "reset_steps") {
    stepCount = 0;
    distanceMeters = 0;
    Serial.println("Passos resetados!");
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

void detectStep() {
  // Ler dados do sensor
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  
  // Calcular magnitude da aceleração vertical (eixo dominante para passos)
  float accelMagnitude = abs(sqrt(
    pow(a.acceleration.x, 2) + 
    pow(a.acceleration.y, 2) + 
    pow(a.acceleration.z, 2)
  ) - 9.8);  // Remover componente gravitacional
  
  // Algoritmo de detecção de pico simples
  if (accelMagnitude > STEP_THRESHOLD && !peakDetected) {
    // Verificar se passou tempo suficiente desde último passo
    if (millis() - lastStepTime > STEP_COOLDOWN) {
      stepCount++;
      distanceMeters = stepCount * STEP_LENGTH;
      lastStepTime = millis();
      peakDetected = true;
      
      Serial.printf("👣 Passo %d detectado! Distância: %.1fm\n", stepCount, distanceMeters);
    }
  }
  
  // Reset do detector de pico quando aceleração volta ao normal
  if (accelMagnitude < STEP_THRESHOLD * 0.5) {
    peakDetected = false;
  }
  
  lastAccel = accelMagnitude;
}

void sendStepUpdate() {
  StaticJsonDocument<300> doc;
  
  doc["device_id"] = device_id;
  doc["device_name"] = device_name;
  doc["user_id"] = user_id;
  doc["timestamp"] = getTimestamp();
  doc["value"] = stepCount;
  doc["unit"] = "steps";
  
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["distance_meters"] = distanceMeters;
  metadata["distance_km"] = distanceMeters / 1000.0;
  metadata["step_length"] = STEP_LENGTH;
  metadata["signal_quality"] = "excellent";
  metadata["battery"] = 100;  // Implementar leitura real
  metadata["sensor_type"] = "MPU6050";
  
  // Calcular calorias aproximadas (baseado em passos)
  float calories = stepCount * 0.04;  // ~0.04 cal por passo
  metadata["calories"] = calories;
  
  char buffer[300];
  serializeJson(doc, buffer);
  
  String topic = "fitness/device/" + String(device_id) + "/steps";
  client.publish(topic.c_str(), buffer);
  
  Serial.printf("Status: %d passos | %.1fm | %.1f cal\n", 
                stepCount, distanceMeters, calories);
}

String getTimestamp() {
  // Simplificado - ideal usar NTP
  return "2026-01-25T12:00:00Z";
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Detectar passos continuamente
  detectStep();
  
  // Enviar atualização periódica
  if (millis() - lastSend > SEND_INTERVAL) {
    lastSend = millis();
    sendStepUpdate();
  }
  
  delay(50);  // Sampling rate ~20Hz
}
