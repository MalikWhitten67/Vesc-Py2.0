from vesc import Vesc
import time
CLUTCH_ENGAGED = False
CLUTCH_TIMING_PERIOD = 0.5  # seconds // Time to wait before engaging clutch






def clutch(): 
    vesc_data = Vesc()
    ADC2_VALUE = vesc_data["adc2"]  # Get ADC2 value from VESC data 
    # resting value of ADC2 is 0.5V, so we can use this to determine if the clutch is engaged or not 
    global CLUTCH_ENGAGED
    
