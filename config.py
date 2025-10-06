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
          "dtsu666": {
            "port": "/dev/ttyUSB0",
            "baudrate": 9600,
            "slave_id": 1
          },
          "mqtt": {
            "broker": "localhost",
            "port": 1883,
            "username": "user",
            "password": "pass",
            "topic_prefix": "dtsu666"
          },
          "poll_interval": 30,
          "emulator": {
            "enabled": True,
            "port": "/dev/ttySO",
            "baudrate": 9600,
            "slave_id": 1
          },
          "logging": {
            "level": 10
          }
        }