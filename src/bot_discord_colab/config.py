import os
import yaml
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    name: str = "Neuro"
    wake_word: str = "Neuro"
    language: str = "pt"
    
    discord_token: str = ""
    llm_api_key: str = ""
    ngrok_authtoken: str = ""
    
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.1-8b-instant"
    tts_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    
    volume: float = 1.0
    silence_timeout: int = 300
    voice_reference: str = "voices/reference.wav"

def load_config() -> AppConfig:
    data = {}
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    profile_path = os.path.join(base_dir, "config", "bot_profile.yaml")
    settings_path = os.path.join(base_dir, "config", "settings.yaml")

    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = yaml.safe_load(f)
                if profile_data:
                    data.update(profile_data)
        except Exception as e:
            print(f"Erro ao analisar {profile_path}: {e}")

    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings_data = yaml.safe_load(f)
                if settings_data:
                    data.update(settings_data)
        except Exception as e:
            print(f"Erro ao analisar {settings_path}: {e}")

    env_mappings = {
        "DISCORD_TOKEN": "discord_token",
        "LLM_API_KEY": "llm_api_key",
        "NGROK_AUTH_TOKEN": "ngrok_authtoken",
    }
    
    for env_key, config_key in env_mappings.items():
        val = os.getenv(env_key)
        if val:
            data[config_key] = val

    return AppConfig(**data)
