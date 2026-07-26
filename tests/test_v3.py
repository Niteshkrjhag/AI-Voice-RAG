import time
from shared.config import config
from assemblyai.streaming.v3 import StreamingClient, StreamingClientOptions, StreamingParameters, StreamingEvents
from assemblyai.streaming.v3.models import TurnEvent, ErrorEvent

def on_data(client, event):
    print("Event received!", getattr(event, 'transcript', getattr(event, 'message', str(event))))

def on_error(client, error):
    print("Error:", error)

options = StreamingClientOptions(api_key=config.ASSEMBLYAI_API_KEY)
client = StreamingClient(options)
client.on(StreamingEvents.Turn, on_data)
client.on(StreamingEvents.Error, on_error)

client.connect(StreamingParameters(sample_rate=16000))
print("Streaming audio...")
with open('q4_live_insights/test_calls/mock_call.wav', 'rb') as f:
    f.read(44)
    while True:
        data = f.read(4096)
        if not data: break
        client.stream(data)
        time.sleep(0.01)

print("Forcing endpoint and waiting 20s...")
client.force_endpoint()
time.sleep(20)
client.disconnect()
print("Done")
