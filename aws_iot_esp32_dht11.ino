#include "secrets.h"
#include <WiFiClientSecure.h>
#include <MQTTClient.h>
#include <ArduinoJson.h>
#include "WiFi.h"
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

#define AWS_IOT_PUBLISH_TOPIC   "enduvia/sensors"
#define AWS_IOT_SUBSCRIBE_TOPIC "enduvia/komut"

WiFiClientSecure net = WiFiClientSecure();
MQTTClient client = MQTTClient(256);

void messageHandler(String &topic, String &payload) {
  Serial.println("Buluttan gelen mesaj: " + topic + " - " + payload);
}

void connectAWS() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println("Wi-Fi baglantisi kuruluyor...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi baglantisi basarili!");

  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);

  client.begin(AWS_IOT_ENDPOINT, 8883, net);
  client.onMessage(messageHandler);

  Serial.println("AWS IoT Core baglantisi kuruluyor...");
  while (!client.connect(THINGNAME)) {
    Serial.print(".");
    delay(500);
  }

  if (!client.connected()) {
    Serial.println("\nAWS baglantisi basarisiz!");
    return;
  }

  client.subscribe(AWS_IOT_SUBSCRIBE_TOPIC);
  Serial.println("\nAWS IoT Core baglantisi tamamlandi!");
}

void publishMessage() {
  float nem = dht.readHumidity();
  float sicaklik = dht.readTemperature();

  if (isnan(nem) || isnan(sicaklik)) {
    Serial.println("Sensorden veri okunamadi! Baglantilari kontrol et.");
    return;
  }

  String durum = "Normal";
  if (sicaklik >= 30.0) {
    durum = "Uyari";
  }

  StaticJsonDocument<200> doc;
  doc["cihaz"] = THINGNAME;
  doc["sicaklik"] = sicaklik;
  doc["nem"] = nem;
  doc["durum"] = durum;

  char jsonBuffer[512];
  serializeJson(doc, jsonBuffer);

  client.publish(AWS_IOT_PUBLISH_TOPIC, jsonBuffer);

  Serial.print("AWS'ye Gonderildi -> ");
  Serial.println(jsonBuffer);
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  connectAWS();
}

void loop() {
  client.loop();

  if (!client.connected()) {
    connectAWS();
  }

  publishMessage();
  delay(5000);
}
