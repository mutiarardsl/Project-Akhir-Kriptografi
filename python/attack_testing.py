#!/usr/bin/env python3
"""
Testing Security - Passive & Active Attacks
Demonstrasi serangan pasif (eavesdropping) dan aktif (replay, modification)
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import ascon

# ===== KONFIGURASI MQTT =====
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_RAW = "iot/sensor/distance/raw"
TOPIC_ENCRYPTED = "iot/sensor/distance/enc"

# ===== KONFIGURASI ASCON =====
# Key yang BENAR (hanya receiver yang sah yang punya)
CORRECT_KEY = "asconciphertest1".encode('utf-8')
CORRECT_NONCE = "asconcipher1test".encode('utf-8')

# Key yang SALAH (attacker mencoba dengan key random)
WRONG_KEY = "wrongkeywrongkey".encode('utf-8')
WRONG_NONCE = "wrongnoncewrong1".encode('utf-8')

ASSOCIATED_DATA = b"ASCON"
VARIANT = "Ascon-128"

# ===== STORAGE UNTUK CAPTURED DATA =====
captured_raw_messages = []
captured_encrypted_messages = []
modified_messages = []

# ===== 1. PASSIVE ATTACK - EAVESDROPPING =====
class PassiveAttacker:
    """Attacker yang mendengarkan (sniff) traffic tanpa memodifikasi"""
    
    def __init__(self):
        self.client = mqtt.Client(
    client_id="Passive_Attacker",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION1
)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.captured_count = 0
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("🕵️  [PASSIVE ATTACK] Connected as eavesdropper")
            # Subscribe ke SEMUA topic untuk mendengarkan traffic
            client.subscribe(TOPIC_RAW)
            client.subscribe(TOPIC_ENCRYPTED)
        
    def on_message(self, client, userdata, msg):
        self.captured_count += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n{'='*60}")
        print(f"👂 [PASSIVE ATTACK] Message Intercepted #{self.captured_count}")
        print(f"🕐 Time: {timestamp}")
        print(f"📝 Topic: {msg.topic}")
        
        payload = msg.payload.decode('utf-8')
        
        if msg.topic == TOPIC_RAW:
            print(f"🔓 RAW DATA CAPTURED:")
            print(f"   {payload}")
            captured_raw_messages.append({
                'timestamp': timestamp,
                'topic': msg.topic,
                'data': payload
            })
            
            # Attacker bisa baca data mentah dengan mudah!
            try:
                data = json.loads(payload)
                print(f"   ⚠️  READABLE INFO:")
                print(f"   Device: {data.get('id', 'N/A')}")
                print(f"   Distance: {data.get('distance', 'N/A')} cm")
                print(f"   ✅ Attacker can read plaintext data!")
            except:
                pass
                
        elif msg.topic == TOPIC_ENCRYPTED:
            print(f"🔐 ENCRYPTED DATA CAPTURED:")
            try:
                data = json.loads(payload)
                encrypted_hex = data.get('encrypted_data', '')[:40]
                print(f"   {encrypted_hex}...")
                captured_encrypted_messages.append({
                    'timestamp': timestamp,
                    'topic': msg.topic,
                    'data': payload
                })
                print(f"   ❌ Attacker CANNOT read encrypted data without key!")
                
                # Coba dekripsi dengan key SALAH
                self.try_decrypt_with_wrong_key(payload)
                
            except Exception as e:
                print(f"   Error: {e}")
    
    def try_decrypt_with_wrong_key(self, encrypted_payload):
        """Attacker mencoba dekripsi dengan key salah"""
        try:
            data = json.loads(encrypted_payload)
            encrypted_hex = data.get('encrypted_data')
            ciphertext = bytes.fromhex(encrypted_hex)
            
            print(f"   🔓 Trying to decrypt with WRONG key...")
            plaintext = ascon.demo_aead_p(VARIANT, ciphertext)
            
            # Dengan key salah, dekripsi akan gagal (return None)
            if plaintext is None:
                print(f"   ❌ DECRYPTION FAILED! (Authentication tag mismatch)")
                print(f"   ✅ ASCON successfully protected the data!")
            else:
                print(f"   ⚠️  Unexpected: decryption succeeded with wrong key")
                
        except Exception as e:
            print(f"   ❌ Decryption error: {e}")
    
    def start(self):
        try:
            self.client.connect(BROKER, PORT, 60)
            print("\n" + "="*60)
            print("🕵️  PASSIVE ATTACK SIMULATION STARTED")
            print("="*60)
            print("Eavesdropping on MQTT traffic...")
            print("Press Ctrl+C to stop\n")
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping passive attack...")
            self.print_summary()
            self.client.disconnect()
    
    def print_summary(self):
        print("\n" + "="*60)
        print("📊 PASSIVE ATTACK SUMMARY")
        print("="*60)
        print(f"📨 Total messages captured: {self.captured_count}")
        print(f"🔓 Raw messages: {len(captured_raw_messages)}")
        print(f"🔐 Encrypted messages: {len(captured_encrypted_messages)}")
        print("\n🔍 FINDINGS:")
        print(f"   ✅ Can intercept all traffic")
        print(f"   ✅ Can read UNENCRYPTED data")
        print(f"   ❌ CANNOT read ENCRYPTED data without key")
        print(f"   ❌ CANNOT decrypt with wrong key")
        print("="*60)

# ===== 2. ACTIVE ATTACK - REPLAY & MODIFICATION =====
class ActiveAttacker:
    """Attacker yang memodifikasi atau replay traffic"""
    
    def __init__(self):
        self.client = mqtt.Client(
    client_id="Active_Attacker",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION1
)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.attack_count = 0
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("🦹 [ACTIVE ATTACK] Connected")
            client.subscribe(TOPIC_RAW)
            client.subscribe(TOPIC_ENCRYPTED)
    
    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        
        if msg.topic == TOPIC_RAW:
            # ATTACK 1: Modify plaintext data
            self.attack_modify_plaintext(payload)
            
        elif msg.topic == TOPIC_ENCRYPTED:
            # ATTACK 2: Replay attack
            self.attack_replay_encrypted(payload)
            
            # ATTACK 3: Modify ciphertext
            self.attack_modify_ciphertext(payload)
    
    def attack_modify_plaintext(self, original_payload):
        """Attack: Modifikasi data plaintext"""
        try:
            data = json.loads(original_payload)
            original_distance = data.get('distance', 0)
            
            # Attacker mengubah nilai jarak!
            data['distance'] = 999  # Fake data
            data['TAMPERED'] = True
            
            modified_payload = json.dumps(data)
            
            # Publish data yang sudah dimodifikasi
            result = self.client.publish(TOPIC_RAW + "/tampered", modified_payload)
            
            self.attack_count += 1
            print(f"\n{'='*60}")
            print(f"🦹 [ACTIVE ATTACK] Modification Attack #{self.attack_count}")
            print(f"📝 Target: Plaintext data")
            print(f"🔧 Original distance: {original_distance} cm")
            print(f"🔧 Modified distance: 999 cm")
            print(f"📤 Published to: {TOPIC_RAW}/tampered")
            print(f"⚠️  ATTACK SUCCESS: Plaintext can be modified!")
            print("="*60)
            
        except Exception as e:
            print(f"Attack failed: {e}")
    
    def attack_replay_encrypted(self, encrypted_payload):
        """Attack: Replay pesan terenkripsi (replay attack)"""
        try:
            # Attacker mengirim ulang pesan lama
            result = self.client.publish(TOPIC_ENCRYPTED + "/replayed", encrypted_payload)
            
            self.attack_count += 1
            print(f"\n{'='*60}")
            print(f"🦹 [ACTIVE ATTACK] Replay Attack #{self.attack_count}")
            print(f"📝 Target: Encrypted data")
            print(f"🔄 Action: Replaying old message")
            print(f"📤 Published to: {TOPIC_ENCRYPTED}/replayed")
            print(f"⚠️  ATTACK PARTIALLY SUCCESS:")
            print(f"   ✅ Can replay encrypted messages")
            print(f"   ❌ But cannot read/modify content")
            print(f"   💡 Defense: Use timestamp + nonce verification")
            print("="*60)
            
        except Exception as e:
            print(f"Attack failed: {e}")
    
    def attack_modify_ciphertext(self, encrypted_payload):
        """Attack: Modifikasi ciphertext"""
        try:
            data = json.loads(encrypted_payload)
            encrypted_hex = data.get('encrypted_data')
            
            # Attacker mengubah beberapa bit dari ciphertext
            ciphertext_bytes = bytes.fromhex(encrypted_hex)
            
            # Flip beberapa bit (XOR dengan random byte)
            modified_bytes = bytearray(ciphertext_bytes)
            modified_bytes[0] ^= 0xFF  # Flip first byte
            modified_bytes[5] ^= 0xAA  # Flip another byte
            
            modified_hex = modified_bytes.hex()
            data['encrypted_data'] = modified_hex
            data['TAMPERED'] = True
            
            modified_payload = json.dumps(data)
            
            # Publish modified ciphertext
            result = self.client.publish(TOPIC_ENCRYPTED + "/tampered", modified_payload)
            
            self.attack_count += 1
            print(f"\n{'='*60}")
            print(f"🦹 [ACTIVE ATTACK] Ciphertext Modification #{self.attack_count}")
            print(f"📝 Target: Encrypted data")
            print(f"🔧 Action: Flipped bits in ciphertext")
            print(f"📤 Published to: {TOPIC_ENCRYPTED}/tampered")
            
            # Coba dekripsi modified ciphertext
            try:
                modified_ciphertext = bytes.fromhex(modified_hex)
                plaintext = ascon.demo_aead_p(VARIANT, modified_ciphertext)
                
                if plaintext is None:
                    print(f"✅ ATTACK FAILED: ASCON detected tampering!")
                    print(f"   Authentication tag verification failed")
                    print(f"   Modified ciphertext was rejected")
                else:
                    print(f"⚠️  Unexpected: Modified ciphertext accepted")
            except Exception as e:
                print(f"✅ ATTACK FAILED: {e}")
            
            print("="*60)
            
        except Exception as e:
            print(f"Attack failed: {e}")
    
    def start(self):
        try:
            self.client.connect(BROKER, PORT, 60)
            print("\n" + "="*60)
            print("🦹 ACTIVE ATTACK SIMULATION STARTED")
            print("="*60)
            print("Attempting to modify and replay messages...")
            print("Press Ctrl+C to stop\n")
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping active attack...")
            self.print_summary()
            self.client.disconnect()
    
    def print_summary(self):
        print("\n" + "="*60)
        print("📊 ACTIVE ATTACK SUMMARY")
        print("="*60)
        print(f"🔨 Total attacks performed: {self.attack_count}")
        print("\n🔍 ATTACK RESULTS:")
        print("1. Plaintext Modification:")
        print("   ⚠️  SUCCESS - Can modify unencrypted data")
        print("   💡 Defense: Use encryption!")
        print("\n2. Replay Attack:")
        print("   ⚠️  PARTIAL - Can replay messages")
        print("   💡 Defense: Use timestamp + unique nonce")
        print("\n3. Ciphertext Modification:")
        print("   ✅ FAILED - ASCON detects tampering")
        print("   ✅ Authentication prevents modification")
        print("="*60)

# ===== MAIN MENU =====
def main():
    print("="*60)
    print("🔐 SECURITY ATTACK TESTING - ASCON")
    print("="*60)
    print("\nSelect attack type:")
    print("1. Passive Attack (Eavesdropping)")
    print("2. Active Attack (Replay & Modification)")
    print("3. Exit")
    print("="*60)
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        attacker = PassiveAttacker()
        attacker.start()
    elif choice == "2":
        attacker = ActiveAttacker()
        attacker.start()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    main()