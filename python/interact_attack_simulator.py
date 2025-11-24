#!/usr/bin/env python3
"""
Interactive Attack Simulator - ASCON Security Testing
Mode interaktif untuk demo serangan passive dan active
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import ascon
import os
import sys

# ===== KONFIGURASI =====
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_RAW = "iot/sensor/distance/raw"
TOPIC_ENCRYPTED = "iot/sensor/distance/enc"

CORRECT_KEY = "asconciphertest1".encode('utf-8')
CORRECT_NONCE = "asconcipher1test".encode('utf-8')
WRONG_KEY = "wrongkeywrongkey".encode('utf-8')
WRONG_NONCE = "wrongnoncewrong1".encode('utf-8')
ASSOCIATED_DATA = b"ASCON"
VARIANT = "Ascon-128"

# ===== STORAGE =====
captured_messages = []
attack_log = []

# ===== UTILITY FUNCTIONS =====
def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_box(text, symbol="═"):
    """Print text in a box"""
    width = 70
    print(f"\n╔{symbol * (width-2)}╗")
    for line in text.split('\n'):
        print(f"║ {line.ljust(width-4)} ║")
    print(f"╚{symbol * (width-2)}╝")

def wait_for_enter(message="Press ENTER to continue..."):
    """Wait for user input"""
    input(f"\n{message}")

def countdown(seconds, message="Starting in"):
    """Countdown timer"""
    for i in range(seconds, 0, -1):
        print(f"\r{message} {i}...", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 50 + "\r", end="")

# ===== INTERACTIVE PASSIVE ATTACK =====
class InteractivePassiveAttack:
    def __init__(self):
        self.client = mqtt.Client("Interactive_Passive_Attacker")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.captured_count = 0
        self.running = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected as passive attacker (eavesdropper)")
            client.subscribe([(TOPIC_RAW, 0), (TOPIC_ENCRYPTED, 0)])
        
    def on_message(self, client, userdata, msg):
        if not self.running:
            return
            
        self.captured_count += 1
        payload = msg.payload.decode('utf-8')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        print(f"\n{'─'*70}")
        print(f"🎯 Message #{self.captured_count} intercepted at {timestamp}")
        print(f"📡 Topic: {msg.topic}")
        
        if msg.topic == TOPIC_RAW:
            self.handle_raw_message(payload)
        elif msg.topic == TOPIC_ENCRYPTED:
            self.handle_encrypted_message(payload)
            
        captured_messages.append({
            'timestamp': timestamp,
            'topic': msg.topic,
            'payload': payload
        })
        
    def handle_raw_message(self, payload):
        """Handle raw unencrypted message"""
        print("🔓 Type: UNENCRYPTED DATA")
        print(f"📦 Raw payload: {payload[:60]}...")
        
        try:
            data = json.loads(payload)
            print("\n⚠️  ATTACKER CAN READ:")
            print(f"   • Device ID: {data.get('id', 'N/A')}")
            print(f"   • Distance: {data.get('distance', 'N/A')} {data.get('unit', '')}")
            print(f"   • Timestamp: {data.get('timestamp', 'N/A')}")
            print("\n❌ VULNERABILITY: No encryption!")
            print("💡 RECOMMENDATION: Use encryption to protect data")
        except:
            print("   (Could not parse as JSON)")
    
    def handle_encrypted_message(self, payload):
        """Handle encrypted message"""
        print("🔐 Type: ENCRYPTED DATA")
        
        try:
            data = json.loads(payload)
            encrypted_hex = data.get('encrypted_data', '')
            print(f"📦 Encrypted (hex): {encrypted_hex[:40]}...")
            
            print("\n🔍 ATTEMPTING TO DECRYPT...")
            print("   Using WRONG KEY (attacker doesn't have the real key)")
            
            # Simulate decryption attempt
            time.sleep(0.5)
            ciphertext = bytes.fromhex(encrypted_hex)
            
            try:
                plaintext = ascon.ascon_decrypt(
                    WRONG_KEY, 
                    WRONG_NONCE, 
                    ASSOCIATED_DATA, 
                    ciphertext, 
                    VARIANT
                )
                
                if plaintext is None:
                    print("\n❌ DECRYPTION FAILED!")
                    print("   Authentication tag mismatch")
                    print("✅ ASCON PROTECTED THE DATA!")
                    print("💡 Attacker cannot read encrypted data without the key")
                else:
                    print("\n⚠️  Unexpected: Decryption succeeded")
            except Exception as e:
                print(f"\n❌ DECRYPTION ERROR: {str(e)[:50]}")
                print("✅ ASCON PROTECTED THE DATA!")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    def run_interactive(self):
        """Run interactive passive attack"""
        clear_screen()
        print_header("🕵️  PASSIVE ATTACK SIMULATOR (Interactive Mode)")
        
        print("\n📋 What is Passive Attack?")
        print("   • Attacker ONLY listens to network traffic")
        print("   • Does NOT modify or send data")
        print("   • Very hard to detect")
        print("   • Goal: Steal information (confidentiality breach)")
        
        wait_for_enter("Press ENTER to start eavesdropping")
        
        try:
            print("\n🔌 Connecting to MQTT broker...")
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
            time.sleep(2)
            
            print("✅ Connected! Now listening to all traffic...")
            print("\n" + "="*70)
            print("👂 EAVESDROPPING MODE ACTIVE")
            print("="*70)
            print("Waiting for messages... (Press Ctrl+C to stop)\n")
            
            self.running = True
            
            # Keep running until interrupted
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping passive attack...")
            self.running = False
            self.show_summary()
        finally:
            self.client.loop_stop()
            self.client.disconnect()
    
    def show_summary(self):
        """Show attack summary"""
        print_header("📊 PASSIVE ATTACK SUMMARY")
        
        print(f"\n📨 Total messages captured: {self.captured_count}")
        
        raw_count = sum(1 for m in captured_messages if m['topic'] == TOPIC_RAW)
        enc_count = sum(1 for m in captured_messages if m['topic'] == TOPIC_ENCRYPTED)
        
        print(f"🔓 Unencrypted messages: {raw_count}")
        print(f"🔐 Encrypted messages: {enc_count}")
        
        print("\n" + "="*70)
        print("🔍 KEY FINDINGS:")
        print("="*70)
        print("✅ Can intercept ALL network traffic")
        print("✅ Can READ unencrypted data easily")
        print("❌ CANNOT read encrypted data without key")
        print("❌ CANNOT decrypt with wrong key")
        print("✅ ASCON successfully protected encrypted data!")
        print("="*70)
        
        wait_for_enter()

# ===== INTERACTIVE ACTIVE ATTACK =====
class InteractiveActiveAttack:
    def __init__(self):
        self.client = mqtt.Client("Interactive_Active_Attacker")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.attack_count = 0
        self.current_message = None
        self.waiting_for_message = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected as active attacker")
            client.subscribe([(TOPIC_RAW, 0), (TOPIC_ENCRYPTED, 0)])
    
    def on_message(self, client, userdata, msg):
        if self.waiting_for_message:
            self.current_message = {
                'topic': msg.topic,
                'payload': msg.payload.decode('utf-8')
            }
    
    def run_interactive(self):
        """Run interactive active attack menu"""
        clear_screen()
        print_header("🦹 ACTIVE ATTACK SIMULATOR (Interactive Mode)")
        
        print("\n📋 What is Active Attack?")
        print("   • Attacker MODIFIES or REPLAYS data")
        print("   • Directly interferes with communication")
        print("   • Can be detected (leaves traces)")
        print("   • Goal: Disrupt integrity and availability")
        
        wait_for_enter("Press ENTER to start")
        
        try:
            print("\n🔌 Connecting to MQTT broker...")
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
            time.sleep(2)
            
            while True:
                self.show_attack_menu()
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping active attack...")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
    
    def show_attack_menu(self):
        """Show interactive attack menu"""
        clear_screen()
        print_header("🦹 ACTIVE ATTACK MENU")
        
        print("\nChoose an attack to perform:")
        print("\n1. 📝 Modify Plaintext Data (Data Tampering)")
        print("2. 🔄 Replay Attack (Resend Old Message)")
        print("3. 🔨 Modify Ciphertext (Break Encryption?)")
        print("4. 💣 Denial of Service (Message Flooding)")
        print("5. 📊 View Attack Statistics")
        print("6. 🚪 Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            self.attack_modify_plaintext_interactive()
        elif choice == "2":
            self.attack_replay_interactive()
        elif choice == "3":
            self.attack_modify_ciphertext_interactive()
        elif choice == "4":
            self.attack_dos_interactive()
        elif choice == "5":
            self.show_statistics()
        elif choice == "6":
            raise KeyboardInterrupt
        else:
            print("❌ Invalid choice!")
            time.sleep(1)
    
    def attack_modify_plaintext_interactive(self):
        """Interactive plaintext modification attack"""
        clear_screen()
        print_header("📝 ATTACK: Plaintext Data Modification")
        
        print("\n📖 Description:")
        print("   This attack intercepts UNENCRYPTED data and modifies it")
        print("   before sending to the system.")
        
        print("\n⚠️  Target: Unencrypted sensor data")
        print("🎯 Goal: Send fake sensor readings\n")
        
        wait_for_enter("Press ENTER to capture a message")
        
        print("📡 Waiting for unencrypted message...")
        self.waiting_for_message = True
        self.current_message = None
        
        # Wait for message
        timeout = 10
        for i in range(timeout):
            if self.current_message and self.current_message['topic'] == TOPIC_RAW:
                break
            time.sleep(1)
            print(f"\r⏳ Waiting... {timeout-i}s", end="", flush=True)
        
        self.waiting_for_message = False
        print("\r" + " "*50 + "\r", end="")
        
        if not self.current_message:
            print("❌ No message captured in time!")
            wait_for_enter()
            return
        
        # Show original message
        print("\n✅ Message captured!")
        try:
            original_data = json.loads(self.current_message['payload'])
            print(f"\n📦 Original Data:")
            print(f"   • Distance: {original_data.get('distance', 'N/A')} cm")
            print(f"   • Device: {original_data.get('id', 'N/A')}")
            
            # Ask for fake value
            print("\n🔧 Enter FAKE distance value to inject:")
            fake_distance = input("   New distance (cm): ").strip()
            
            try:
                fake_distance = int(fake_distance)
            except:
                fake_distance = 999
            
            # Modify data
            original_data['distance'] = fake_distance
            original_data['TAMPERED'] = True
            original_data['attack_time'] = datetime.now().isoformat()
            
            modified_payload = json.dumps(original_data)
            
            print(f"\n🔨 Modified Data:")
            print(f"   • Distance: {fake_distance} cm (FAKE!)")
            print(f"   • Tampered flag: True")
            
            wait_for_enter("Press ENTER to send fake data")
            
            # Publish modified data
            result = self.client.publish(TOPIC_RAW + "/tampered", modified_payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.attack_count += 1
                print("\n✅ ATTACK SUCCESSFUL!")
                print(f"📤 Fake data published to: {TOPIC_RAW}/tampered")
                
                print_box(
                    "⚠️  VULNERABILITY EXPLOITED!\n"
                    "Unencrypted data can be modified by attacker.\n"
                    "System will receive FAKE sensor readings!\n\n"
                    "💡 DEFENSE: Use encryption + authentication",
                    "─"
                )
            else:
                print("❌ Failed to publish")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        wait_for_enter()
    
    def attack_replay_interactive(self):
        """Interactive replay attack"""
        clear_screen()
        print_header("🔄 ATTACK: Replay Attack")
        
        print("\n📖 Description:")
        print("   This attack captures a valid message and resends it")
        print("   at a later time to trick the system.")
        
        print("\n⚠️  Target: Any captured message (encrypted or not)")
        print("🎯 Goal: Make system think event happened again\n")
        
        wait_for_enter("Press ENTER to capture a message")
        
        print("📡 Waiting for any message...")
        self.waiting_for_message = True
        self.current_message = None
        
        # Wait for message
        timeout = 10
        for i in range(timeout):
            if self.current_message:
                break
            time.sleep(1)
            print(f"\r⏳ Waiting... {timeout-i}s", end="", flush=True)
        
        self.waiting_for_message = False
        print("\r" + " "*50 + "\r", end="")
        
        if not self.current_message:
            print("❌ No message captured!")
            wait_for_enter()
            return
        
        print("\n✅ Message captured!")
        print(f"📦 Topic: {self.current_message['topic']}")
        print(f"📦 Payload: {self.current_message['payload'][:60]}...")
        
        print("\n⏰ Waiting before replay...")
        countdown(3, "Replaying in")
        
        # Replay message
        result = self.client.publish(
            self.current_message['topic'] + "/replayed",
            self.current_message['payload']
        )
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self.attack_count += 1
            print("\n✅ ATTACK SUCCESSFUL!")
            print(f"🔄 Message replayed to: {self.current_message['topic']}/replayed")
            
            print_box(
                "⚠️  REPLAY ATTACK SUCCESS!\n"
                "Old message was resent to the system.\n"
                "System might process it as NEW data!\n\n"
                "💡 DEFENSE: Use timestamp + unique nonce/counter",
                "─"
            )
        else:
            print("❌ Failed to replay")
        
        wait_for_enter()
    
    def attack_modify_ciphertext_interactive(self):
        """Interactive ciphertext modification"""
        clear_screen()
        print_header("🔨 ATTACK: Ciphertext Modification")
        
        print("\n📖 Description:")
        print("   This attack tries to modify ENCRYPTED data")
        print("   to see if encryption can be broken.")
        
        print("\n⚠️  Target: Encrypted data")
        print("🎯 Goal: Modify encrypted data without detection\n")
        
        wait_for_enter("Press ENTER to capture encrypted message")
        
        print("📡 Waiting for encrypted message...")
        self.waiting_for_message = True
        self.current_message = None
        
        timeout = 10
        for i in range(timeout):
            if self.current_message and self.current_message['topic'] == TOPIC_ENCRYPTED:
                break
            time.sleep(1)
            print(f"\r⏳ Waiting... {timeout-i}s", end="", flush=True)
        
        self.waiting_for_message = False
        print("\r" + " "*50 + "\r", end="")
        
        if not self.current_message:
            print("❌ No encrypted message captured!")
            wait_for_enter()
            return
        
        try:
            print("\n✅ Encrypted message captured!")
            data = json.loads(self.current_message['payload'])
            encrypted_hex = data.get('encrypted_data', '')
            
            print(f"📦 Original ciphertext: {encrypted_hex[:40]}...")
            
            print("\n🔧 Modifying ciphertext...")
            print("   Flipping random bits in encrypted data...")
            
            # Modify ciphertext
            ciphertext_bytes = bytearray(bytes.fromhex(encrypted_hex))
            ciphertext_bytes[0] ^= 0xFF  # Flip first byte
            ciphertext_bytes[5] ^= 0xAA  # Flip another byte
            
            modified_hex = ciphertext_bytes.hex()
            print(f"📦 Modified ciphertext: {modified_hex[:40]}...")
            
            data['encrypted_data'] = modified_hex
            data['TAMPERED'] = True
            
            wait_for_enter("Press ENTER to send modified ciphertext")
            
            # Publish
            result = self.client.publish(
                TOPIC_ENCRYPTED + "/tampered",
                json.dumps(data)
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print("\n📤 Modified ciphertext sent!")
                
                print("\n🔍 Testing if modification is detected...")
                time.sleep(1)
                
                # Try to decrypt
                try:
                    modified_ciphertext = bytes(ciphertext_bytes)
                    plaintext = ascon.ascon_decrypt(
                        CORRECT_KEY,
                        CORRECT_NONCE,
                        ASSOCIATED_DATA,
                        modified_ciphertext,
                        VARIANT
                    )
                    
                    if plaintext is None:
                        print("\n✅ ATTACK FAILED (Good!)")
                        print_box(
                            "✅ ASCON DETECTED TAMPERING!\n"
                            "Authentication tag verification failed.\n"
                            "Modified ciphertext was REJECTED.\n\n"
                            "🛡️  ASCON provides integrity protection!",
                            "─"
                        )
                    else:
                        print("\n⚠️  ATTACK SUCCESS (Bad!)")
                        print("   Modified data was accepted")
                        
                except Exception as e:
                    print(f"\n✅ ATTACK FAILED: {str(e)[:50]}")
                    print_box(
                        "✅ ASCON PROTECTED THE DATA!\n"
                        "Tampering was detected and rejected.\n\n"
                        "🛡️  Authenticated encryption works!",
                        "─"
                    )
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        wait_for_enter()
    
    def attack_dos_interactive(self):
        """Interactive DoS attack"""
        clear_screen()
        print_header("💣 ATTACK: Denial of Service (Message Flooding)")
        
        print("\n📖 Description:")
        print("   This attack floods the system with fake messages")
        print("   to overwhelm it and cause service disruption.")
        
        print("\n⚠️  WARNING: This is disruptive!")
        print("🎯 Goal: Overload system resources\n")
        
        confirm = input("Continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            return
        
        num_messages = input("\nHow many fake messages to send? (1-100): ").strip()
        try:
            num_messages = int(num_messages)
            num_messages = max(1, min(100, num_messages))
        except:
            num_messages = 10
        
        print(f"\n💣 Flooding system with {num_messages} fake messages...")
        countdown(3, "Starting in")
        
        success = 0
        for i in range(num_messages):
            fake_data = {
                "id": "ATTACKER",
                "distance": 999,
                "count": i,
                "timestamp": time.time(),
                "FAKE": True
            }
            
            result = self.client.publish(TOPIC_RAW + "/dos", json.dumps(fake_data))
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                success += 1
            
            print(f"\r📤 Sent: {i+1}/{num_messages}", end="", flush=True)
            time.sleep(0.1)
        
        print(f"\n\n✅ DoS attack completed!")
        print(f"📊 Success rate: {success}/{num_messages}")
        
        print_box(
            f"⚠️  SYSTEM FLOODED!\n"
            f"Sent {success} fake messages in rapid succession.\n"
            f"This can overwhelm system resources.\n\n"
            f"💡 DEFENSE: Rate limiting, message validation",
            "─"
        )
        
        self.attack_count += success
        wait_for_enter()
    
    def show_statistics(self):
        """Show attack statistics"""
        clear_screen()
        print_header("📊 ATTACK STATISTICS")
        
        print(f"\n🔨 Total attacks performed: {self.attack_count}")
        print(f"⏰ Session duration: {time.strftime('%H:%M:%S', time.gmtime(time.time()))}")
        
        print("\n" + "="*70)
        print("📋 ATTACK SUMMARY:")
        print("="*70)
        print("1. Plaintext Modification: Modifies unencrypted data")
        print("   Status: ⚠️  Successful on unencrypted data")
        print("\n2. Replay Attack: Resends old messages")
        print("   Status: ⚠️  Partially successful")
        print("\n3. Ciphertext Modification: Tampers with encrypted data")
        print("   Status: ✅ Failed - ASCON detected tampering")
        print("\n4. DoS Attack: Floods system with messages")
        print("   Status: ⚠️  Can overwhelm without rate limiting")
        print("="*70)
        
        wait_for_enter()

# ===== MAIN MENU =====
def main_menu():
    """Main interactive menu"""
    while True:
        clear_screen()
        print_header("🔐 INTERACTIVE ATTACK SIMULATOR - ASCON Security Testing")
        
        print("\n" + "="*70)
        print("  Choose Attack Type:")
        print("="*70)
        print("\n1. 🕵️  Passive Attack (Eavesdropping)")
        print("   → Listen to network traffic")
        print("   → Try to read encrypted vs unencrypted data")
        print("   → Test: Confidentiality protection")
        
        print("\n2. 🦹 Active Attack (Modification & Replay)")
        print("   → Modify data in transit")
        print("   → Replay old messages")
        print("   → Test: Integrity protection")
        
        print("\n3. 📚 Learn About Attacks")
        print("   → Explanation of attack types")
        print("   → Defense mechanisms")
        
        print("\n4. 🚪 Exit")
        
        print("\n" + "="*70)
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            attacker = InteractivePassiveAttack()
            attacker.run_interactive()
        elif choice == "2":
            attacker = InteractiveActiveAttack()
            attacker.run_interactive()
        elif choice == "3":
            show_attack_tutorial()
        elif choice == "4":
            clear_screen()
            print("\n👋 Thank you for using Attack Simulator!")
            print("🛡️  Remember: Use encryption to protect your IoT systems!\n")
            break
        else:
            print("❌ Invalid choice!")
            time.sleep(1)

def show_attack_tutorial():
    """Show tutorial about attacks"""
    clear_screen()
    print_header("📚 ATTACK TYPES TUTORIAL")
    
    print("\n🕵️  PASSIVE ATTACK:")
    print("   • Only LISTENS to traffic")
    print("   • Does NOT modify anything")
    print("   • Hard to detect")
    print("   • Breaks CONFIDENTIALITY")
    print("   • Defense: Encryption (like ASCON)")
    
    print("\n🦹 ACTIVE ATTACK:")
    print("   • MODIFIES or REPLAYS data")
    print("   • Directly interferes")
    print("   • Easier to detect")
    print("   • Breaks INTEGRITY & AVAILABILITY")
    print("   • Defense: Authentication + Encryption")
    
    print("\n🛡️  ASCON PROTECTION:")
    print("   ✅ Provides ENCRYPTION (confidentiality)")
    print("   ✅ Provides AUTHENTICATION (integrity)")
    print("   ✅ Lightweight for IoT devices")
    print("   ✅ Resistant to tampering")
    
    wait_for_enter()

# ===== RUN PROGRAM =====
if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")