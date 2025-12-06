#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_time::{Duration, Timer};
use embassy_rp::adc::{Adc, Input};
use embassy_rp::bind_interrupts;
use embassy_rp::gpio::{Level, Output};
use {defmt_rtt as _, panic_probe as _};

// The ADC (analog-to-digital converter) uses interrupts to read data.
// binds the ADC interrupt to the Embassy handler so we can read the temperature sensor safely.
bind_interrupts!(struct Irqs {
    ADC_IRQ => embassy_rp::adc::InterruptHandler;
});

// --------- Temperature calculation ----------
// raw is the ADC reading from the internal temperature sensor
// returns temperature in degrees Celsius
fn pico_temperature(raw: u16) -> f32 {
    let voltage = raw as f32 * 3.3 / 65535.0;
    27.0 - (voltage - 0.706) / 0.001721
}

// --------- Main ----------
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    // Initialize peripherals
    let p = embassy_rp::init(Default::default());

    // LED on GPIO 25
    let mut led = Output::new(p.PIN_25, Level::Low);

    // ADC for internal temperature sensor
    // creates new ADC interface 
    let mut adc = Adc::new(p.ADC, Irqs);
    // point to internal temperature sensor
    let mut temp_pin = Input::new_temp_sensor();

    // Temperature thresholds
    let too_low_temp = 16.0;
    let too_high_temp = 22.0;

    loop {
        let raw = adc.read(&mut temp_pin).unwrap();
        let temp = pico_temperature(raw);

        // LED logic
        if temp < too_low_temp || temp > too_high_temp {
            led.set_high();
        } else {
            led.set_low();
        }

        defmt::info!("Temperature: {} °C", temp);

        Timer::after(Duration::from_secs(2)).await;
    }
}
