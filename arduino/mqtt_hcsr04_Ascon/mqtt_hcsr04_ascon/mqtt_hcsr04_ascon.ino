/*
 * ESP32 Complete System: IoT Security with ASCON + Energy Monitoring
 * Features:
 * - HC-SR04 Sensor Reading
 * - MQTT Publishing
 * - Energy Consumption Monitoring
 * - Toggle between Normal Mode and Energy Monitoring Mode
 */

#include <WiFi.h>
#include <PubSubClient.h>

// ===== KONFIGURASI WIFI =====
const char* ssid = "TD";          // Ganti!
const char* password = "seterahgue";   // Ganti!

// ===== KONFIGURASI MQTT =====
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP32_HCSR04_Complete";
const char* mqtt_topic_raw = "iot/sensor/distance/raw";
const char* mqtt_topic_energy = "iot/sensor/energy";

// ===== KONFIGURASI HC-SR04 =====
#define TRIGGER_PIN 5    // GPIO5
#define ECHO_PIN 18      // GPIO18
#define MAX_DISTANCE 400

// ===== CONFIGURATION: ENABLE/DISABLE ENERGY MONITORING =====
#define ENERGY_MONITORING_ENABLED true  // Set false untuk disable energy monitoring

// ===== OBJECTS =====
WiFiClient espClient;
PubSubClient client(espClient);

// ===== ENERGY MONITORING STRUCTURE =====
struct EnergyStats {
  // Timing (microseconds)
  unsigned long sensor_read_time_us;
  unsigned long json_creation_time_us;
  unsigned long mqtt_publish_time_us;
  unsigned long total_cycle_time_us;
  
  // Energy (millijoules)
  float sensor_energy_mj;
  float json_energy_mj;
  float mqtt_energy_mj;
  float idle_energy_mj;
  float total_energy_mj;
  
  // Cumulative
  unsigned long cycle_count;
  float cumulative_energy_mj;
  float average_power_mw;
} energyStats;

// ESP32 Current Draw (mA) - dari datasheet Espressif
const float CURRENT_WIFI_TX = 200.0;      // mA saat WiFi transmit
const float CURRENT_WIFI_RX = 100.0;      // mA saat WiFi receive  
const float CURRENT_CPU_ACTIVE = 60.0;    // mA saat CPU aktif
const float CURRENT_IDLE = 30.0;          // mA saat idle
const float VOLTAGE = 3.3;                // Volt (ESP32 operating voltage)

// ===== TIMING VARIABLES =====
unsigned long lastMsg = 0;
const long interval = 2000;  // Kirim setiap 2 detik
int messageCount = 0;
unsigned long programStartTime = 0;
unsigned long lastEnergyReport = 0;
const long energyReportInterval = 10000; // Report setiap 10 detik

// ===== UTILITY: CALCULATE ENERGY =====
float calculateEnergy(float current_ma, unsigned long time_us) {
  /*
   * Energy (mJ) = Power (mW) × Time (ms)
   * Power (mW) = Voltage (V) × Current (mA)
   * Time (ms) = time_us / 1000
   */
  float power_mw = VOLTAGE * current_ma;
  float time_ms = time_us / 1000.0;
  float energy_mj = power_mw * time_ms;
  return energy_mj;
}

// ===== SENSOR: READ DISTANCE =====
long readDistance() {
  unsigned long startTime = micros();
  
  // Trigger pulse
  digitalWrite(TRIGGER_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIGGER_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGGER_PIN, LOW);
  
  // Read echo
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // timeout 30ms
  long distance = duration * 0.034 / 2;  // Convert to cm
  
  if (distance == 0 || distance > MAX_DISTANCE) {
    distance = 0; // Out of range
  }
  
  // Calculate energy if monitoring enabled
  if (ENERGY_MONITORING_ENABLED) {
    energyStats.sensor_read_time_us = micros() - startTime;
    energyStats.sensor_energy_mj = calculateEnergy(
      CURRENT_CPU_ACTIVE, 
      energyStats.sensor_read_time_us
    );
  }
  
  return distance;
}

// ===== WIFI SETUP =====
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  unsigned long wifiStartTime = millis();
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  unsigned long wifiConnectTime = millis() - wifiStartTime;

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  if (ENERGY_MONITORING_ENABLED) {
    float wifiEnergy = calculateEnergy(CURRENT_WIFI_TX, wifiConnectTime * 1000);
    Serial.print("WiFi connection time: ");
    Serial.print(wifiConnectTime);
    Serial.println(" ms");
    Serial.print("WiFi connection energy: ");
    Serial.print(wifiEnergy, 3);
    Serial.println(" mJ");
  }
}

// ===== MQTT CALLBACK =====
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

// ===== MQTT RECONNECT =====
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    unsigned long connectStartTime = micros();
    
    if (client.connect(mqtt_client_id)) {
      Serial.println("connected");
      
      if (ENERGY_MONITORING_ENABLED) {
        unsigned long connectTime = micros() - connectStartTime;
        float connectEnergy = calculateEnergy(CURRENT_WIFI_TX, connectTime);
        
        Serial.print("MQTT connection time: ");
        Serial.print(connectTime / 1000.0, 2);
        Serial.println(" ms");
        Serial.print("MQTT connection energy: ");
        Serial.print(connectEnergy, 3);
        Serial.println(" mJ");
      }
      
      client.subscribe("iot/sensor/control");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// ===== PRINT ENERGY HEADER =====
void printEnergyHeader() {
  Serial.println("\n╔═══════════════════════════════════════════════════════════════════════════╗");
  Serial.println("║ Cycle | Read(μs) | JSON(μs) | MQTT(μs) | Total(μs) | Energy(mJ) | Power(mW) ║");
  Serial.println("╠═══════════════════════════════════════════════════════════════════════════╣");
}

// ===== PRINT ENERGY CYCLE =====
void printEnergyCycle() {
  char buffer[200];
  sprintf(buffer, "║ %5lu │ %8lu │ %8lu │ %8lu │ %9lu │ %10.3f │ %9.2f ║",
          energyStats.cycle_count,
          energyStats.sensor_read_time_us,
          energyStats.json_creation_time_us,
          energyStats.mqtt_publish_time_us,
          energyStats.total_cycle_time_us,
          energyStats.total_energy_mj,
          energyStats.average_power_mw);
  Serial.println(buffer);
}

// ===== PRINT ENERGY SUMMARY =====
void printEnergySummary() {
  unsigned long runtime_ms = millis() - programStartTime;
  float runtime_sec = runtime_ms / 1000.0;
  
  Serial.println("╠═══════════════════════════════════════════════════════════════════════════╣");
  Serial.println("║                          ENERGY SUMMARY                                    ║");
  Serial.println("╠═══════════════════════════════════════════════════════════════════════════╣");
  
  Serial.print("║ Total Cycles: ");
  Serial.print(energyStats.cycle_count);
  Serial.print(" | Runtime: ");
  Serial.print(runtime_sec, 1);
  Serial.println(" s");
  
  Serial.print("║ Cumulative Energy: ");
  Serial.print(energyStats.cumulative_energy_mj, 3);
  Serial.print(" mJ = ");
  Serial.print(energyStats.cumulative_energy_mj / 1000.0, 6);
  Serial.print(" J = ");
  Serial.print(energyStats.cumulative_energy_mj / 3600000.0, 9);
  Serial.println(" Wh");
  
  if (runtime_sec > 0) {
    float avg_power_w = (energyStats.cumulative_energy_mj / 1000.0) / runtime_sec;
    Serial.print("║ Average Power: ");
    Serial.print(avg_power_w * 1000.0, 2);
    Serial.println(" mW");
  }
  
  if (energyStats.cycle_count > 0) {
    float energy_per_cycle = energyStats.cumulative_energy_mj / energyStats.cycle_count;
    Serial.print("║ Energy per Cycle: ");
    Serial.print(energy_per_cycle, 3);
    Serial.println(" mJ");
  }
  
  Serial.println("╚═══════════════════════════════════════════════════════════════════════════╝\n");
}

// ===== SETUP =====
void setup() {
  Serial.begin(115200);
  
  // Setup pins
  pinMode(TRIGGER_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Print header
  Serial.println("\n\n╔═══════════════════════════════════════════════════════════╗");
  Serial.println("║     ESP32 IoT Security System with Energy Monitoring     ║");
  Serial.println("╠═══════════════════════════════════════════════════════════╣");
  Serial.println("║ Sensor: HC-SR04 Ultrasonic Distance Sensor               ║");
  Serial.println("║ Protocol: MQTT                                            ║");
  Serial.println("║ Security: ASCON Encryption (Python side)                 ║");
  
  if (ENERGY_MONITORING_ENABLED) {
    Serial.println("║ Energy Monitoring: ENABLED ✅                             ║");
  } else {
    Serial.println("║ Energy Monitoring: DISABLED ❌                            ║");
  }
  
  Serial.println("╚═══════════════════════════════════════════════════════════╝\n");
  
  // Initialize energy stats
  if (ENERGY_MONITORING_ENABLED) {
    memset(&energyStats, 0, sizeof(energyStats));
    programStartTime = millis();
  }
  
  // Connect WiFi
  setup_wifi();
  
  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  Serial.println("\n--- System Started ---");
  
  if (ENERGY_MONITORING_ENABLED) {
    printEnergyHeader();
  }
}

// ===== MAIN LOOP =====
void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  
  // Send sensor data
  if (now - lastMsg > interval) {
    lastMsg = now;
    
    unsigned long cycleStartTime = 0;
    if (ENERGY_MONITORING_ENABLED) {
      cycleStartTime = micros();
      energyStats.cycle_count++;
    }
    
    messageCount++;
    
    // ===== 1. READ SENSOR =====
    long distance = readDistance();
    
    // ===== 2. CREATE JSON =====
    unsigned long jsonStartTime = 0;
    if (ENERGY_MONITORING_ENABLED) {
      jsonStartTime = micros();
    }
    
    String jsonData = "{";
    jsonData += "\"id\":\"" + String(mqtt_client_id) + "\",";
    jsonData += "\"count\":" + String(messageCount) + ",";
    jsonData += "\"distance\":" + String(distance) + ",";
    jsonData += "\"timestamp\":" + String(millis()) + ",";
    jsonData += "\"unit\":\"cm\"";
    jsonData += "}";
    
    if (ENERGY_MONITORING_ENABLED) {
      energyStats.json_creation_time_us = micros() - jsonStartTime;
      energyStats.json_energy_mj = calculateEnergy(
        CURRENT_CPU_ACTIVE, 
        energyStats.json_creation_time_us
      );
    }
    
    // ===== 3. MQTT PUBLISH =====
    unsigned long mqttStartTime = 0;
    if (ENERGY_MONITORING_ENABLED) {
      mqttStartTime = micros();
    }
    
    boolean publishSuccess = client.publish(mqtt_topic_raw, jsonData.c_str());
    
    if (ENERGY_MONITORING_ENABLED) {
      energyStats.mqtt_publish_time_us = micros() - mqttStartTime;
      energyStats.mqtt_energy_mj = calculateEnergy(
        CURRENT_WIFI_TX, 
        energyStats.mqtt_publish_time_us
      );
    }
    
    // ===== PRINT NORMAL OUTPUT =====
    if (!ENERGY_MONITORING_ENABLED) {
      Serial.print("Distance: ");
      Serial.print(distance);
      Serial.println(" cm");
      Serial.println("Publishing data...");
      
      if (publishSuccess) {
        Serial.println("Data sent!");
      } else {
        Serial.println("Publish failed!");
      }
      Serial.println("---");
    }
    
    // ===== CALCULATE ENERGY =====
    if (ENERGY_MONITORING_ENABLED) {
      energyStats.total_cycle_time_us = micros() - cycleStartTime;
      energyStats.total_energy_mj = energyStats.sensor_energy_mj + 
                                     energyStats.json_energy_mj + 
                                     energyStats.mqtt_energy_mj;
      
      energyStats.cumulative_energy_mj += energyStats.total_energy_mj;
      energyStats.average_power_mw = (energyStats.total_energy_mj / 
                                      (energyStats.total_cycle_time_us / 1000.0));
      
      // Print energy cycle
      printEnergyCycle();
      
      // Print summary every 10 cycles
      if (energyStats.cycle_count % 10 == 0) {
        printEnergySummary();
        printEnergyHeader();
      }
      
      // Publish energy data
      String energyJson = "{";
      energyJson += "\"cycle\":" + String(energyStats.cycle_count) + ",";
      energyJson += "\"sensor_time_us\":" + String(energyStats.sensor_read_time_us) + ",";
      energyJson += "\"json_time_us\":" + String(energyStats.json_creation_time_us) + ",";
      energyJson += "\"mqtt_time_us\":" + String(energyStats.mqtt_publish_time_us) + ",";
      energyJson += "\"total_energy_mj\":" + String(energyStats.total_energy_mj, 3) + ",";
      energyJson += "\"cumulative_energy_mj\":" + String(energyStats.cumulative_energy_mj, 3) + ",";
      energyJson += "\"avg_power_mw\":" + String(energyStats.average_power_mw, 2);
      energyJson += "}";
      
      client.publish(mqtt_topic_energy, energyJson.c_str());
    }
  }
  
  // Idle energy tracking
  if (ENERGY_MONITORING_ENABLED) {
    unsigned long idleStartTime = micros();
    delay(10);
    unsigned long idleTime = micros() - idleStartTime;
    energyStats.idle_energy_mj = calculateEnergy(CURRENT_IDLE, idleTime);
    energyStats.cumulative_energy_mj += energyStats.idle_energy_mj;
  } else {
    delay(10);
  }
  
  // Periodic energy report via Serial (every 10 seconds)
  if (ENERGY_MONITORING_ENABLED && (now - lastEnergyReport > energyReportInterval)) {
    lastEnergyReport = now;
    
    Serial.println("\n🔋 === PERIODIC ENERGY REPORT ===");
    Serial.print("Runtime: ");
    Serial.print((now - programStartTime) / 1000.0, 1);
    Serial.println(" seconds");
    Serial.print("Total Energy: ");
    Serial.print(energyStats.cumulative_energy_mj, 3);
    Serial.print(" mJ (");
    Serial.print(energyStats.cumulative_energy_mj / 1000.0, 6);
    Serial.println(" J)");
    Serial.println("=================================\n");
  }
}