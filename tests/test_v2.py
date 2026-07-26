import time
from shared.config import config
import assemblyai as aai

aai.settings.api_key = config.ASSEMBLYAI_API_KEY

def on_data(transcript):
    if not getattr(transcript, 'text', None): return
    print("Transcript:", transcript.text)

def on_error(error):
    print("Error:", error)

transcriber = aai.RealtimeTranscriber(
    sample_rate=16000,
    on_data=on_data,
    on_error=on_error,
)
transcriber.connect()
print("Streaming audio...")
with open('q4_live_insights/test_calls/mock_call.wav', 'rb') as f:
    while True:
        data = f.read(4096)
        if not data: break
        transcriber.stream(data)
        time.sleep(0.1)

transcriber.close()
print("Done")
