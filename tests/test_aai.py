import assemblyai as aai
from shared.config import config
aai.settings.api_key = config.ASSEMBLYAI_API_KEY
print("Testing AssemblyAI connection...")
def on_open(session_opened): print("Opened")
def on_data(transcript): print("Data")
def on_error(error): print(f"Error: {error}")
def on_close(): print("Closed")
transcriber = aai.RealtimeTranscriber(
    sample_rate=16000,
    on_data=on_data,
    on_error=on_error,
    on_open=on_open,
    on_close=on_close,
)
try:
    transcriber.connect()
    print("Connected successfully!")
    transcriber.close()
except Exception as e:
    print(f"Connection failed: {e}")
