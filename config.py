# config.py
MAX_VESC_CURRENT = 60.0  # Maximum current in Amps
PIVESC_VERSION = 0.1
VESC_PORT = '/dev/ttyACM0'
VESC_BAUDRATE = 115200

PROFILES = {
    "eco": {
        "current": 30,
        "fw": 0,
    },
    "street": {
        "current": 60,
        "fw": 30,
    },
    "boost": {
        "current": 100,
        "fw": 60,
    }
}
