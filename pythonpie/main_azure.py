import machine
import time
import socket
import network
import hmac
import hashlib
import ubinascii
import ujson
from umqtt.simple import MQTTClient

from secrets import SSID, PASSWORD, HOST_NAME, DEVICE_ID, PRIMARY_KEY


# ---------------- TEMPERATURE FUNCTION ----------------

def get_temp(sensor_temp, conversion_factor):
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    return temperature


# ---------------- WIFI CONNECTION ----------------

def connect_to_wifi():
    print("Connecting to WiFi:", SSID)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    for i in range(25):
        if wlan.isconnected():
            print("Connected:", wlan.ifconfig())
            return True
        print("Waiting for connection...", i)
        time.sleep(1)

    print("FAILED to connect to WiFi.")
    return False


# ---------------- SAS TOKEN CREATION ----------------

def generate_sas_token(uri, key, expiry=3600):
    ttl = int(time.time()) + expiry
    sign_key = ubinascii.a2b_base64(key)
    message = "{}\n{}".format(uri, ttl)
    signature = ubinascii.b2a_base64(
        hmac.new(sign_key, message.encode('utf-8'), hashlib.sha256).digest()
    ).rstrip()

    token = "SharedAccessSignature sr={}&sig={}&se={}".format(
        uri, ubinascii.quote(signature), ttl
    )
    return token


# ---------------- MQTT CONNECTION TO AZURE ----------------

def connect_azure():
    uri = "{}%2Fdevices%2F{}".format(HOST_NAME, DEVICE_ID)
    sas = generate_sas_token(uri, PRIMARY_KEY)

    with open("azure_ca.pem", "rb") as f:
        ca_cert = f.read()

    ssl_params = {"cert": None, "key": None, "cadata": ca_cert}

    client = MQTTClient(
        client_id=DEVICE_ID,
        server=HOST_NAME,
        port=8883,
        user="{}{}{}{}".format(HOST_NAME, "/devices/", DEVICE_ID, "/?api-version=2021-04-12"),
        password=sas,
        ssl=True,
        ssl_params=ssl_params,
        keepalive=60,
    )

    print("Connecting to Azure IoT Hub...")
    client.connect()
    print("Connected to Azure!")

    return client


# ---------------- WEB PAGE ----------------

def send_response(temperature, client):
    response = f"""
        <html>
            <head><title>Pico Temperature</title></head>
            <body>
                <h1>Current Temperature: {temperature:.2f} °C</h1>
            </body>
        </html>
        """
    client.send("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n")
    client.send(response)
    client.close()


# ---------------- SETUP ----------------

sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / 65535
LED = machine.Pin("LED", machine.Pin.OUT)

# Webserver
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
websocket = socket.socket()
websocket.bind(addr)
websocket.listen(1)
print("Web server running on http://", addr)

# Connect WiFi
if not connect_to_wifi():
    raise RuntimeError("Could not connect to WiFi.")

# Connect Azure
mqtt = connect_azure()

topic_pub = b"devices/%s/messages/events/" % DEVICE_ID


# ---------------- MAIN LOOP ----------------

while True:
    temperature = get_temp(sensor_temp, conversion_factor)
    print("Temp:", temperature)

    # LED warning
    LED.value(temperature < 16 or temperature > 22)

    # Publish to Azure
    payload = ujson.dumps({"temperature": temperature})
    mqtt.publish(topic_pub, payload)

    # Web server handling
    try:
        client, addr = websocket.accept()
        request = client.recv(1024)
        send_response(temperature, client)
    except:
        pass

    time.sleep(2)
