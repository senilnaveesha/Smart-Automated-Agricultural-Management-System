#include <WiFi.h>
#include <HTTPClient.h>

// --------------------
// Wi-Fi settings
// --------------------
const char* WIFI_SSID = "SLT-LTE-WiFi-EEEC";
const char* WIFI_PASS = "E41NDL7LJ38";

// Change laptop IP here:
const char* LAPTOP_URL = "http://192.168.1.111:8000/api/v1/nodes/node01/sensors";

// --------------------
// Pins (ESP32 ADC1 pins recommended when using Wi-Fi)
// --------------------
#define SOIL1_PIN 34
#define SOIL2_PIN 35
#define RAIN_DO_PIN 26

// Optional: relay pin (if you have it connected)
#define RELAY_PIN 25  // change if needed

// --------------------
// Helpers
// --------------------
String boolToJson(bool v) {
  return v ? "true" : "false";
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  Serial.print("Connecting to WiFi");
  unsigned long start = millis();

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - start > 20000) { // 20s timeout
      Serial.println("\nWiFi connect timeout. Restarting...");
      ESP.restart();
    }
  }

  Serial.println("\nWiFi connected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

bool postToLaptop(int soil1_raw, int soil2_raw, bool rain, bool pump_on) {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  http.begin(LAPTOP_URL);
  http.addHeader("Content-Type", "application/json");

  // Use millis-based timestamp for prototype
  unsigned long ts = millis() / 1000;

  String json = "{";
  json += "\"soil1_raw\":" + String(soil1_raw) + ",";
  json += "\"soil2_raw\":" + String(soil2_raw) + ",";
  json += "\"rain\":" + boolToJson(rain) + ",";
  json += "\"pump_on\":" + boolToJson(pump_on) + ",";
  json += "\"ts\":" + String(ts);
  json += "}";

  int code = http.POST(json);
  String resp = http.getString();
  http.end();

  Serial.print("POST code: ");
  Serial.print(code);
  Serial.print(" | resp: ");
  Serial.println(resp);

  return (code >= 200 && code < 300);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // ADC 12-bit: 0-4095
  analogReadResolution(12);

  pinMode(RAIN_DO_PIN, INPUT);

  // Relay optional
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW); // default OFF (depends on relay type)

  Serial.println("=== ESP32 Sensor Sender Start ===");

  connectWiFi();
}

void loop() {
  // Read sensors
  int soil1_raw = analogRead(SOIL1_PIN);
  int soil2_raw = analogRead(SOIL2_PIN);

  // Rain module DO might be inverted on some boards:
  // If your module outputs LOW when raining, then:
  // bool rain = (digitalRead(RAIN_DO_PIN) == LOW);
  bool rain = (digitalRead(RAIN_DO_PIN) == HIGH);

  // For prototype: pump state just mirrors relay pin output
  bool pump_on = (digitalRead(RELAY_PIN) == HIGH);

  // Print local debug
  Serial.println("------------------------");
  Serial.print("Soil1 RAW: "); Serial.println(soil1_raw);
  Serial.print("Soil2 RAW: "); Serial.println(soil2_raw);
  Serial.print("Rain: "); Serial.println(rain ? "YES" : "NO");
  Serial.print("Pump: "); Serial.println(pump_on ? "ON" : "OFF");

  // Send to laptop
  bool ok = postToLaptop(soil1_raw, soil2_raw, rain, pump_on);
  if (!ok) {
    Serial.println("⚠ Failed to send to laptop (will retry).");
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected, reconnecting...");
      connectWiFi();
    }
  }

  delay(1000);
}
