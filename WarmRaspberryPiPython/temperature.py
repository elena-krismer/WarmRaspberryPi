import machine 
import time
import socket
from secrets import SSID, PASSWORD

# ---------- Temperature Function ----------
def get_temp(sensor_temp, conversion_factor):
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    return temperature

# ---------- WiFi Connection ----------
def connect_to_wifi():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        pass
    print("Connected to WiFi:", wlan.ifconfig())  

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
        print(e)  # Ignore if no client is connected

    time.sleep(2)
