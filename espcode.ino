#include <WiFi.h>
#include <WebServer.h>

// Replace with your Wi-Fi credentials
const char* ssid = "Hannan";
const char* password = "ayaan@shan";

// Hardware pins
const int moisturePin = 34; // ADC1_6 — analog input
const int pumpPin = 26;    

// Web server runs on port 80
WebServer server(80);

// Handle GET /moisture — returns raw ADC value
void handleMoisture() {
  int raw = analogRead(moisturePin);

  // Debug print
  Serial.print("Raw ADC Value: ");
  Serial.println(raw);

  String json = "{\"raw\": " + String(raw) + "}";
  server.send(200, "application/json", json);
}

// Handle POST /start_pump
void handleStartPump() {
  digitalWrite(pumpPin, HIGH); // Turn pump ON
  delay(5000);                 // Run for 5 seconds (adjust as needed)
  digitalWrite(pumpPin, LOW);  // Turn pump OFF
  server.send(200, "text/plain", "Pump started");
}

void setup() {
  Serial.begin(115200);

  pinMode(pumpPin, OUTPUT);
  digitalWrite(pumpPin, LOW); // Ensure pump is OFF

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  server.on("/moisture", HTTP_GET, handleMoisture);
  server.on("/start_pump", HTTP_POST, handleStartPump);

  server.begin();
  Serial.println("Server started");
}

void loop() {
  server.handleClient();
}