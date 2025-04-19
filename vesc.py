import serial
import struct
from config import VESC_PORT, VESC_BAUDRATE 
COMM_GET_VALUES = 4
COMM_SET_DUTY = 5
COMM_SET_CURRENT = 6
COMM_FW_VERSION = 0
COMM_JUMP_TO_BOOTLOADER = 1
COMM_ERASE_NEW_APP = 2
COMM_WRITE_NEW_APP_DATA = 3
COMM_GET_VALUES = 4
COMM_SET_DUTY = 5
COMM_SET_CURRENT = 6
COMM_SET_CURRENT_BRAKE = 7
COMM_SET_RPM = 8 
COMM_PARK_MODE = 200
COMM_PARK_UNLOCK = 201
COMM_GET_PARKED_STATUS = 202 
COMM_SET_MOTOR_LIMITS = 203
COMM_GET_ADC_VALUES = 204
COMM_SET_BATTERY_CUT = 86 
COMM_GET_PARKED_STATUS = 202
def crc16(data: bytes):
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if (crc & 0x8000):
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc
def create_vesc_packet(payload):
    packet = bytearray()
    length = len(payload)
    
    # Start byte
    if length < 256:
        packet.append(2)  # short packet
        packet.append(length)
    else:
        packet.append(3)
        packet.append((length >> 8) & 0xFF)
        packet.append(length & 0xFF)
    
    # Payload
    packet.extend(payload)

    # CRC
    crc = crc16(payload)
    packet.append((crc >> 8) & 0xFF)
    packet.append(crc & 0xFF)

    # End byte
    packet.append(3)
    
    return bytes(packet)

def vesc_serial():
    try:
        return serial.Serial(VESC_PORT, VESC_BAUDRATE, timeout=0.1)
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None 

  

def build_packet(command_id):
    payload = bytes([command_id])
    length = len(payload)

    if length < 256:
        packet = b'\x02' + bytes([length]) + payload
    else:
        packet = b'\x03' + struct.pack('>H', length) + payload

    crc = crc16(payload)
    packet += struct.pack('>H', crc)
    packet += b'\x03'
    return packet

def read_packet(ser):
    start = ser.read(1)
    if start not in [b'\x02', b'\x03']:
        return None
    
    length = ser.read(1)[0] if start == b'\x02' else struct.unpack('>H', ser.read(2))[0]
    payload = ser.read(length)
    crc_received = struct.unpack('>H', ser.read(2))[0]
    end = ser.read(1)

    if end != b'\x03':
        return None

    if crc16(payload) != crc_received:
        return None

    return payload

def parse_get_values(data):
    values = {}
    i = 0

    def unpack(fmt, size):
        nonlocal i
        val = struct.unpack(fmt, data[i:i+size])[0]
        i += size
        return val  
    adc_values = get_adc_values()
    values['temp_mosfet'] = unpack('>h', 2) / 10.0
    values['temp_motor'] = unpack('>h', 2) / 10.0
    values['current_motor'] = unpack('>i', 4) / 100.0
    values['current_battery'] = unpack('>i', 4) / 100.0
    values['id'] = unpack('>i', 4) / 100.0
    values['iq'] = unpack('>i', 4) / 100.0 
    duty_cycle_raw = unpack('>h', 2) / 1000.0  # Already in 0.0–1.0 range
    values['duty_cycle'] = min(duty_cycle_raw, 1.0) * 0.9  # If you want to scale to 90%

    values['rpm'] = unpack('>i', 4)
    values['v_in'] = (unpack('>h', 2) / 10.0) + 0.5  # Add calibration offset 
    values['amp_hours'] = unpack('>i', 4) / 1000.0  # Reports in mAh correctly
    values['amp_hours_charged'] = unpack('>i', 4) / 1000.0 
    values['watt_hours'] = unpack('>i', 4) / 10000.0
    values['watt_hours_charged'] = unpack('>i', 4) / 10000.0
    values['tachometer'] = unpack('>i', 4)
    values['tachometer_abs'] = unpack('>i', 4) 
    values['adc1'] = adc_values[0] 
    values['adc2'] = adc_values[1] 
    values['isParked'] = is_vesc_parked()
    values['vesc_fw']  = get_vecs_fw_version() 

 
    return values

def get_vesc_values():
    
    serial_con = vesc_serial()  
    serial_con.write(build_packet(COMM_GET_VALUES))
    payload = read_packet(serial_con)

    if payload and payload[0] == COMM_GET_VALUES:
            return parse_get_values(payload[1:])
    else:
            return None
def get_adc_values():
    
    serial_con = vesc_serial()  
    serial_con.write(build_packet(COMM_GET_ADC_VALUES))
    payload = read_packet(serial_con)
    if payload and payload[0] == COMM_GET_ADC_VALUES:
        return list([payload[1], payload[2]])
    else:
        return None
     
def Vesc():
    try:
        data = get_vesc_values()
        if not data:
            return None

         
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None
     
def set_duty_cycle(duty):
    
    serial_con = vesc_serial()  
    try:
        duty = max(0.0, min(duty, 1.0))
        payload = struct.pack('>Bf', COMM_SET_DUTY, duty)
        packet = create_vesc_packet(payload)
        serial_con.write(packet)
        print(f"Duty cycle set to {duty}")
    except Exception as e:
        print(f"Failed to set duty cycle: {e}")
 
def set_current( current):
    payload = struct.pack('>Bf', COMM_SET_CURRENT, current)
    packet = create_vesc_packet(payload)
    serial_con.write(packet)


def get_vecs_fw_version():
    
    serial_con = vesc_serial()  
    payload = struct.pack('>B', COMM_FW_VERSION)
    packet = create_vesc_packet(payload)
    serial_con.write(packet)

    response = read_packet(serial_con)
    if response and response[0] == COMM_FW_VERSION:
        major = response[1]
        minor = response[2]
        return f"{major}.{minor}"
    else:
        return "unknown"

def set_battery_cut(start, end):
     
     serial_con = vesc_serial()  
     try:
         payload = struct('>Bfff', COMM_SET_BATTERY_CUT, start,end)
         packet = create_vesc_packet(payload)
         serial_con.write(packet)
         response = read_packet(serial_con)
         if response and response[0] == COMM_SET_BATTERY_CUT:
             print("Successfully set battery cutoff value")
         else:
             print("Failed to set battery cutoff")
         return True
     except Exception as e:
        print(f"Error occured {e}")
        return False

def set_rpm( rpm):
    
    serial_con = vesc_serial()  
    payload = struct.pack('>Bf', COMM_SET_RPM, rpm)
    packet = create_vesc_packet(payload)
    serial_con.write(packet)
    print(f"RPM set to {rpm}")

def disable_input(serial_con):  
    print("Input mode disabled (APP_NONE).")


def set_max_current_limit(serial_con, limit):
    # This sends a current limit, e.g., 0 to fully restrict
    payload = struct.pack('>f', limit)
    packet = create_vesc_packet(payload)
    serial_con.write(packet)
    print(f"Max current limited to {limit}A")
 

def is_vesc_parked():
    
    serial_con = vesc_serial()  
    try:
        serial_con.write(build_packet(COMM_GET_PARKED_STATUS))

            # Read the response
        payload = read_packet(serial_con)
        if not payload:
            print("No response from VESC")
            return None

            # Confirm it's a valid park status response
        if payload[0] != COMM_GET_PARKED_STATUS:
            print("Unexpected response type")
            return None

            # Interpret response (assume 1 byte boolean: 1 = parked, 0 = not parked)
        parked_flag = payload[1]
        return bool(parked_flag)
    except Exception as e:
        print(f"Error checking parked status: {e}")
        return None
    
def set_motor_current_limit(motor_current, battery_current, fieldweakening): 
    print(motor_current, battery_current, fieldweakening)
    try:
        payload = struct.pack('>Bffff',
    COMM_SET_MOTOR_LIMITS,
    motor_current,
    battery_current,
    fieldweakening,
    0.0
)

        packet = create_vesc_packet(payload)

        serial_con = vesc_serial()
        serial_con.write(packet)
        response = read_packet(serial_con)

        print(f"Got response: {response} ({type(response)})")

        if not response or len(response) < 13:
            print("Invalid or too short response")
            return False

        if isinstance(response[0], bytes):
            # This is wrong — each byte should be int (0-255), not b'\x01'
            print("Response appears to be list of byte-objects, not raw bytes")
            return False

        if response[0] != COMM_SET_MOTOR_LIMITS:
            print(f"Unexpected command in response: {response[0]}")
            return False

        # Now unpack floats — skip the command byte
        l_current_max, l_in_current_max, foc_fw_current_max = struct.unpack('>fff', response[1:13])

        print(f"Vesc Successfully set values Motor_A {l_current_max} Battery_A {l_in_current_max} FieldWeakening_A {foc_fw_current_max}")
        return True
    except Exception as e:
        print(f"Error setting motor current: {e}")
        return False