import  struct
import os
import time  
from vesc import create_vesc_packet, is_vesc_parked, COMM_PARK_MODE, COMM_PARK_UNLOCK,  COMM_SET_MOTOR_LIMITS, build_packet,  set_rpm,   set_max_current_limit, vesc_serial, disable_input, Vesc, get_vesc_values,set_duty_cycle, set_current
parked = None  # Global variable
def calculate_speed(rpm, wheel_circumference, gear_ratio=1):
    if rpm < 1000:  # Ignore RPM below 1000 to avoid idle values
        return 0  # Idle speed
    speed = (rpm * wheel_circumference) / gear_ratio
    speed_kmh = (speed * 60) / 1000  # Convert meters per minute to km/h
    return round(speed_kmh, 2)

def calculate_throttle_percentage(current_in, max_current):
    raw_throttle = (current_in / max_current) * 100
    return max(min(raw_throttle, 100), 0)  # Clamp between 0 and 100
 

 
 

 
def park_bike():
    try:
        v =  vesc_serial()
        payload = struct.pack('>B', COMM_PARK_MODE)
        packet = create_vesc_packet(payload)
        v.write(packet)
        response = v.read(1)
        if response and response[0] == COMM_PARK_MODE:
            global parked
            parked = True 
            return True
        else:
            
            print("error")
            return False
    except Exception as e:
        print(f"Failed to park bike: {e}")
        return False
    

def unpark_bike():
    try:
        v =  vesc_serial()
        payload = struct.pack('>B', COMM_PARK_UNLOCK)
        packet = create_vesc_packet(payload)
        v.write(packet)
        response = v.read(1)
        if response and response[0] == COMM_PARK_UNLOCK:
            global parked
            parked = False
            return True
        else:
            return False
    except Exception as e:
        print(f"Failed to unpark bike: {e}")
        return False
    
 