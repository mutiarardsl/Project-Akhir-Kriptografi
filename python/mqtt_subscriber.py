#!/usr/bin/env python3
"""
MQTT Subscriber dengan ASCON Decryption
Menerima data terenkripsi, dekripsi dengan ASCON, dan tampilkan hasil
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import ascon  # Import modul ASCON yang sudah ada

# ===== KONFIGURASI MQTT =====
BROKER = "broker.hivemq.com"  # Ganti dengan broker Anda
PORT = 1883
TOPIC_ENCRYPTED = "iot/sensor/distance/enc"
CLIENT_ID = "Python_Decryptor"

# ===== KONFIGURASI ASCON =====
# Key dan nonce HARUS SAMA dengan yang digunakan untuk enkripsi
KEY = "asconciphertest1".encode('utf-8')  # 16 bytes key
NONCE = "asconcipher1test".encode('utf-8')  # 16 bytes nonce
ASSOCIATED_DATA = b"ASCON"
VARIANT = "Ascon-128"

# ===== STATISTIK =====
stats = {
    "total_messages": 0,
    "decrypted_messages": 0,
    "failed_decryptions": 0,
    "total_decryption_time": 0,
    "start_time": time.time()
}

# ===== FUNGSI DEKRIPSI =====
def decrypt_data(ciphertext_bytes):
    """
    Dekripsi data menggunakan ASCON
    """
    try:
        # Dekripsi menggunakan ASCON
        plaintext_bytes = ascon.demo_aead_p(VARIANT, ciphertext_bytes)
        
        if plaintext_bytes is None:
            print("❌ Decryption failed: Authentication tag mismatch!")
            return None
        
        # Convert bytes ke string
        plaintext = plaintext_bytes.decode('utf-8')
        return plaintext
        
    except Exception as e:
        print(f"❌ Decryption error: {e}")
        return None

# ===== CALLBACK SAAT TERHUBUNG =====
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        print(f"📡 Subscribing to topic: {TOPIC_ENCRYPTED}")
        client.subscribe(TOPIC_ENCRYPTED)
    else:
        print(f"❌ Failed to connect, return code {rc}")

# ===== CALLBACK SAAT MENERIMA PESAN =====
def on_message(client, userdata, msg):
    try:
        stats["total_messages"] += 1
        
        # Decode payload
        payload = msg.payload.decode('utf-8')
        
        print(f"\n{'='*60}")
        print(f"📩 Received encrypted message #{stats['total_messages']}")
        print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📝 Topic: {msg.topic}")
        
        # Parse JSON
        try:
            encrypted_payload = json.loads(payload)
            encrypted_hex = encrypted_payload.get("encrypted_data")
            original_encryption_time = encrypted_payload.get("encryption_time_ms", 0)
            
            print(f"🔢 Encrypted data (hex): {encrypted_hex[:32]}...")
            print(f"📏 Encrypted size: {encrypted_payload.get('encrypted_size', 'N/A')} bytes")
            print(f"⏱️  Original encryption time: {original_encryption_time} ms")
            
        except Exception as e:
            print(f"❌ Error parsing JSON: {e}")
            return
        
        # Convert hex string ke bytes
        try:
            ciphertext_bytes = bytes.fromhex(encrypted_hex)
        except Exception as e:
            print(f"❌ Error converting hex to bytes: {e}")
            stats["failed_decryptions"] += 1
            return
        
        # Dekripsi data
        print("🔓 Decrypting with ASCON...")
        start_time = time.time()
        
        decrypted_data = decrypt_data(ciphertext_bytes)
        
        decryption_time = (time.time() - start_time) * 1000  # Convert to ms
        stats["total_decryption_time"] += decryption_time
        
        if decrypted_data:
            stats["decrypted_messages"] += 1
            
            print(f"✅ Decryption successful!")
            print(f"⏱️  Decryption time: {decryption_time:.3f} ms")
            print(f"📦 Decrypted data: {decrypted_data}")
            
            # Parse decrypted JSON data
            try:
                sensor_data = json.loads(decrypted_data)
                print("\n📊 Sensor Information:")
                print(f"   🆔 Device ID: {sensor_data.get('id', 'N/A')}")
                print(f"   🔢 Message Count: {sensor_data.get('count', 'N/A')}")
                print(f"   📏 Distance: {sensor_data.get('distance', 'N/A')} {sensor_data.get('unit', '')}")
                print(f"   ⏰ Device Timestamp: {sensor_data.get('timestamp', 'N/A')}")
            except:
                print("   (Not JSON format)")
                
        else:
            stats["failed_decryptions"] += 1
            print("❌ Decryption FAILED!")
            
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        stats["failed_decryptions"] += 1

# ===== CALLBACK DISCONNECT =====
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"⚠️  Unexpected disconnection. Code: {rc}")
        print("🔄 Attempting to reconnect...")

# ===== MAIN PROGRAM =====
def main():
    print("="*60)
    print("🚀 MQTT Subscriber with ASCON Decryption")
    print("="*60)
    print(f"📡 Broker: {BROKER}:{PORT}")
    print(f"📥 Subscribe: {TOPIC_ENCRYPTED}")
    print(f"🔓 Algorithm: {VARIANT}")
    print("="*60)
    
    # Setup MQTT Client
    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Connect ke broker
    try:
        print(f"\n🔌 Connecting to broker...")
        client.connect(BROKER, PORT, 60)
        
        # Start loop
        print("✅ Starting MQTT loop...")
        print("⌨️  Press Ctrl+C to stop\n")
        
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        print_statistics()
        client.disconnect()
        print("👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

# ===== FUNGSI STATISTIK =====
def print_statistics():
    runtime = time.time() - stats["start_time"]
    print("\n" + "="*60)
    print("📊 STATISTICS")
    print("="*60)
    print(f"⏱️  Runtime: {runtime:.2f} seconds")
    print(f"📨 Total messages received: {stats['total_messages']}")
    print(f"🔓 Successfully decrypted: {stats['decrypted_messages']}")
    print(f"❌ Failed decryptions: {stats['failed_decryptions']}")
    
    if stats['total_messages'] > 0:
        success_rate = (stats['decrypted_messages'] / stats['total_messages']) * 100
        print(f"✅ Success rate: {success_rate:.2f}%")
    
    if stats['decrypted_messages'] > 0:
        avg_time = stats['total_decryption_time'] / stats['decrypted_messages']
        print(f"⏱️  Average decryption time: {avg_time:.3f} ms")
    
    print("="*60)

if __name__ == "__main__":
    main()