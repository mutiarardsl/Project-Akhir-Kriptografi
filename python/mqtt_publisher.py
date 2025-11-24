#!/usr/bin/env python3
"""
MQTT Publisher dengan ASCON Encryption + ThingSpeak Integration
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import ascon  
import requests

# ===== KONFIGURASI MQTT =====
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_RAW = "iot/sensor/distance/raw"
TOPIC_ENCRYPTED = "iot/sensor/distance/enc"
CLIENT_ID = "Python_Encryptor"
THINGSPEAK_API = "ET2DBONJU765X8CC"

# ===== KONFIGURASI ASCON =====
KEY = "asconciphertest1".encode('utf-8')      # 16 bytes
NONCE = "asconcipher1test".encode('utf-8')    # 16 bytes
ASSOCIATED_DATA = b"ASCON"
VARIANT = "Ascon-128"

# ===== STATISTIK =====
stats = {
    "total_messages": 0,
    "encrypted_messages": 0,
    "errors": 0,
    "start_time": time.time()
}

# ===== FUNGSI THINGSPEAK =====
def send_to_thingspeak(distance, enc_time):
    url = (
        f"https://api.thingspeak.com/update?api_key={THINGSPEAK_API}"
        f"&field1={distance}&field2={enc_time}"
    )
    try:
        requests.get(url)
        print("🌐 Sent to ThingSpeak!")
    except Exception as e:
        print(f"❌ ThingSpeak Error: {e}")

# ===== FUNGSI ENKRIPSI =====
def encrypt_data(plaintext_data):
    try:
        if isinstance(plaintext_data, dict):
            plaintext_data = json.dumps(plaintext_data)
        
        ciphertext = ascon.demo_aead_c(
            VARIANT,
            plaintext_data,
            KEY,
            NONCE,
            ASSOCIATED_DATA
        )
        return ciphertext
    
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        return None

# ===== CALLBACK CONNECT =====
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC_RAW)
    else:
        print(f"❌ Failed to connect. Code: {rc}")

# ===== CALLBACK MESSAGE =====
def on_message(client, userdata, msg):
    try:
        stats["total_messages"] += 1
        
        payload = msg.payload.decode('utf-8')
        print("\n" + "="*60)
        print(f"📩 Message #{stats['total_messages']}")
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📝 Topic: {msg.topic}")
        print(f"📦 Raw: {payload}")

        # Parsing JSON
        try:
            data = json.loads(payload)
            distance = data.get("distance", None)
            print(f"📊 Distance: {distance} cm")
        except:
            data = payload
            distance = None

        # Enkripsi
        print("🔐 Encrypting with ASCON...")
        start_time = time.time()
        encrypted_data = encrypt_data(payload)
        encryption_time = round((time.time() - start_time) * 1000, 3)

        if encrypted_data:
            encrypted_hex = encrypted_data.hex()

            encrypted_payload = {
                "encrypted_data": encrypted_hex,
                "encryption_time_ms": encryption_time,
                "algorithm": VARIANT,
                "timestamp": datetime.now().isoformat(),
                "original_size": len(payload),
                "encrypted_size": len(encrypted_data)
            }

            result = client.publish(TOPIC_ENCRYPTED, json.dumps(encrypted_payload))

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                stats["encrypted_messages"] += 1
                print(f"✅ Encrypted data published!")
                print(f"⏱️ Time: {encryption_time} ms")
                print(f"🔢 Preview: {encrypted_hex[:32]}...")

                # === SEND TO THINGSPEAK ===
                if distance is not None:
                    send_to_thingspeak(distance, encryption_time)
                else:
                    print("⚠️ No distance field, skipping ThingSpeak")
            else:
                print("❌ Failed to publish encrypted data")
                stats["errors"] += 1
        else:
            stats["errors"] += 1

    except Exception as e:
        print(f"❌ Message Handling Error: {e}")
        stats["errors"] += 1

# ===== CALLBACK DISCONNECT =====
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"⚠️ Unexpected disconnect ({rc})")

# ===== STATISTIK =====
def print_statistics():
    runtime = time.time() - stats["start_time"]
    print("\n" + "="*60)
    print("📊 FINAL STATISTICS")
    print("="*60)
    print(f"⏱️ Runtime: {runtime:.2f} sec")
    print(f"📨 Total messages: {stats['total_messages']}")
    print(f"🔐 Encrypted: {stats['encrypted_messages']}")
    print(f"❌ Errors: {stats['errors']}")
    if stats["total_messages"] > 0:
        rate = (stats["encrypted_messages"] / stats["total_messages"]) * 100
        print(f"✅ Success Rate: {rate:.2f}%")
    print("="*60)

# ===== MAIN =====
def main():
    print("="*60)
    print("🚀 MQTT ASCON Encryptor + ThingSpeak")
    print("="*60)

    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        print("\n🔌 Connecting...")
        client.connect(BROKER, PORT, 60)
        print("✅ Connected. Waiting for messages...\n")
        client.loop_forever()

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        print_statistics()
        client.disconnect()

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
