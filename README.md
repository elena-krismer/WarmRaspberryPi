# WarmRaspberryPI

Features
- Reads internal temperature of Raspberry Pi Pico W
- Turns LED on when temperature is outside defined thresholds, off otherwise
- Optional MicroPython web server to display current temperature
- Rust version uses Embassy for asynchronous handling and LED control

## WiFi-Enabled Raspberry Pi Pico Temperature Monitor

This application was designed to run on a Raspberry Pi Pico W and provide real-time temperature readings through a simple web interface. The system measures the internal temperature sensor, evaluates whether the temperature falls outside a user-defined safe range, and then serves the data to any connected browser through an onboard web server. An LED indicator is used to signal when the temperature is too low or too high.

**Challenge: WiFi Connection Issues**

During development, one of the main obstacles was establishing a reliable WiFi connection. The Pico W repeatedly failed to connect to the home network, even though the SSID and password were correct. Connection attempts resulted in long waiting loops without the device ever joining the network.

After investigation, the issue was traced to WiFi band compatibility. The Raspberry Pi Pico W only supports 2.4 GHz WiFi, while some routers—and even certain smartphone hotspot configurations—default to 5 GHz, which the Pico cannot detect or use.

**Solution**

The issue was resolved by switching to a network that operated on 2.4 GHz. In this case, enabling a smartphone hotspot proved to be the most effective and immediate solution. By activating the hotspot’s compatibility mode (which forces 2.4 GHz on both iPhone and Android), the Pico W was able to connect instantly.

After updating the SSID and password in the code, the WiFi connection became stable, allowing the web server to function as intended.

**Outcome**

With the WiFi issue resolved, the temperature monitoring application now performs reliably. It successfully reads temperature data, hosts a web page accessible from any device on the same network, and visually alerts the user when the temperature crosses defined thresholds. This troubleshooting process also reinforced the importance of WiFi band compatibility when working with microcontroller-based wireless systems.

## MicroPython Version

Create a secrets.py file with your WiFi credentials:

```python
SSID = "your_wifi_ssid"
PASSWORD = "your_wifi_password"
```

Upload the main script and secrets.py to the Pico W.

## Rust Version

### Build and Flash
Build for the Pico W:

```bash
cargo build --release 
```


Flash to the Pico W:
```bash
probe-rs run --chip RP2040 target/thumbv6m-none-eabi/release/rustpie
```


LED will indicate temperature status (on/off based on thresholds).
