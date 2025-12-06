import machine 
import time
import socket
from secrets import SSID, PASSWORD
import network

# ---------- Temperature Function ----------
def get_temp(sensor_temp, conversion_factor):
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    return temperature

# ---------- WiFi Connection ----------
def connect_to_wifi():
    print("Trying to connect to WiFi:", SSID)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    for i in range(20):
        if wlan.isconnected():
            break
        print("Waiting for connection...", i)
        time.sleep(1)

    if wlan.isconnected():
        print("WiFi connected!")
        print(wlan.ifconfig())
    else:
        print("WiFi FAILED to connect.")

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


# ---------- Setup ----------
sensor_temp = machine.ADC(4) # internal temperature sensor
conversion_factor = 3.3 / (65535)
too_low_temp = 16.0
too_high_temp = 22.0

# ---------- Web Server ----------
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
websocket = socket.socket()
websocket.bind(addr)
websocket.listen(1)
print("Web server running on http://{}".format(addr))

LED = machine.Pin("LED", machine.Pin.OUT)

connect_to_wifi()

while True:
    # Update temperature and LED
    temperature = get_temp(sensor_temp, conversion_factor)
    LED.value(temperature < too_low_temp or temperature > too_high_temp)
    print("Temp: {:.2f} °C".format(temperature))

    # Non-blocking accept
    try:
        client, addr = websocket.accept()
        print("Client connected from", addr)
        request = client.recv(1024)
        send_response(temperature, client)
    except Exception as e:
        print(e)  

    time.sleep(2)
