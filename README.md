# PS1XXXXMOD Python Library

![License](https://img.shields.io/badge/license-Apache%202-blue)
![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)

## Overview

**PS1XXXXMOD** is a Python library designed to interface with the **PS1-\*.\*-MOD** series of gas sensors (e.g., PS1-CO-1000-MOD) via a serial port. This library facilitates communication with the sensor, allowing users to send commands, receive responses, and interpret data related to gas concentration, temperature, and humidity.

## Features

- **Active and Passive Upload Modes**: Switch between active and passive data upload modes.
- **Comprehensive Data Retrieval**: Obtain gas concentrations, temperature, humidity, and sensor information.
- **Light Control**: Turn the sensor's light on or off and query its status.
- **Sleep Mode Management**: Enter and exit sleep modes to conserve power.
- **Checksum Verification**: Ensures data integrity through checksum calculations.
- **Error Handling**: Robust exception handling for invalid values, checksum mismatches, and communication issues.
- **Type Hints and Documentation**: Enhanced readability and maintainability with type annotations and detailed docstrings.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Initialization](#initialization)
  - [Basic Operations](#basic-operations)
  - [Advanced Operations](#advanced-operations)
- [API Reference](#api-reference)
- [Example](#example)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.6 or higher
- [pySerial](https://pyserial.readthedocs.io/en/latest/) library

### Installing pySerial

You can install the `pyserial` library using `pip`:

```bash
pip install pyserial
```

### Installing PS1XXXXMOD

Clone the repository and install the library:

```bash
git clone https://github.com/yourusername/PS1XXXXMOD.git
cd PS1XXXXMOD
pip install .
```

## Usage

### Initialization

To start using the `PS1XXXXMOD` class, import it and create an instance by specifying the serial port to which your sensor is connected.

```python
from ps1xxxxmod import PS1XXXXMOD

# Initialize the sensor on COM4 (Windows) or /dev/ttyUSB0 (Linux)
sensor = PS1XXXXMOD(port="COM4")
```

### Basic Operations

#### Setting Upload Modes

- **Active Upload Mode**: The sensor continuously sends data.
- **Passive Upload Mode**: The sensor sends data only upon request.

```python
# Set to active upload mode
sensor.set_active_upload()

# Set to passive upload mode
sensor.set_passive_upload()
```

#### Retrieving Sensor Information

```python
sensor_info = sensor.get_sensor_info()
if sensor_info:
    print("Sensor Information:")
    for key, value in sensor_info.items():
        print(f"{key}: {value}")
```

#### Reading Gas Concentration

```python
gas_data = sensor.gas_concentration(include_unit=True)
if gas_data:
    print("Gas Concentration Data:")
    for key, value in gas_data.items():
        print(f"{key}: {value}")
```

#### Reading All Data

```python
all_data = sensor.read_all(include_unit=True)
if all_data:
    print("All Sensor Data:")
    for key, value in all_data.items():
        print(f"{key}: {value}")
```

#### Controlling the Sensor's Light

```python
# Turn on the light
sensor.turn_on_light()

# Turn off the light
sensor.turn_off_light()

# Query the light status
light_status = sensor.query_light_status()
print(f"Light is {'on' if light_status else 'off'}")
```

#### Managing Sleep Mode

```python
# Enter sleep mode
sensor.enter_sleep_mode()

# Exit sleep mode and wait for restoration
sensor.exit_sleep_mode(wait_for_restore=True)
```

### Advanced Operations

#### Active Reading

Continuously read data if available:

```python
while True:
    data = sensor.active_reading()
    if data:
        print(data)
    time.sleep(1)  # Wait for 1 second between readings
```

#### Converting Seconds to Readable Format

```python
readable_time = PS1XXXXMOD.seconds_to_readable(100000)
print(readable_time)  # Outputs: "0 years, 1 days, 3 hours, 46 minutes, 40 seconds"
```

## API Reference

### `PS1XXXXMOD` Class

#### `__init__(self, port: str, baudrate: int = 9600, bytesize: int = serial.EIGHTBITS, stopbits: int = serial.STOPBITS_ONE, parity: str = serial.PARITY_NONE, timeout: float = 1.0) -> None`

Initializes the serial connection with the sensor.

#### `set_active_upload(self) -> None`

Sets the sensor to active upload mode.

#### `set_passive_upload(self) -> None`

Sets the sensor to passive upload mode.

#### `get_sensor_info(self) -> Optional[Dict[str, Any]]`

Retrieves sensor information.

#### `get_sensor_info_2(self) -> Optional[Dict[str, Any]]`

Retrieves sensor information using an alternative command.

#### `gas_concentration(self, include_unit: bool = True) -> Optional[Dict[str, Any]]`

Retrieves the gas concentration measured by the sensor.

#### `read_all(self, include_unit: bool = True) -> Optional[Dict[str, Any]]`

Reads all measurements from the sensor, including gas, temperature, and humidity.

#### `get_temp_humidity(self) -> Dict[str, float]`

Retrieves the current temperature and humidity from the sensor.

*Note: This method is not yet implemented.*

#### `get_temp_humidity_cal(self) -> Dict[str, float]`

Retrieves the current temperature and humidity from the sensor with calibration.

*Note: This method is not yet implemented.*

#### `enter_sleep_mode(self) -> Optional[bool]`

Puts the sensor into sleep mode.

#### `exit_sleep_mode(self, wait_for_restore: bool = False) -> Optional[bool]`

Exits the sensor's sleep mode.

#### `enter_sleep_mode_2(self) -> bool`

Puts the sensor into sleep mode using an alternative command.

#### `exit_sleep_mode_2(self, wait_for_restore: bool = False) -> bool`

Exits the sensor's sleep mode using an alternative command.

#### `turn_off_light(self) -> Optional[bool]`

Turns off the sensor's light.

#### `turn_on_light(self) -> Optional[bool]`

Turns on the sensor's light.

#### `query_light_status(self) -> Optional[bool]`

Queries the status of the sensor's light.

#### `active_reading(self) -> Optional[Dict[str, int]]`

Actively reads gas concentrations if data is available.

#### `close(self) -> None`

Closes the serial connection with the sensor.

#### `to_hex(self, int_value: int) -> str`

Converts an integer value to a hexadecimal string.

#### `seconds_to_readable(seconds: float) -> str`

Converts a number of seconds into a readable approximate representation (years, days, hours, minutes, and seconds).

### Exceptions

#### `InvalidValue`

Raised when an invalid value is provided.

#### `InvalidChecksum`

Raised when the response checksum does not match.

#### `NoResponse`

Raised when no response is received from the sensor.

## Example

Below is an example script demonstrating how to use the `PS1XXXXMOD` library to read data from a PS1-CO-1000-MOD sensor.

```python
import time
from ps1xxxxmod import PS1XXXXMOD

def main():
    try:
        # Initialize the sensor on COM4 (Windows) or /dev/ttyUSB0 (Linux)
        sensor = PS1XXXXMOD(port="COM4")
        sensor.set_passive_upload()

        print("Starting data read from the sensor...")
        while True:
            data = sensor.read_all()
            if data:
                print(data)
            time.sleep(1)  # Wait one second between readings

    except PS1XXXXMOD.InvalidChecksum as e:
        print(f"Checksum error: {e}")
    except PS1XXXXMOD.NoResponse as e:
        print(f"No response from sensor: {e}")
    except PS1XXXXMOD.InvalidValue as e:
        print(f"Invalid value: {e}")
    except KeyboardInterrupt:
        print("Manual interruption by user.")
    finally:
        sensor.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()
```

**Output:**

```
Starting data read from the sensor...
{'gas_concentration_1': 500, 'gas_unit_1': 'ppm', 'full_range': 1000, 'gas_concentration_2': 250, 'gas_unit_2': 'mg/m³', 'temperature': 23.5, 'humidity': 45.0}
...
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

Please ensure your code adheres to the existing style and includes appropriate documentation and tests.

## License

This project is licensed under the [Apache 2 License](LICENSE).

---

*Feel free to reach out with any questions or suggestions. Happy coding!*
