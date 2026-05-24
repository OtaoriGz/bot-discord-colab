from faster_whisper import WhisperModel
import os

import torch

model = None

def get_stt_model():
    global model
    if model is None:
        print("Carregando modelo STT (faster-whisper)...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        model = WhisperModel("small", device=device, compute_type=compute)
        print(f"Modelo STT carregado! ({device} / {compute})")
    return model

def transcribe_audio(file_path: str) -> dict:
    m = get_stt_model()
    segments, info = m.transcribe(file_path, language="pt", vad_filter=True)
    segments = list(segments)
    text = " ".join([segment.text for segment in segments]).strip()
    avg_logprob = sum(s.avg_logprob for s in segments) / len(segments) if segments else 0.0
    return {"text": text, "avg_logprob": avg_logprob}
