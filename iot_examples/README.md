# 📡 IoT Examples - Códigos para Dispositivos ESP32

Esta pasta contém **exemplos funcionais** de código Arduino para ESP32 e um simulador Python para integração IoT com o sistema Evolução Fitness.

## 🎯 Visão Geral

O sistema suporta **7 tipos de dispositivos IoT**:

| Tipo | Descrição | Arquivo Hardware | Simulador |
|------|-----------|-----------------|-----------|
| ❤️ **heartrate** | Monitor de Frequência Cardíaca | `esp32_heartrate_monitor.ino` | ✅ Sim |
| 👣 **steps** | Contador de Passos (Pedômetro) | `esp32_step_counter.ino` | ✅ Sim |
| 🏋️ **reps** | Contador de Repetições | `esp32_rep_counter.ino` | ✅ Sim |
| 📍 **gps** | Rastreador GPS | `esp32_gps_tracker.ino` | ✅ Sim |
| ⚖️ **weight** | Balança Inteligente | (a implementar) | ✅ Sim |
| 🌡️ **temperature** | Sensor de Temperatura | (a implementar) | ❌ Não |
| 🔧 **generic** | Dispositivo Genérico | `esp32_simulator.ino` | ✅ Sim |

---

## 🔧 Arquivos Disponíveis

### 1. **esp32_heartrate_monitor.ino** - Monitor Cardíaco Real

**Hardware necessário:**
- ESP32
- Sensor MAX30102 (Oxímetro de Pulso)
- Conexões I2C: SDA=GPIO21, SCL=GPIO22

**Bibliotecas necessárias:**
```
- WiFi (built-in ESP32)
- PubSubClient (MQTT)
- ArduinoJson
- MAX30105 (SparkFun)
- heartRate (SparkFun)
```

**Funcionalidades:**
- Lê batimentos cardíacos do sensor MAX30102
- Calcula média móvel (4 leituras)
- Envia dados via MQTT
- Detecta qualidade do sinal automaticamente

**Configurar:**
```cpp
const char* ssid = "SEU_WIFI_SSID";
const char* password = "SUA_SENHA_WIFI";
const char* mqtt_server = "IP_DO_SERVIDOR";
const char* device_id = "ESP32_HEART_001";
const int user_id = 1;  // ID do usuário no Django
```

---

### 2. **esp32_gps_tracker.ino** - Rastreador GPS

**Hardware necessário:**
- ESP32
- Módulo GPS NEO-6M ou NEO-7M
- Conexões: GPS TX → ESP32 GPIO16, GPS RX → ESP32 GPIO17

**Bibliotecas necessárias:**
```
- WiFi (built-in ESP32)
- PubSubClient (MQTT)
- ArduinoJson
- TinyGPS++
```

**Funcionalidades:**
- Rastreia coordenadas GPS em tempo real
- Calcula distância percorrida (Haversine)
- Envia velocidade, altitude e número de satélites
- Qualidade de sinal baseada em satélites visíveis

**Dados enviados:**
```json
{
  "device_id": "ESP32_GPS_001",
  "value": 1542.5,
  "unit": "meters",
  "metadata": {
    "latitude": -23.5505,
    "longitude": -46.6333,
    "speed": 8.5,
    "altitude": 732,
    "satellites": 9
  }
}
```

---

### 3. **esp32_rep_counter.ino** - Contador de Repetições

**Hardware necessário:**
- ESP32
- Acelerômetro MPU6050
- Conexões I2C: SDA=GPIO21, SCL=GPIO22

**Bibliotecas necessárias:**
```
- WiFi (built-in ESP32)
- PubSubClient (MQTT)
- ArduinoJson
- Adafruit_MPU6050
- Adafruit_Sensor
```

**Funcionalidades:**
- Detecta repetições de exercícios por movimento
- Conta séries automaticamente
- Filtra falsos positivos (cooldown de 500ms)
- Suporta comandos MQTT (reset_reps, next_set)

**Como usar:**
1. Fixe o ESP32+MPU6050 no braço/perna
2. Faça exercícios de musculação
3. O sistema detecta cada repetição completa
4. Dados são enviados em tempo real

---

### 4. **esp32_step_counter.ino** - Pedômetro Inteligente

**Hardware necessário:**
- ESP32
- Acelerômetro MPU6050
- Conexões I2C: SDA=GPIO21, SCL=GPIO22

**Bibliotecas necessárias:**
```
- WiFi (built-in ESP32)
- PubSubClient (MQTT)
- ArduinoJson
- Adafruit_MPU6050
- Adafruit_Sensor
```

**Funcionalidades:**
- Conta passos com algoritmo de detecção de pico
- Calcula distância percorrida (75cm por passo)
- Estima calorias queimadas (~0.04 cal/passo)
- Filtra movimentos falsos

**Dados enviados:**
```json
{
  "value": 5842,
  "unit": "steps",
  "metadata": {
    "distance_meters": 4381.5,
    "distance_km": 4.38,
    "calories": 233.7
  }
}
```

---

### 5. **esp32_simulator.ino** - Simulador Simples

**Hardware necessário:**
- Apenas ESP32 (sem sensores)

**Uso:**
- Para testes sem hardware físico
- Gera valores aleatórios de heartrate
- Ideal para desenvolvimento inicial

---

### 6. **iot_simulator.py** - Simulador Python Completo ⭐

**Requisitos:**
```bash
pip install paho-mqtt
```

**Funcionalidades:**
- Simula **TODOS** os tipos de dispositivos simultaneamente
- Não precisa de ESP32
- Roda direto no computador
- Ótimo para desenvolvimento e testes

**Como usar:**
```bash
# 1. Certifique-se de que o broker MQTT está rodando
# (o Django já tem um configurado)

# 2. Execute o simulador
python iot_examples/iot_simulator.py

# 3. Veja os dados chegando no dashboard IoT do sistema
```

**Dispositivos simulados:**
- ❤️ Monitor Cardíaco (60-180 bpm)
- 👣 Pedômetro (cumulativo)
- 🏋️ Contador de Repetições (8-15 reps)
- 📍 GPS Tracker (com coordenadas)
- ⚖️ Balança (70-75 kg)

---

## 🚀 Como Começar

### Opção 1: Testar SEM Hardware (Recomendado)

```bash
# Instalar dependências Python
pip install paho-mqtt

# Rodar simulador
python iot_examples/iot_simulator.py
```

Acesse o dashboard IoT no sistema e veja os dados chegando em tempo real!

---

### Opção 2: Usar Hardware Real (ESP32)

#### Passo 1: Instalar Arduino IDE
- Download: https://www.arduino.cc/en/software
- Adicionar suporte ESP32: https://github.com/espressif/arduino-esp32

#### Passo 2: Instalar Bibliotecas

No Arduino IDE, vá em **Sketch → Include Library → Manage Libraries** e instale:

```
✓ PubSubClient (by Nick O'Leary)
✓ ArduinoJson (by Benoit Blanchon)
✓ Adafruit MPU6050 (se usar acelerômetro)
✓ TinyGPS++ (se usar GPS)
✓ SparkFun MAX3010x (se usar sensor cardíaco)
```

#### Passo 3: Configurar o Código

Edite o arquivo `.ino` escolhido:

```cpp
// Configurar WiFi
const char* ssid = "SEU_WIFI_SSID";
const char* password = "SUA_SENHA_WIFI";

// Configurar servidor MQTT (IP do seu computador rodando Django)
const char* mqtt_server = "192.168.1.100";  // Altere aqui!

// ID único do dispositivo
const char* device_id = "ESP32_HEART_001";

// ID do usuário no sistema Django
const int user_id = 1;  // Verifique no admin do Django
```

#### Passo 4: Upload para ESP32

1. Conecte o ESP32 via USB
2. Selecione a placa: **Tools → Board → ESP32 Dev Module**
3. Selecione a porta: **Tools → Port → COMx** (Windows) ou **/dev/ttyUSB0** (Linux)
4. Clique em **Upload** ➡️

#### Passo 5: Verificar Funcionamento

Abra o **Serial Monitor** (Ctrl+Shift+M) e verifique:
```
ESP32 ... - Iniciando...
Conectando ao WiFi: ...
WiFi conectado!
Endereço IP: 192.168.1.xxx
Conectando ao MQTT...conectado!
```

---

## 📊 Visualizando os Dados

1. Acesse o sistema Django
2. Vá para **IoT Dashboard** (menu superior)
3. Cadastre o dispositivo manualmente ou aguarde auto-registro
4. Veja os dados chegando em tempo real!

---

## 🔌 Configuração do Broker MQTT

O sistema Django já tem um serviço MQTT configurado:

**Arquivo:** `controle_treinamento/settings.py`
```python
MQTT_BROKER_HOST = 'localhost'
MQTT_BROKER_PORT = 1883
MQTT_CLIENT_ID = 'django_fitness_server'
MQTT_BASE_TOPIC = 'fitness/device'
```

### Instalar Mosquitto (Broker MQTT)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

**Windows:**
- Download: https://mosquitto.org/download/
- Instalar e iniciar o serviço

**Testar conexão:**
```bash
# Terminal 1 - Subscriber
mosquitto_sub -t "fitness/device/#" -v

# Terminal 2 - Publisher (teste)
mosquitto_pub -t "fitness/device/test/heartrate" -m '{"value": 75}'
```

---

## 🎯 Estrutura dos Dados MQTT

### Tópicos (Topics)

```
fitness/device/{DEVICE_ID}/{SENSOR_TYPE}
```

**Exemplos:**
- `fitness/device/ESP32_HEART_001/heartrate`
- `fitness/device/ESP32_GPS_001/gps`
- `fitness/device/SIM_STEPS_01/steps`

### Payload JSON

```json
{
  "device_id": "ESP32_HEART_001",
  "device_name": "Monitor Cardíaco Principal",
  "user_id": 1,
  "timestamp": "2026-01-25T15:30:00Z",
  "value": 150,
  "unit": "bpm",
  "metadata": {
    "signal_quality": "excellent",
    "battery": 85,
    "sensor_type": "MAX30102"
  }
}
```

---

## 🛠️ Troubleshooting

### Problema: ESP32 não conecta ao WiFi
```
✓ Verificar SSID e senha
✓ ESP32 só suporta WiFi 2.4GHz (não 5GHz)
✓ Verificar se o roteador permite novos dispositivos
```

### Problema: Não conecta ao MQTT
```
✓ Verificar se broker Mosquitto está rodando: systemctl status mosquitto
✓ Verificar firewall (porta 1883)
✓ Verificar IP do servidor no código
✓ Testar com mosquitto_pub/sub
```

### Problema: Sensor não detectado
```
✓ Verificar conexões físicas (SDA, SCL, VCC, GND)
✓ Usar scanner I2C para detectar endereço
✓ Verificar se biblioteca está instalada corretamente
```

### Problema: Dados não aparecem no Django
```
✓ Verificar logs do Django: python manage.py runserver
✓ Verificar se dispositivo está cadastrado
✓ Verificar tópico MQTT está correto
✓ Verificar serviço MQTT do Django está ativo
```

---

## 📚 Próximos Passos

1. **Começar com o simulador Python** para entender o fluxo
2. **Montar um ESP32 com sensor simples** (exemplo: heartrate)
3. **Testar comunicação MQTT** com mosquitto_sub
4. **Visualizar dados** no dashboard IoT
5. **Expandir com mais sensores** conforme necessidade

---

## 🤝 Contribuindo

Sinta-se livre para:
- Adicionar novos sensores
- Melhorar algoritmos de detecção
- Otimizar consumo de bateria
- Criar novos simuladores

---

## 📄 Licença

Estes códigos são exemplos educacionais e podem ser modificados livremente para seu projeto.

---

**Dúvidas?** Consulte a documentação do Django em `ARCHITECTURE.md` ou abra uma issue no repositório.
