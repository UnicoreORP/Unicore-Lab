import time
from lightstreamer.client import LightstreamerClient, Subscription, SubscriptionListener

# Live NASA ISS telemetry channels (PUI IDs)
CHANNELS = {
    "S4000001": "Solar Array 2A Voltage (V)",
    "S4000002": "Solar Array 2A Current (A)",
    "S0000001": "Starboard Radiator Loop A Temp (°C)",
    "USLAB000058": "US Lab Cabin Pressure (mmHg)",
    "TIME_000001": "ISS Signal Heartbeat (GMT)",
}

class ISSTelemetryListener(SubscriptionListener):
    def onItemUpdate(self, update):
        item = update.getItemName()
        value = update.getValue("Value")
        ts = update.getValue("TimeStamp")
        label = CHANNELS.get(item, item)
        print(f"[{ts}] {label:<38} | {value}")

def main():
    client = LightstreamerClient("https://push.lightstreamer.com", "ISSLIVE")
    sub = Subscription(
        mode="MERGE",
        items=list(CHANNELS.keys()),
        fields=["TimeStamp", "Value"],
    )
    sub.setRequestedSnapshot("yes")
    sub.addListener(ISSTelemetryListener())

    client.subscribe(sub)
    client.connect()
    print("Connected to NASA ISSLive telemetry stream (Ctrl+C to stop)...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDisconnecting from ISSLive...")
        client.disconnect()

if __name__ == "__main__":
    main()
