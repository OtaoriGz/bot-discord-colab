from faster_whisper import WhisperModel
import os

model = None

def get_stt_model():
    global model
    if model is None:
        print("Carregando modelo STT (faster-whisper)...")
        # Usando float32 para forcar rodar de modo confiavel via CPU, ou auto/int8
        model = WhisperModel("small", device="cpu", compute_type="int8")
        print("Modelo STT carregado!")
    return model

def transcribe_audio(file_path: str) -> str:
    m = get_stt_model()
    segments, _ = m.transcribe(file_path, language="pt", vad_filter=True)
    text = " ".join([segment.text for segment in segments])
    return text.strip()