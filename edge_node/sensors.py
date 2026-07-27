import time
import random
import json
from datetime import datetime

class EVSensorSimulator:
    def __init__(self, station_id="EV-STATION-001"):
        self.station_id = station_id
        # Define normal operating baselines
        self.temperature = 28.0
        self.current = 135.0
        self.gas_ppm = 2.0
        self.fan_speed = 2200

    def generate_data(self, mode="normal"):
        """Generates a single data frame based on the operational mode."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        if mode == "normal":
            # Add subtle realistic fluctuations
            self.temperature = min(50.0, self.temperature + random.uniform(-0.2, 0.5))
            self.current = max(110.0, min(160.0, self.current + random.uniform(-3.0, 3.0)))
            self.gas_ppm = max(0.0, min(6.0, self.gas_ppm + random.uniform(-0.3, 0.3)))
            # Fan speed scales dynamically with temperature
            self.fan_speed = int(1600 + (self.temperature * 45))

        elif mode == "hazard":
            # Simulate a severe thermal runaway and cooling malfunction event
            self.fan_speed = max(0, self.fan_speed - random.randint(200, 500))  # Fan failing
            self.temperature += random.uniform(4.0, 10.0)                        # Temp soaring
            self.current = max(220.0, self.current + random.uniform(10.0, 25.0)) # Short circuit surge
            self.gas_ppm += random.uniform(6.0, 12.0)                           # Battery off-gassing

        return {
            "station_id": self.station_id,
            "timestamp": timestamp,
            "sensors": {
                "cable_temperature_celsius": round(self.temperature, 2),
                "electrical_current_amperes": round(self.current, 2),
                "hydrogen_gas_ppm": round(self.gas_ppm, 2),
                "cooling_fan_speed_rpm": int(self.fan_speed)
            }
        }

if __name__ == "__main__":
    # Test execution to see the data format in action
    simulator = EVSensorSimulator()
    print("--- Simulating Normal Operations ---")
    for _ in range(3):
        print(json.dumps(simulator.generate_data(mode="normal"), indent=2))
        time.sleep(1)