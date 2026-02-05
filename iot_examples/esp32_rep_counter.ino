/*
 * ESP32 Rep Counter Pro - Contador de Repetições para Musculação
 * 
 * Este código usa um acelerômetro MPU6050 para detectar repetições
 * de exercícios e enviar dados para o sistema Django via MQTT.
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

const char* device_id = "ESP32_REPS_001";       
const char* device_name = "Rep Counter Pro";    
const int user_id = 1;                          

const int SEND_INTERVAL = 10000;  // Enviar a cada 10 segundos
// ==================================================

Adafruit_MPU6050 mpu;
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastSend = 0;
int repCount = 0;
int currentSet = 1;
bool isMoving = false;
bool lastMovingState = false;

// Parâmetros para detecção de repetição
const float ACCEL_THRESHOLD = 1.5;  // m/s² acima da gravidade
const unsigned long REP_COOLDOWN = 500;  // ms entre repetições
unsigned long lastRepTime = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Rep Counter Pro - Iniciando...");
  
  // Inicializar MPU6050
  if (!mpu.begin()) {
    Serial.println("ERRO: MPU6050 não encontrado!");
    while (1) {
      delay(10);
    }
  }
  
  Serial.println("MPU6050 inicializado!");
  
  // Configurar MPU6050
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  Serial.println("Rep Counter pronto. Comece seu exercício!");
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
  // Callback para comandos
  String command = "";
  for (unsigned int i = 0; i < length; i++) {
    command += (char)payload[i];
  }
  
  if (command == "reset_reps") {
    repCount = 0;
    Serial.println("Repetições resetadas!");
  } else if (command == "next_set") {
    currentSet++;
    repCount = 0;
    Serial.printf("Série %d iniciada!\n", currentSet);
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

void detectRep() {
  // Ler dados do sensor
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  
  // Calcular magnitude da aceleração (removendo gravidade)
  float accelMagnitude = sqrt(
    pow(a.acceleration.x, 2) + 
    pow(a.acceleration.y, 2) + 
    pow(a.acceleration.z - 9.8, 2)  // Subtrair gravidade do eixo Z
  );
  
  // Detectar movimento significativo
  if (accelMagnitude > ACCEL_THRESHOLD) {
    isMoving = true;
  } else {
    isMoving = false;
  }
  
  // Detectar repetição completa (início -> movimento -> parada)
  if (lastMovingState && !isMoving) {
    // Verificar cooldown para evitar dupla contagem
    if (millis() - lastRepTime > REP_COOLDOWN) {
      repCount++;
      lastRepTime = millis();
      
      Serial.printf("✓ Repetição %d detectada! (Série %d)\n", repCount, currentSet);
      
      // Enviar notificação imediata
      sendRepUpdate(true);
    }
  }
  
  lastMovingState = isMoving;
}

void sendRepUpdate(bool immediate = false) {
  StaticJsonDocument<300> doc;
  
  doc["device_id"] = device_id;
  doc["device_name"] = device_name;
  doc["user_id"] = user_id;
  doc["timestamp"] = getTimestamp();
  doc["value"] = repCount;
  doc["unit"] = "reps";
  
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["current_set"] = currentSet;
  metadata["signal_quality"] = "excellent";
  metadata["battery"] = 100;  // Implementar leitura real
  metadata["sensor_type"] = "MPU6050";
  metadata["immediate"] = immediate;
  
  char buffer[300];
  serializeJson(doc, buffer);
  
  String topic = "fitness/device/" + String(device_id) + "/reps";
  client.publish(topic.c_str(), buffer);
  
  if (!immediate) {
    Serial.printf("Status enviado: %d reps (Série %d)\n", repCount, currentSet);
  }
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
  
  // Detectar repetições continuamente
  detectRep();
  
  // Enviar atualização periódica
  if (millis() - lastSend > SEND_INTERVAL) {
    lastSend = millis();
    sendRepUpdate(false);
  }
  
  delay(50);  // Sampling rate ~20Hz
}
