import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """Load default config from JSON file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        # fallback default
        return {
            "reader": {
                "port": "/dev/ttyUSB0",
                "baudrate": 9600,
                "parity": "N",
                "stopbits": 1,
                "timeout": 1
            },
            "mqtt": {
                "host": "localhost",
                "port": 1883,
                "username": "user",
                "password": "pass",
                "topic_prefix": "dtsu666"
            },
            "poll_interval": 30,
            "slave": {
                "id": 1
            },
            "emulator": {
                "enabled": True,
                "port": "/dev/ttySO",
                "baudrate": 9600,
                "parity": "N",
                "stopbits": 1
            },
            "logging": {
                "level": 10
            }
        }
