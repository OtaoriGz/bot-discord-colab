import os
import yaml
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

class AppConfig(BaseModel):
    # Segredos e Tokens (Carregados do .env ou ambiente)
    discord_token: Optional[str] = None
    llm_api_key: Optional[str] = None
    ngrok_authtoken: Optional[str] = None

    # Configuração de Persona (bot_profile.yaml)
    name: str = "Neuro"
    description: str = ""
    personality: str = ""
    wake_word: str = "Neuro"
    voice_reference: str = "voices/reference.wav"

    # Configurações de Controle e Técnicas (settings.yaml)
    language: str = "pt-BR"
    volume: float = 1.0
    silence_timeout: float = 2.0
    tts_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.1-8b-instant"
    active_guild_id: Optional[int] = None
    active_voice_channel_id: Optional[int] = None
    listen_filter: List[int] = []

def load_config(
    profile_path: str = "config/bot_profile.yaml",
    settings_path: str = "config/settings.yaml"
) -> AppConfig:
    """Carrega as configurações dos arquivos YAML e mescla com overrides de variáveis de ambiente."""
    # Carrega o arquivo .env se estiver disponível
    load_dotenv()
    
    data = {}

    # 1. Carregar perfil do bot (YAML)
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            profile_data = yaml.safe_load(f)
            if profile_data:
                data.update(profile_data)

    # 2. Carregar configurações técnicas (YAML)
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            settings_data = yaml.safe_load(f)
            if settings_data:
                data.update(settings_data)

    # 3. Aplicar overrides de variáveis de ambiente
    env_mappings = {
        "DISCORD_TOKEN": "discord_token",
        "LLM_API_KEY": "llm_api_key",
        "GROQ_API_KEY": "llm_api_key",
        "OPENROUTER_API_KEY": "llm_api_key",
        "NGROK_AUTHTOKEN": "ngrok_authtoken",
        "BOT_NAME": "name",
        "BOT_DESCRIPTION": "description",
        "BOT_PERSONALITY": "personality",
        "BOT_WAKE_WORD": "wake_word",
        "BOT_VOICE_REFERENCE": "voice_reference",
        "BOT_VOLUME": "volume",
        "BOT_SILENCE_TIMEOUT": "silence_timeout",
        "BOT_TTS_MODEL": "tts_model",
        "LLM_BASE_URL": "llm_base_url",
        "BOT_LLM_MODEL": "llm_model",
        "LLM_MODEL": "llm_model",
        "BOT_ACTIVE_GUILD_ID": "active_guild_id",
        "BOT_ACTIVE_VOICE_CHANNEL_ID": "active_voice_channel_id",
        "BOT_LISTEN_FILTER": "listen_filter",
    }

    for env_var, field_name in env_mappings.items():
        val = os.getenv(env_var)
        if val is not None:
            # Converter tipos apropriadamente para manter a validação do Pydantic
            if field_name in ["volume", "silence_timeout"]:
                try:
                    data[field_name] = float(val)
                except ValueError:
                    pass
            elif field_name in ["active_guild_id", "active_voice_channel_id"]:
                try:
                    data[field_name] = int(val)
                except ValueError:
                    pass
            elif field_name == "listen_filter":
                # Permite passar IDs separados por vírgula no env (ex: "12345,67890")
                try:
                    data[field_name] = [int(x.strip()) for x in val.split(",") if x.strip()]
                except ValueError:
                    pass
            else:
                data[field_name] = val

    # Instanciar a classe de configuração que validará todos os dados
    return AppConfig(**data)
