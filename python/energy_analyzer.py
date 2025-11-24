#!/usr/bin/env python3
"""
Energy Consumption Analyzer
Menerima data energi dari ESP32 via MQTT dan membuat analisis
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import matplotlib.pyplot as plt
from collections import deque

# ===== KONFIGURASI =====
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_ENERGY = "iot/sensor/energy"
CLIENT_ID = "Energy_Analyzer"

# ===== DATA STORAGE =====
energy_data = {
    'cycles': deque(maxlen=100),
    'sensor_time': deque(maxlen=100),
    'mqtt_time': deque(maxlen=100),
    'total_energy': deque(maxlen=100),
    'cumulative_energy': deque(maxlen=100),
    'avg_power': deque(maxlen=100),
    'timestamps': deque(maxlen=100)
}

stats = {
    'total_cycles': 0,
    'total_energy_mj': 0,
    'start_time': time.time()
}

# ===== CALLBACKS =====
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        print(f"📡 Subscribing to: {TOPIC_ENERGY}")
        client.subscribe(TOPIC_ENERGY)
    else:
        print(f"❌ Failed to connect, code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        
        # Extract data
        cycle = data.get('cycle', 0)
        sensor_time = data.get('sensor_time_us', 0)
        mqtt_time = data.get('mqtt_time_us', 0)
        total_energy = data.get('total_energy_mj', 0)
        cumulative_energy = data.get('cumulative_energy_mj', 0)
        avg_power = data.get('avg_power_mw', 0)
        
        # Store data
        energy_data['cycles'].append(cycle)
        energy_data['sensor_time'].append(sensor_time)
        energy_data['mqtt_time'].append(mqtt_time)
        energy_data['total_energy'].append(total_energy)
        energy_data['cumulative_energy'].append(cumulative_energy)
        energy_data['avg_power'].append(avg_power)
        energy_data['timestamps'].append(time.time())
        
        # Update stats
        stats['total_cycles'] = cycle
        stats['total_energy_mj'] = cumulative_energy
        
        # Print real-time
        print(f"\n{'='*70}")
        print(f"📊 Cycle #{cycle}")
        print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"⏱️  Sensor read time: {sensor_time} μs")
        print(f"⏱️  MQTT publish time: {mqtt_time} μs")
        print(f"⚡ Cycle energy: {total_energy:.3f} mJ")
        print(f"⚡ Cumulative energy: {cumulative_energy:.3f} mJ = {cumulative_energy/1000:.6f} J")
        print(f"💡 Average power: {avg_power:.2f} mW")
        
        # Show stats every 10 cycles
        if cycle % 10 == 0:
            print_statistics()
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")

# ===== STATISTICS =====
def print_statistics():
    runtime = time.time() - stats['start_time']
    
    print(f"\n{'='*70}")
    print("📊 ENERGY CONSUMPTION STATISTICS")
    print(f"{'='*70}")
    print(f"⏱️  Runtime: {runtime:.2f} seconds")
    print(f"🔄 Total cycles: {stats['total_cycles']}")
    print(f"⚡ Total energy consumed: {stats['total_energy_mj']:.3f} mJ")
    print(f"⚡ Total energy (Joules): {stats['total_energy_mj']/1000:.6f} J")
    print(f"⚡ Total energy (Wh): {stats['total_energy_mj']/3600000:.9f} Wh")
    
    if runtime > 0:
        avg_power = (stats['total_energy_mj'] / 1000) / runtime  # Watts
        print(f"💡 Average power consumption: {avg_power*1000:.2f} mW")
    
    if stats['total_cycles'] > 0:
        energy_per_cycle = stats['total_energy_mj'] / stats['total_cycles']
        print(f"⚡ Average energy per cycle: {energy_per_cycle:.3f} mJ")
    
    print(f"{'='*70}")

def generate_plots():
    """Generate energy consumption plots"""
    if len(energy_data['cycles']) < 2:
        print("⚠️  Not enough data for plotting")
        return
    
    print("\n📈 Generating plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('ESP32 Energy Consumption Analysis', fontsize=16)
    
    cycles = list(energy_data['cycles'])
    
    # Plot 1: Energy per cycle
    axes[0, 0].plot(cycles, list(energy_data['total_energy']), 'b-', linewidth=2)
    axes[0, 0].set_xlabel('Cycle')
    axes[0, 0].set_ylabel('Energy (mJ)')
    axes[0, 0].set_title('Energy Consumption per Cycle')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Cumulative energy
    axes[0, 1].plot(cycles, list(energy_data['cumulative_energy']), 'g-', linewidth=2)
    axes[0, 1].set_xlabel('Cycle')
    axes[0, 1].set_ylabel('Cumulative Energy (mJ)')
    axes[0, 1].set_title('Cumulative Energy Consumption')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Average power
    axes[1, 0].plot(cycles, list(energy_data['avg_power']), 'r-', linewidth=2)
    axes[1, 0].set_xlabel('Cycle')
    axes[1, 0].set_ylabel('Power (mW)')
    axes[1, 0].set_title('Average Power Consumption')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Time breakdown
    axes[1, 1].plot(cycles, list(energy_data['sensor_time']), 'b-', label='Sensor Read', linewidth=2)
    axes[1, 1].plot(cycles, list(energy_data['mqtt_time']), 'r-', label='MQTT Publish', linewidth=2)
    axes[1, 1].set_xlabel('Cycle')
    axes[1, 1].set_ylabel('Time (μs)')
    axes[1, 1].set_title('Execution Time Breakdown')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"energy_analysis_{timestamp}.png"
    plt.savefig(filename, dpi=300)
    print(f"✅ Plot saved as: {filename}")
    
    plt.show()

def save_report():
    """Save energy report to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"energy_report_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("="*70 + "\n")
        f.write("ESP32 ENERGY CONSUMPTION REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        runtime = time.time() - stats['start_time']
        f.write(f"Runtime: {runtime:.2f} seconds\n")
        f.write(f"Total Cycles: {stats['total_cycles']}\n\n")
        
        f.write(f"TOTAL ENERGY CONSUMPTION:\n")
        f.write(f"  {stats['total_energy_mj']:.3f} mJ\n")
        f.write(f"  {stats['total_energy_mj']/1000:.6f} J\n")
        f.write(f"  {stats['total_energy_mj']/3600000:.9f} Wh\n\n")
        
        if runtime > 0:
            avg_power = (stats['total_energy_mj'] / 1000) / runtime
            f.write(f"AVERAGE POWER: {avg_power*1000:.2f} mW\n\n")
        
        if stats['total_cycles'] > 0:
            energy_per_cycle = stats['total_energy_mj'] / stats['total_cycles']
            f.write(f"ENERGY PER CYCLE: {energy_per_cycle:.3f} mJ\n\n")
        
        # Detailed cycle data
        f.write("\nDETAILED CYCLE DATA:\n")
        f.write("-"*70 + "\n")
        f.write("Cycle | Sensor(μs) | MQTT(μs) | Energy(mJ) | Power(mW)\n")
        f.write("-"*70 + "\n")
        
        for i in range(min(len(energy_data['cycles']), 50)):  # First 50 cycles
            f.write(f"{energy_data['cycles'][i]:5d} | "
                   f"{energy_data['sensor_time'][i]:10d} | "
                   f"{energy_data['mqtt_time'][i]:8d} | "
                   f"{energy_data['total_energy'][i]:10.3f} | "
                   f"{energy_data['avg_power'][i]:8.2f}\n")
        
        f.write("\n" + "="*70 + "\n")
    
    print(f"\n✅ Report saved as: {filename}")

# ===== MAIN =====
def main():
    print("="*70)
    print("⚡ ESP32 ENERGY CONSUMPTION ANALYZER")
    print("="*70)
    print(f"📡 Broker: {BROKER}:{PORT}")
    print(f"📥 Topic: {TOPIC_ENERGY}")
    print("="*70)
    
    client = mqtt.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        print("\n🔌 Connecting to broker...")
        client.connect(BROKER, PORT, 60)
        
        print("✅ Starting analysis...")
        print("⌨️  Press Ctrl+C to stop and generate report\n")
        
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping analyzer...")
        print_statistics()
        
        # Generate report
        save_report()
        
        # Ask if user wants plots
        try:
            choice = input("\n📈 Generate plots? (y/n): ").strip().lower()
            if choice == 'y':
                generate_plots()
        except:
            pass
        
        client.disconnect()
        print("\n👋 Goodbye!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()