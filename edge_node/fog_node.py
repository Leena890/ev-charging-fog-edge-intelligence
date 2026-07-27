import json
import os
import time
import random
from datetime import datetime
import boto3  # Native AWS SDK to speak to your lab
from sklearn.ensemble import IsolationForest

class FogNode:
    def __init__(self):
        # 1. AWS Cloud Configuration
        # PASTE YOUR EXACT SQS QUEUE URL HERE FROM YOUR SQS CONSOLE
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/457979104534/EV_Station_Queue"
        self.sqs_client = boto3.client('sqs', region_name='us-east-1')

        # 2. Local Deadband Filter State
        self.last_sent_temp = 28.0
        self.deadband_threshold = 1.5  # Ignore temperature changes smaller than 1.5°C

        # 3. Machine Learning Configuration (Isolation Forest)
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.calibrate_local_ml()

        print("\n[Fog Node] Local Edge ML and AWS Cloud Pipeline Initialized successfully.")

    def calibrate_local_ml(self):
        """Generates baseline telemetry to train the edge model locally"""
        print("[Fog Node] Calibrating & collecting baseline data for Edge ML model...")

        # Simulated normal operations baseline dataset
        baseline_data = []
        for _ in range(100):
            temp = random.uniform(25.0, 32.0)
            current = random.uniform(120.0, 150.0)
            gas = random.uniform(1.0, 3.0)
            rpm = random.randint(2400, 2700)
            baseline_data.append([temp, current, gas, rpm])

        self.model.fit(baseline_data)
        print("[Fog Node] Edge Isolation Forest Model Trained successfully!")

    def send_to_cloud(self, payload):
        """Blasts the telemetry packet straight to AWS SQS with an offline failover cache"""
        backup_file = "edge_offline_buffer.json"

        # A. Check if an offline buffer exists and try to flush it first if network is healthy
        if os.path.exists(backup_file):
            print("\n🔄 Network link recovered! Flushing edge local backup buffer to AWS...")
            try:
                with open(backup_file, "r") as f:
                    cached_logs = json.load(f)

                for log in cached_logs:
                    self.sqs_client.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps(log))

                os.remove(backup_file)
                print("✅ Offline edge buffer completely synchronized with AWS Cloud.\n")
            except Exception as flush_err:
                print(f"⚠️ Cloud sync still unstable. Postponing buffer flush: {str(flush_err)}")

        # B. Try to send the live current payload
        try:
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(payload)
            )
            print(f"[Fog Node] Cloud Sync Successful! MessageId: {response.get('MessageId')}")
        except Exception as e:
            # C. FAILOVER TRIGGER: Network is broken. Cache data locally instead of losing it!
            print(f"\n🚨 [NETWORK DROPPED] AWS Cloud unreachable: {str(e)}")
            print(f"⚠️ Local storage failover activated! Writing packet to {backup_file}...")

            existing_cache = []
            if os.path.exists(backup_file):
                try:
                    with open(backup_file, "r") as f:
                        existing_cache = json.load(f)
                except Exception:
                    existing_cache = []

            existing_cache.append(payload)

            with open(backup_file, "w") as f:
                json.dump(existing_cache, f, indent=4)

    def monitor_stream(self):
        print("\n--- Starting Continuous Live Edge Monitoring Stream ---")

        tick_count = 0
        while True:
            tick_count += 1
            time.sleep(2)

            # Updated baseline ranges
            temp = random.uniform(28.0, 34.0)
            current = random.uniform(130.0, 155.0)
            gas = random.uniform(1.2, 3.5)
            rpm = random.randint(2500, 2800)

            # Occasional anomaly trigger every 15 cycles for live testing
            if tick_count % 15 == 0:
                temp = random.uniform(75.0, 85.0)      # Critical spike
                current = random.uniform(280.0, 310.0) # Current surge
                gas = random.uniform(40.0, 50.0)       # Outgassing event
                rpm = random.randint(400, 600)          # Fan motor failure

            # Construct structured log payload
            payload = {
                "station_id": "EV-STATION-001",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "sensors": {
                    "cable_temperature_celsius": round(temp, 2),
                    "electrical_current_amperes": round(current, 2),
                    "hydrogen_gas_ppm": round(gas, 2),
                    "cooling_fan_speed_rpm": int(rpm)
                }
            }

            # Predict using local ML engine (-1 = Anomaly, 1 = Normal)
            current_features = [[temp, current, gas, rpm]]
            prediction = self.model.predict(current_features)[0]

            # CRITICAL ANOMALY DETECTED BY ML
            if prediction == -1:
                print(f"\n🚨 [CRITICAL ANOMALY DETECTED BY EDGE ML] 🚨")
                print("Fog Node executed LOCAL EMERGENCY POWER SHUTDOWN!")
                print(json.dumps(payload, indent=2))
                print("[Fog Node] Bypassing bandwidth filters. Blasting critical alert directly to AWS API Gateway instantly!")
                self.send_to_cloud(payload)
                continue

            # REGULAR TELEMETRY PROCESSING (Deadband Filter Check)
            temp_deviation = abs(temp - self.last_sent_temp)
            if temp_deviation >= self.deadband_threshold:
                print(f"[Fog Node] Significant variation detected. Forwarding telemetry packet to AWS buffer batch.")
                self.send_to_cloud(payload)
                self.last_sent_temp = temp
            else:
                print(f"[Fog Node] Data dropped by Deadband filter (Micro-fluctuation). Saved Bandwidth!")

if __name__ == "__main__":
    node = FogNode()
    node.monitor_stream()
