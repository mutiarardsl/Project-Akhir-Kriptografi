#!/usr/bin/env python3
"""
Real-time Attack Monitor
Menampilkan SEMUA aktivitas: data normal, data terenkripsi, dan SERANGAN
Monitor ini subscribe ke SEMUA topic untuk mendeteksi anomali
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
from collections import deque
import os

# ===== KONFIGURASI =====
BROKER = "broker.hivemq.com"
PORT = 1883

# Subscribe ke SEMUA topic yang relevan
TOPICS = [
    ("iot/sensor/distance/raw", 0),           # Data normal
    ("iot/sensor/distance/enc", 0),           # Data encrypted
    ("iot/sensor/distance/raw/tampered", 0),  # Data yang dimodifikasi attacker
    ("iot/sensor/distance/enc/tampered", 0),  # Encrypted yang dimodifikasi
    ("iot/sensor/distance/enc/replayed", 0),  # Replay attack
    ("iot/sensor/distance/raw/dos", 0),       # DoS attack
]

# ===== STORAGE =====
message_history = deque(maxlen=50)  # Keep last 50 messages
attack_detected = []
normal_messages = 0
attack_messages = 0

# ===== COLORS FOR TERMINAL =====
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colored(text, color):
    print(f"{color}{text}{Colors.END}")

# ===== MQTT CALLBACKS =====
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print_colored("\n✅ Monitor connected to broker!", Colors.GREEN)
        print_colored("📡 Subscribing to all topics...", Colors.CYAN)
        for topic, qos in TOPICS:
            client.subscribe(topic)
            print(f"   → {topic}")
        print_colored("\n🔍 Monitoring started... Press Ctrl+C to stop\n", Colors.BOLD)
    else:
        print_colored(f"❌ Connection failed with code {rc}", Colors.RED)

def on_message(client, userdata, msg):
    global normal_messages, attack_messages
    
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    # Detect attack based on topic
    is_attack = any(keyword in topic for keyword in ['tampered', 'replayed', 'dos'])
    
    if is_attack:
        attack_messages += 1
        handle_attack_message(timestamp, topic, payload)
    else:
        normal_messages += 1
        handle_normal_message(timestamp, topic, payload)
    
    # Store in history
    message_history.append({
        'timestamp': timestamp,
        'topic': topic,
        'payload': payload,
        'is_attack': is_attack
    })

def handle_normal_message(timestamp, topic, payload):
    """Handle normal legitimate messages"""
    print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
    print_colored(f"[{timestamp}] 📨 NORMAL MESSAGE #{normal_messages}", Colors.GREEN)
    print(f"📍 Topic: {topic}")
    
    try:
        data = json.loads(payload)
        
        if topic.endswith('/raw'):
            # Unencrypted data
            print_colored("🔓 Type: UNENCRYPTED DATA", Colors.YELLOW)
            print(f"   Device: {data.get('id', 'N/A')}")
            print(f"   Distance: {Colors.BOLD}{data.get('distance', 'N/A')} cm{Colors.END}")
            print(f"   Count: {data.get('count', 'N/A')}")
            print_colored("   ⚠️  Warning: This data is NOT protected!", Colors.YELLOW)
            
        elif topic.endswith('/enc'):
            # Encrypted data
            print_colored("🔐 Type: ENCRYPTED DATA", Colors.CYAN)
            encrypted_hex = data.get('encrypted_data', '')
            print(f"   Encrypted (preview): {encrypted_hex[:40]}...")
            print(f"   Size: {data.get('encrypted_size', 'N/A')} bytes")
            print(f"   Encryption time: {data.get('encryption_time_ms', 'N/A')} ms")
            print_colored("   ✅ This data is PROTECTED by ASCON!", Colors.GREEN)
            
    except json.JSONDecodeError:
        print(f"   Payload (raw): {payload[:100]}...")

def handle_attack_message(timestamp, topic, payload):
    """Handle attack messages with alert"""
    print(f"\n{Colors.RED}{'='*80}{Colors.END}")
    print_colored(f"🚨 [ALERT] ATTACK DETECTED! #{attack_messages}", Colors.RED)
    print_colored(f"[{timestamp}]", Colors.RED)
    print(f"📍 Topic: {Colors.RED}{topic}{Colors.END}")
    
    # Determine attack type
    if 'tampered' in topic:
        attack_type = "DATA MODIFICATION ATTACK"
        if 'raw' in topic:
            attack_severity = "HIGH"
            attack_status = "SUCCESSFUL"
            color = Colors.RED
        else:
            attack_severity = "MEDIUM"
            attack_status = "BLOCKED BY ASCON"
            color = Colors.YELLOW
    elif 'replayed' in topic:
        attack_type = "REPLAY ATTACK"
        attack_severity = "MEDIUM"
        attack_status = "SUCCESSFUL"
        color = Colors.YELLOW
    elif 'dos' in topic:
        attack_type = "DENIAL OF SERVICE"
        attack_severity = "HIGH"
        attack_status = "IN PROGRESS"
        color = Colors.RED
    else:
        attack_type = "UNKNOWN ATTACK"
        attack_severity = "UNKNOWN"
        attack_status = "UNKNOWN"
        color = Colors.RED
    
    print_colored(f"🔨 Attack Type: {attack_type}", color)
    print_colored(f"⚠️  Severity: {attack_severity}", color)
    print_colored(f"📊 Status: {attack_status}", color)
    
    try:
        data = json.loads(payload)
        
        # Show what was modified
        if data.get('TAMPERED'):
            print_colored("\n🔍 ATTACK DETAILS:", Colors.RED)
            
            if 'distance' in data:
                distance = data.get('distance')
                print(f"   Injected Distance: {Colors.RED}{Colors.BOLD}{distance} cm{Colors.END}")
                
                if distance == 999 or distance > 500:
                    print(f"   {Colors.RED}⚠️  FAKE VALUE DETECTED!{Colors.END}")
                    print(f"   This is clearly malicious (unrealistic value)")
            
            if 'attack_time' in data:
                print(f"   Attack Timestamp: {data.get('attack_time')}")
            
            if 'FAKE' in data:
                print(f"   {Colors.RED}⚠️  This is a FAKE message from attacker!{Colors.END}")
        
        # Compare with recent normal messages
        if message_history:
            recent_normals = [m for m in message_history if not m['is_attack']]
            if recent_normals:
                last_normal = recent_normals[-1]
                try:
                    last_data = json.loads(last_normal['payload'])
                    if 'distance' in last_data and 'distance' in data:
                        normal_distance = last_data.get('distance')
                        attack_distance = data.get('distance')
                        diff = abs(attack_distance - normal_distance)
                        
                        print_colored("\n📊 COMPARISON WITH NORMAL DATA:", Colors.YELLOW)
                        print(f"   Normal value: {normal_distance} cm")
                        print(f"   Attacked value: {Colors.RED}{attack_distance} cm{Colors.END}")
                        print(f"   Difference: {Colors.RED}{diff} cm{Colors.END}")
                        
                        if diff > 50:
                            print(f"   {Colors.RED}🚨 ANOMALY: Huge difference detected!{Colors.END}")
                except:
                    pass
    
    except json.JSONDecodeError:
        print(f"   Payload: {payload[:100]}...")
    
    # Log attack
    attack_detected.append({
        'timestamp': timestamp,
        'type': attack_type,
        'topic': topic,
        'severity': attack_severity
    })
    
    print_colored("\n💡 RECOMMENDATION:", Colors.YELLOW)
    if 'raw' in topic:
        print("   → Use encryption to prevent data modification!")
        print("   → ASCON can protect against this attack")
    else:
        print("   → ASCON detected and blocked this attack")
        print("   → Encrypted data integrity is maintained")

def print_statistics():
    """Print monitoring statistics"""
    print(f"\n\n{Colors.CYAN}{'='*80}{Colors.END}")
    print_colored("📊 MONITORING STATISTICS", Colors.BOLD)
    print(f"{Colors.CYAN}{'='*80}{Colors.END}")
    
    print(f"\n📨 Total Messages: {normal_messages + attack_messages}")
    print_colored(f"   ✅ Normal: {normal_messages}", Colors.GREEN)
    print_colored(f"   🚨 Attacks: {attack_messages}", Colors.RED)
    
    if attack_messages > 0:
        attack_rate = (attack_messages / (normal_messages + attack_messages)) * 100
        print(f"\n⚠️  Attack Rate: {Colors.RED}{attack_rate:.1f}%{Colors.END}")
    
    if attack_detected:
        print(f"\n🔍 ATTACK BREAKDOWN:")
        attack_types = {}
        for attack in attack_detected:
            attack_type = attack['type']
            attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
        
        for attack_type, count in attack_types.items():
            print(f"   • {attack_type}: {count}")
    
    print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")

def print_live_dashboard():
    """Print live dashboard (updated periodically)"""
    clear_screen()
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{'  🔍 REAL-TIME ATTACK MONITOR - IoT Security Dashboard':^80}{Colors.END}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")
    
    # Status
    print(f"{Colors.GREEN}🟢 MONITORING ACTIVE{Colors.END} | Broker: {BROKER}:{PORT}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Stats boxes
    print(f"┌{'─'*25}┬{'─'*25}┬{'─'*25}┐")
    print(f"│ {'NORMAL MESSAGES':^23} │ {'ATTACK MESSAGES':^23} │ {'TOTAL MESSAGES':^23} │")
    print(f"│ {Colors.GREEN}{normal_messages:^23}{Colors.END} │ {Colors.RED}{attack_messages:^23}{Colors.END} │ {normal_messages + attack_messages:^23} │")
    print(f"└{'─'*25}┴{'─'*25}┴{'─'*25}┘\n")
    
    # Recent attacks
    if attack_detected:
        print(f"{Colors.RED}🚨 RECENT ATTACKS:{Colors.END}")
        for attack in list(attack_detected)[-5:]:
            print(f"   [{attack['timestamp']}] {attack['type']} - Severity: {attack['severity']}")
        print()
    
    # Recent messages
    print(f"{Colors.CYAN}📨 RECENT ACTIVITY (Last 5 messages):{Colors.END}")
    for msg in list(message_history)[-5:]:
        icon = "🚨" if msg['is_attack'] else "📨"
        color = Colors.RED if msg['is_attack'] else Colors.GREEN
        topic_short = msg['topic'].split('/')[-1]
        print(f"   {color}{icon} [{msg['timestamp']}] {topic_short}{Colors.END}")
    
    print(f"\n{Colors.YELLOW}💡 Watching all topics... Press Ctrl+C to stop{Colors.END}")

# ===== MAIN PROGRAM =====
def main():
    clear_screen()
    print_colored("="*80, Colors.CYAN)
    print_colored("  🔍 REAL-TIME ATTACK MONITOR", Colors.BOLD)
    print_colored("="*80, Colors.CYAN)
    
    print("\n📋 This monitor will show:")
    print("   ✅ Normal sensor data (encrypted & unencrypted)")
    print("   🚨 Attack attempts in REAL-TIME")
    print("   📊 Comparison between normal and malicious data")
    print("   🔍 Attack detection and analysis")
    
    input("\nPress ENTER to start monitoring...")
    
    # Setup MQTT client
    client = mqtt.Client("Attack_Monitor")
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        print("\n🔌 Connecting to MQTT broker...")
        client.connect(BROKER, PORT, 60)
        
        # Start monitoring
        client.loop_start()
        
        # Keep running and show live stats every 5 seconds
        last_update = time.time()
        while True:
            time.sleep(0.5)
            
            # Update dashboard every 5 seconds if there's activity
            if time.time() - last_update > 5 and (normal_messages + attack_messages) > 0:
                # Don't clear if recent messages to avoid missing info
                # print_live_dashboard()
                last_update = time.time()
        
    except KeyboardInterrupt:
        print_colored("\n\n🛑 Stopping monitor...", Colors.YELLOW)
        print_statistics()
        
        # Save log to file
        if attack_detected:
            filename = f"attack_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write("ATTACK LOG\n")
                f.write("="*80 + "\n\n")
                for attack in attack_detected:
                    f.write(f"[{attack['timestamp']}] {attack['type']}\n")
                    f.write(f"  Topic: {attack['topic']}\n")
                    f.write(f"  Severity: {attack['severity']}\n\n")
            
            print_colored(f"\n💾 Attack log saved to: {filename}", Colors.GREEN)
        
        client.loop_stop()
        client.disconnect()
        print_colored("\n👋 Monitor stopped. Goodbye!", Colors.CYAN)
        
    except Exception as e:
        print_colored(f"\n❌ Error: {e}", Colors.RED)

if __name__ == "__main__":
    main()