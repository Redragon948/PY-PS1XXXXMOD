import serial
import time
from typing import Any, Dict, Optional, Union


class PS1XXXXMOD:
    """
    Class to interface with the PS1-XX-XX-MOD sensor via serial port.

    This class provides methods to send commands to the sensor, receive responses,
    and interpret data related to gas concentration, temperature, and humidity.

    Attributes:
        ser (serial.Serial): Serial object for serial communication.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        bytesize: int = serial.EIGHTBITS,
        stopbits: int = serial.STOPBITS_ONE,
        parity: str = serial.PARITY_NONE,
        timeout: float = 1.0,
    ) -> None:
        """
        Initializes the serial connection with the sensor.

        Parameters:
            port (str): Serial port to which the sensor is connected (e.g., "COM4" or "/dev/ttyUSB0").
            baudrate (int, optional): Transmission speed in baud. Default is 9600.
            bytesize (int, optional): Number of bits per byte. Default is serial.EIGHTBITS.
            stopbits (int, optional): Number of stop bits. Default is serial.STOPBITS_ONE.
            parity (str, optional): Parity. Default is serial.PARITY_NONE.
            timeout (float, optional): Timeout for read operations. Default is 1.0 seconds.
        """
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            stopbits=stopbits,
            parity=parity,
            timeout=timeout,  # Timeout to prevent blocking
        )
        self.ser.timeout = timeout

    def _send_command(
        self,
        command: bytes,
        needed_response: bool = True,
        attempts: int = 3,
        response_size: int = 9,
        read_timeout: Optional[float] = None,
        write_timeout: Optional[float] = None,
        wait_time: float = 0,
        add_checksum: bool = True,
        ignore_error: bool = True,
    ) -> Union[bytes, bool]:
        """
        Sends a command to the sensor and handles the reception of the response.

        Parameters:
            command (bytes): Command to send to the sensor.
            needed_response (bool, optional): Indicates if a response from the sensor is required. Default is True.
            attempts (int, optional): Number of attempts to send the command. Default is 3.
            response_size (int, optional): Expected size of the response in bytes. Default is 9.
            read_timeout (float, optional): Specific timeout for reading the response.
            write_timeout (float, optional): Specific timeout for writing the command.
            wait_time (float, optional): Wait time after sending the command. Default is 0.
            add_checksum (bool, optional): Indicates whether to add a checksum to the command. Default is True.
            ignore_error (bool, optional): Indicates whether to ignore errors. Default is True.

        Returns:
            bytes: The response received from the sensor if `needed_response` is True.
            bool: True if the command was sent successfully and no response is needed.

        Raises:
            InvalidValue: If a timeout value is invalid and `ignore_error` is False.
            NoResponse: If no response is received and `ignore_error` is False.
        """
        if write_timeout is not None:
            if write_timeout > 0:
                self.ser.timeout = write_timeout
            else:
                if not ignore_error:
                    raise self.InvalidValue("Write timeout must be greater than 0")

        if add_checksum:
            command += self._convert_to_bytes(self._calculate_checksum(command))

        for _ in range(attempts):
            self._clean()
            self.ser.write(command)

            if needed_response:
                if wait_time:
                    if wait_time > 0:
                        time.sleep(wait_time)
                    else:
                        if not ignore_error:
                            raise self.InvalidValue("Wait time must be greater than 0")
                if read_timeout is not None:
                    if read_timeout > 0:
                        self.ser.timeout = read_timeout
                    else:
                        if not ignore_error:
                            raise self.InvalidValue(
                                "Read timeout must be greater than 0"
                            )
                response = self.ser.read(response_size)
                if response:
                    return response
            else:
                return True

        if not ignore_error:
            raise self.NoResponse("Response not received")

    def _clean(self) -> None:
        """
        Cleans the input buffer of the serial port.
        """
        self.ser.reset_input_buffer()

    def _convert_to_bytes(self, input_data: Union[int, str, bytes]) -> bytes:
        """
        Converts the provided input into bytes. Supports various input types:
        - int: Converted to bytes using the minimal length that can contain the value.
        - str: Considered as hexadecimal if compatible, otherwise as an ASCII string.
        - bin (string starting with '0b'): Converted to bytes.

        Parameters:
            input_data (int, str, bytes): Value to convert to `bytes`.

        Returns:
            bytes: Byte representation of the provided input.

        Raises:
            ValueError: If the string format is unrecognized.
            TypeError: If the input type is unsupported.
        """
        if isinstance(input_data, int):
            # Convert an integer to bytes (choosing sufficient size to contain the value)
            byte_length = (input_data.bit_length() + 7) // 8 or 1
            return input_data.to_bytes(byte_length, byteorder="big")

        elif isinstance(input_data, str):
            # Check if it's a hexadecimal string (all characters are hexadecimal)
            try:
                return bytes.fromhex(input_data)
            except ValueError:
                pass  # Continue if it's not a valid hexadecimal string

            # Check if it's a binary string (must start with '0b')
            if input_data.startswith("0b"):
                try:
                    int_value = int(input_data, 2)
                    byte_length = (int_value.bit_length() + 7) // 8 or 1
                    return int_value.to_bytes(byte_length, byteorder="big")
                except ValueError:
                    raise ValueError(f"The binary string '{input_data}' is invalid.")

            # Otherwise, consider the string as an ASCII/UTF-8 string
            return input_data.encode("utf-8")

        elif isinstance(input_data, bytes):
            return input_data

        else:
            raise TypeError(
                "Input type not supported. Must be int, str (hex/bin/ASCII), or bytes."
            )

    def _generate_command_byte_string(
        self, command: Union[int, bytes], payload: Union[int, bytes] = b"\x00"
    ) -> bytes:
        """
        Generates a byte string for the command to send to the sensor.

        Parameters:
            command (int, bytes): Command to send.
            payload (int, bytes, optional): Additional payload for the command. Default is b"\x00".

        Returns:
            bytes: Byte string formatted according to the sensor's protocol.

        Raises:
            TypeError: If `command` or `payload` are not of type int or bytes.
        """
        if not isinstance(command, (bytes, int)):
            raise TypeError("Command must be of type int or bytes.")
        if not isinstance(payload, (bytes, int)):
            raise TypeError("Payload must be of type int or bytes.")

        command_bytes = self._convert_to_bytes(command)
        payload_bytes = self._convert_to_bytes(payload)
        return b"\xFF\x01" + command_bytes + payload_bytes + b"\x00\x00\x00\x00"

    def _byte_to_bin_array(self, byte: int) -> list[int]:
        """
        Converts a byte into a list of bits.

        Parameters:
            byte (int): Byte to convert.

        Returns:
            list[int]: List of bits (0 or 1) representing the byte.
        """
        bit_string = bin(byte)[2:].zfill(8)
        return [int(b) for b in bit_string]

    def _extract_range(self, bytes_data: bytes) -> int:
        """
        Extracts the maximum range from the first two bytes.

        Parameters:
            bytes_data (bytes): Byte sequence from which to extract the range.

        Returns:
            int: Extracted maximum range.
        """
        return (bytes_data[0] << 8) | bytes_data[1]

    def _parse_unit(self, byte: int) -> Optional[tuple[str, str]]:
        """
        Interprets the unit byte.

        Parameters:
            byte (int): Byte representing the unit of measurement.

        Returns:
            tuple[str, str] | None: Measurement unit as a tuple or None if unrecognized.
        """
        if byte == 0x02:
            return "ppm", "mg/m³"
        elif byte == 0x04:
            return "ppb", "µg/m³"
        elif byte == 0x08:
            return "10g/m³", "%"
        else:
            return None

    def _extract_decimal_places(self, byte: int) -> int:
        """
        Extracts the number of decimal places from the specified byte.

        Parameters:
            byte (int): Byte from which to extract decimal places.

        Returns:
            int: Number of decimal places.
        """
        bit_array = self._byte_to_bin_array(byte)
        bit_array.reverse()
        return (
            (bit_array[7] << 3)
            | (bit_array[6] << 2)
            | (bit_array[5] << 1)
            | bit_array[4]
        )

    def _extract_data_sign(self, byte: int) -> int:
        """
        Extracts the data sign from the specified byte.

        Parameters:
            byte (int): Byte from which to extract the sign.

        Returns:
            int: Data sign (0 for positive, 1 for negative).
        """
        bit_array = self._byte_to_bin_array(byte)
        bit_array.reverse()
        return (
            (bit_array[3] << 3)
            | (bit_array[2] << 2)
            | (bit_array[1] << 1)
            | bit_array[0]
        )

    def _extract_gas_concentration(self, bytes_data: bytes) -> int:
        """
        Extracts gas concentration from the specified two bytes.

        Parameters:
            bytes_data (bytes): Two bytes representing gas concentration.

        Returns:
            int: Extracted gas concentration.
        """
        return (bytes_data[0] << 8) + bytes_data[1]

    def _extract_temp(self, bytes_data: bytes) -> float:
        """
        Extracts temperature from the specified two bytes.

        Parameters:
            bytes_data (bytes): Two bytes representing temperature.

        Returns:
            float: Extracted temperature, divided by 100.
        """
        return float((bytes_data[0] << 8) | bytes_data[1]) / 100

    def _extract_hum(self, bytes_data: bytes) -> float:
        """
        Extracts humidity from the specified two bytes.

        Parameters:
            bytes_data (bytes): Two bytes representing humidity.

        Returns:
            float: Extracted humidity, divided by 100.
        """
        return float((bytes_data[0] << 8) | bytes_data[1]) / 100

    def set_active_upload(self) -> None:
        """
        Sets the sensor to active upload mode.

        This method sends a command to the sensor to start active data upload.
        """
        self._clean()

        command = b"\x78"
        payload = b"\x40"
        self._send_command(
            self._generate_command_byte_string(command=command, payload=payload),
            needed_response=False,
        )

    def set_passive_upload(self) -> None:
        """
        Sets the sensor to passive upload mode.

        This method sends a command to the sensor to set passive data upload.
        """
        self._clean()

        command = b"\x78"
        payload = b"\x41"
        self._send_command(
            self._generate_command_byte_string(command=command, payload=payload),
            needed_response=False,
        )

    def get_sensor_info(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves sensor information.

        This method sends a command to the sensor to obtain information such as sensor type,
        maximum range, unit of measurement, data sign, and number of decimal places.

        Returns:
            dict | None: Dictionary containing sensor information or None if the response is invalid.

        Raises:
            InvalidChecksum: If the response checksum is invalid.
        """
        command = b"\xD1"
        response = self._send_command(command, add_checksum=False)
        if response and len(response) == 9:
            if not self._check_response_checksum(response=response):
                raise self.InvalidChecksum(
                    f"Checksum mismatch, response: {str(response)}"
                )
            sensor_type = response[0]
            max_range = self._extract_range(response[1:3])
            unit = response[3]
            decimal_places = self._extract_decimal_places(response[7])
            data_sign = self._extract_data_sign(response[7])
            return {
                "sensor_type": sensor_type,
                "maximum_range": max_range,
                "unit_raw": unit,  # 0x02 (ppm and mg/m³) 0x04 (ppb and µg/m³)
                "unit": self._parse_unit(unit),
                "data_sign": data_sign,  # 0 (positive number) 1 (negative number)
                "decimal_places": decimal_places,  # Number of decimal places, maximum is 3
            }
        return None

    def get_sensor_info_2(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves sensor information using an alternative command.

        This method sends another command to the sensor to obtain additional information
        such as sensor type, maximum range, unit of measurement, data sign,
        and number of decimal places.

        Returns:
            dict | None: Dictionary containing sensor information or None if the response is invalid.

        Raises:
            InvalidChecksum: If the response checksum is invalid.
        """
        command = b"\xD7"
        response = self._send_command(command, add_checksum=False)
        if response and len(response) == 9:
            if not self._check_response_checksum(response=response):
                raise self.InvalidChecksum(
                    f"Checksum mismatch, response: {str(response)}"
                )
            sensor_type = response[2]
            max_range = self._extract_range(response[3:5])
            unit = response[5]
            decimal_places = self._extract_decimal_places(response[6])
            data_sign = self._extract_data_sign(response[6])
            return {
                "sensor_type": sensor_type,
                "maximum_range": max_range,
                "unit_raw": unit,  # 0x02 (ppm and mg/m³), 0x04 (ppb and µg/m³), 0x08 (10g/m³ and %)
                "unit": self._parse_unit(unit),
                "data_sign": data_sign,  # 0 (positive number) 1 (negative number)
                "decimal_places": decimal_places,  # Number of decimal places, maximum is 3
            }
        return None

    def gas_concentration(self, include_unit: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieves the gas concentration measured by the sensor.

        Parameters:
            include_unit (bool, optional): Indicates whether to include units in the results. Default is True.

        Returns:
            dict | None: Dictionary with gas concentrations and their respective units or only numerical values.

        Raises:
            InvalidChecksum: If the response checksum is invalid.
        """
        command = b"\x86"
        response = self._send_command(
            self._generate_command_byte_string(command=command)
        )
        if response and len(response) == 9:
            if not self._check_response_checksum(response=response):
                raise self.InvalidChecksum(
                    f"Checksum mismatch, response: {str(response)}"
                )
            gas_concentration_1 = self._extract_gas_concentration(response[2:4])
            full_range = self._extract_range(response[4:6])
            gas_concentration_2 = self._extract_gas_concentration(response[6:8])
            if include_unit:
                sensor_info = self.get_sensor_info()
                if sensor_info and sensor_info["unit"]:
                    return {
                        "gas_concentration_1": gas_concentration_1,
                        "gas_unit_1": sensor_info["unit"][0],
                        "full_range": full_range,
                        "gas_concentration_2": gas_concentration_2,
                        "gas_unit_2": sensor_info["unit"][1],
                    }
            else:
                return {
                    "gas_concentration_1": gas_concentration_1,
                    "full_range": full_range,
                    "gas_concentration_2": gas_concentration_2,
                }
        return None

    def read_all(self, include_unit: bool = True) -> Optional[Dict[str, Any]]:
        """
        Reads all measurements from the sensor, including gas, temperature, and humidity.

        Parameters:
            include_unit (bool, optional): Indicates whether to include units in the results. Default is True.

        Returns:
            dict | None: Dictionary with all measurements or None if the response is invalid.

        Raises:
            InvalidChecksum: If the response checksum is invalid.
        """
        command = b"\x87"
        response = self._send_command(
            self._generate_command_byte_string(command=command), response_size=13
        )
        if response and len(response) == 13:
            if not self._check_response_checksum(response=response):
                raise self.InvalidChecksum(
                    f"Checksum mismatch, response: {str(response)}"
                )
            gas_concentration_1 = self._extract_gas_concentration(response[2:4])
            full_range = self._extract_range(response[4:6])
            gas_concentration_2 = self._extract_gas_concentration(response[6:8])
            temperature = self._extract_temp(response[8:10])
            humidity = self._extract_hum(response[10:12])
            if include_unit:
                sensor_info = self.get_sensor_info()
                if sensor_info and sensor_info["unit"]:
                    return {
                        "gas_concentration_1": gas_concentration_1,
                        "gas_unit_1": sensor_info["unit"][0],
                        "full_range": full_range,
                        "gas_concentration_2": gas_concentration_2,
                        "gas_unit_2": sensor_info["unit"][1],
                        "temperature": temperature,
                        "humidity": humidity,
                    }
            else:
                return {
                    "gas_concentration_1": gas_concentration_1,
                    "full_range": full_range,
                    "gas_concentration_2": gas_concentration_2,
                    "temperature": temperature,
                    "humidity": humidity,
                }
        return None

    def get_temp_humidity(self) -> Dict[str, float]:
        """
        Retrieves the current temperature and humidity from the sensor.

        Note:
            This method requires the implementation of the correct command to obtain
            temperature and humidity data.

        Returns:
            dict: Dictionary with current temperature and humidity.

        Raises:
            NotImplementedError: If the command to obtain temperature and humidity is not implemented.
        """
        # TODO: Implement the correct command to obtain temperature and humidity
        raise NotImplementedError(
            "The command to obtain temperature and humidity must be implemented."
        )

    def get_temp_humidity_cal(self) -> Dict[str, float]:
        """
        Retrieves the current temperature and humidity from the sensor with calibration.

        Note:
            This method requires the implementation of the correct command to obtain
            calibrated temperature and humidity data.

        Returns:
            dict: Dictionary with calibrated temperature and humidity.

        Raises:
            NotImplementedError: If the command to obtain calibrated temperature and humidity is not implemented.
            InvalidChecksum: If the response checksum is invalid.
        """
        # TODO: Implement the correct command to obtain calibrated temperature and humidity
        raise NotImplementedError(
            "The command to obtain calibrated temperature and humidity must be implemented."
        )

    def enter_sleep_mode(self) -> Optional[bool]:
        """
        Puts the sensor into sleep mode.

        Returns:
            bool | None: True if the command was successfully executed, False otherwise, None if the response is invalid.
        """
        response = self._send_command(
            b"\xAF\x53\x6C\x65\x65\x70", response_size=2, add_checksum=False
        )
        if response and len(response) == 2:
            response_decoded = response.decode("utf-8").strip().lower()
            return response_decoded == "ok"
        return None

    def exit_sleep_mode(self, wait_for_restore: bool = False) -> Optional[bool]:
        """
        Exits the sensor's sleep mode.

        Parameters:
            wait_for_restore (bool, optional): Indicates whether to wait for restoration after exiting sleep mode. Default is False.

        Returns:
            bool | None: True if the command was successfully executed, False otherwise, None if the response is invalid.
        """
        response = self._send_command(
            b"\xAE\x45\x78\x69\x74", response_size=2, add_checksum=False
        )
        if wait_for_restore:
            time.sleep(5)  # Wait 5 seconds for restoration
        if response and len(response) == 2:
            response_decoded = response.decode("utf-8").strip().lower()
            return response_decoded == "ok"
        return None

    def enter_sleep_mode_2(self) -> bool:
        """
        Puts the sensor into sleep mode using an alternative command.

        Returns:
            bool: True if the command was successfully executed, False otherwise.

        Raises:
            InvalidChecksum: If the response checksum is invalid.
        """
        response = self._send_command(
            b"\xA1\x53\x6C\x65\x65\x70\x32", add_checksum=False
        )
        if response and len(response) == 9:
            if not self._check_response_checksum(response=response):
                raise self.InvalidChecksum(
                    f"Checksum mismatch, response: {str(response)}"
                )
            return True
        return False

    def exit_sleep_mode_2(self, wait_for_restore: bool = False) -> bool:
        """
        Exits the sensor's sleep mode using an alternative command.

        Parameters:
            wait_for_restore (bool, optional): Indicates whether to wait for restoration after exiting sleep mode. Default is False.

        Returns:
            bool: True if the command was successfully executed, False otherwise.

        Raises:
            InvalidChecksum: If the response checksum is invalid.
        """
        response = self._send_command(b"\xA2\x45\x78\x69\x74\x32", add_checksum=False)
        if wait_for_restore:
            time.sleep(5)  # Wait 5 seconds for restoration
        if response and len(response) == 9:
            if not self._check_response_checksum(response=response):
                raise self.InvalidChecksum(
                    f"Checksum mismatch, response: {str(response)}"
                )
            return True
        return False

    def turn_off_light(self) -> Optional[bool]:
        """
        Turns off the sensor's light.

        Returns:
            bool | None: True if the command was successfully executed, False otherwise, None if the response is invalid.
        """
        command = b"\x88"
        response = self._send_command(
            self._generate_command_byte_string(command=command),
            response_size=2,
        )
        if response and len(response) == 2:
            response_decoded = response.decode("utf-8").strip().lower()
            return response_decoded == "ok"
        return None

    def turn_on_light(self) -> Optional[bool]:
        """
        Turns on the sensor's light.

        Returns:
            bool | None: True if the command was successfully executed, False otherwise, None if the response is invalid.
        """
        command = b"\x89"
        response = self._send_command(
            self._generate_command_byte_string(command=command),
            response_size=2,
        )
        if response and len(response) == 2:
            response_decoded = response.decode("utf-8").strip().lower()
            return response_decoded == "ok"
        return None

    def query_light_status(self) -> Optional[bool]:
        """
        Queries the status of the sensor's light.

        Returns:
            bool | None: True if the light is on, False if it is off, None if the response is invalid.

        Raises:
            InvalidChecksum: If the response checksum is invalid.
        """
        command = b"\x8A"
        response = self._send_command(
            self._generate_command_byte_string(command=command),
        )
        if response and len(response) == 9:
            if not self._check_response_checksum(response=response):
                raise self.InvalidChecksum("Checksum mismatch")
            return response[2] == 0x01  # 1: on, 0: off
        return None

    def active_reading(self) -> Optional[Dict[str, int]]:
        """
        Actively reads gas concentrations if data is available.

        Returns:
            dict | None: Dictionary with gas concentrations or None if no valid data is available.

        Raises:
            InvalidChecksum: If the checksum of the read data is invalid.
        """
        if self.ser.in_waiting:
            read = self.ser.read(9)
            if read and len(read) == 9:
                if not self._check_response_checksum(response=read):
                    raise self.InvalidChecksum(f"Checksum mismatch, read: {str(read)}")
                gas_concentration_1 = self._extract_gas_concentration(read[2:4])
                full_range = self._extract_range(read[4:6])
                gas_concentration_2 = self._extract_gas_concentration(read[6:8])
                return {
                    "gas_concentration_1": gas_concentration_1,
                    "full_range": full_range,
                    "gas_concentration_2": gas_concentration_2,
                }
        return None

    def close(self) -> None:
        """
        Closes the serial connection with the sensor.
        """
        self.ser.close()

    def _calculate_checksum(
        self, data: bytes, include_first: bool = False, length: int = 0
    ) -> int:
        """
        Calculates the checksum for a sequence of bytes.

        1. Sums the specified bytes (by default, from the second byte to the end or up to the `length` parameter).
        2. Inverts each bit of the result to obtain an 8-bit value.
        3. Adds 1 to the final result.

        Parameters:
            data (bytes): A sequence of bytes from which to calculate the checksum.
            include_first (bool, optional): If True, includes the first byte in the calculations. Default is False.
            length (int, optional): Number of bytes to include in the calculation; if 0, includes up to the end of the sequence.

        Returns:
            int: The calculated checksum as an 8-bit integer.

        Raises:
            ValueError: If `data` contains fewer than 4 bytes, making checksum calculation impossible.
        """
        data_length = len(data)
        if data_length < 4:
            raise ValueError(
                "The data sequence must contain at least 4 bytes for checksum calculation."
            )

        # Define the range of bytes to sum
        start = (
            0 if include_first else 1
        )  # Start from the first byte if include_first is True, otherwise from the second byte

        # Determine the end of the byte range to sum
        if length > 0:
            end = start + length if (start + length) <= data_length else data_length
        else:
            end = data_length + length if length < 0 else data_length

        # Step 1: Sum the specified bytes in the range
        checksum = sum(data[start:end]) & 0xFF  # Take only the last 8 bits of the sum

        # Step 2: Invert each bit
        checksum = ~checksum & 0xFF  # Invert and limit to 8 bits

        # Step 3: Add 1 to the result
        checksum = (checksum + 1) & 0xFF  # Add 1 and limit to 8 bits

        return checksum

    def _check_response_checksum(
        self, response: bytes, include_first: bool = False
    ) -> bool:
        """
        Verifies the checksum of the response received from the sensor.

        Parameters:
            response (bytes): The sequence of bytes received from the sensor, including the checksum.
            include_first (bool, optional): If True, includes the first byte in the checksum calculation. Default is False.

        Returns:
            bool: True if the calculated checksum matches the received checksum, False otherwise.

        Raises:
            ValueError: If the response contains fewer than 1 byte, making checksum verification impossible.
        """
        if len(response) < 1:
            raise ValueError(
                "The response must contain at least 1 byte to verify the checksum."
            )

        # Extract the checksum from the response
        checksum_received = response[-1]

        # Calculate the checksum of the response, excluding the last byte (checksum)
        calculated_checksum = self._calculate_checksum(
            response[:-1], include_first=include_first
        )

        # Check if the calculated checksum matches the received checksum
        return calculated_checksum == checksum_received

    def to_hex(self, int_value: int) -> str:
        """
        Converts an integer value to a hexadecimal string.

        Parameters:
            int_value (int): Integer value to convert.

        Returns:
            str: Hexadecimal representation of the value.
        """
        return "{:02X}".format(int_value)

    class InvalidValue(Exception):
        """
        Exception raised when an invalid value is provided.
        """

        pass

    class InvalidChecksum(Exception):
        """
        Exception raised when the response checksum does not match.
        """

        pass

    class NoResponse(Exception):
        """
        Exception raised when no response is received from the sensor.
        """

        pass


if __name__ == "__main__":
    # Example usage of the PS1XXXXMOD class
    try:
        sensor = PS1XXXXMOD("COM4")
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
