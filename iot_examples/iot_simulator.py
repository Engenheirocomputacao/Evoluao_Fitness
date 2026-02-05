#!/usr/bin/env python3
"""
Simulador Python de Dispositivo IoT
"""
import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime, timezone

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

DEVICES = [
    {"id": "SIM_HR_01", "type": "heartrate", "unit": "bpm", "min": 60, "max": 180},
    {"id": "SIM_STEP_01", "type": "steps", "unit": "steps", "min": 0, "max": 50},
]

def on_connect(client, userdata, flags, rc):
    print(f"Conectado: {rc}")

client = mqtt.Client(client_id="python_sim", protocol=mqtt.MQTTv5)
client.on_connect = on_connect

try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
except:
    print("Não foi possível conectar ao broker local.")

while True:
    try:
        for dev in DEVICES:
            val = random.randint(dev["min"], dev["max"])
            payload = {
                "device_id": dev["id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "value": val,
                "unit": dev["unit"]
            }
            topic = f"fitness/device/{dev['id']}/{dev['type']}"
            client.publish(topic, json.dumps(payload))
            print(f"Enviado {dev['type']}: {val}")
        time.sleep(5)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(e)
        time.sleep(5)
