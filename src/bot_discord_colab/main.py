import sys
from typing import Optional

from .config import AppConfig, load_config
from .discord_voice import DiscordVoiceBot
from .state import CentralState


def mask_token(token: Optional[str]) -> str:
    if not token:
        return "Nao configurado"
    if len(token) <= 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def print_startup_summary(config: AppConfig):
    print("=" * 60)
    print("BOT DISCORD COLAB")
    print("=" * 60)
    print(f"Nome do bot:       {config.name}")
    print(f"Wake word:         {config.wake_word}")
    print(f"Idioma:            {config.language}")
    print(f"LLM base URL:      {config.llm_base_url}")
    print(f"Modelo LLM:        {config.llm_model}")
    print(f"Modelo TTS:        {config.tts_model}")
    print(f"Volume:            {config.volume}")
    print(f"Silencio:          {config.silence_timeout}s")
    print(f"Voz referencia:    {config.voice_reference}")
    print("-" * 60)
    print(f"Discord token:     {mask_token(config.discord_token)}")
    print(f"LLM API key:       {mask_token(config.llm_api_key)}")
    print(f"Ngrok auth token:  {mask_token(config.ngrok_authtoken)}")
    print("=" * 60)


def run(start_discord: bool = True):
    try:
        config = load_config()
    except Exception as exc:
        print(f"Erro ao carregar configuracoes: {exc}", file=sys.stderr)
        raise

    print_startup_summary(config)
    state = CentralState()

    if not start_discord:
        print("Modo sem Discord ativo. Configuracoes carregadas com sucesso.")
        return {"config": config, "state": state}

    if not config.discord_token:
        print("DISCORD_TOKEN nao configurado. Use run(start_discord=False) para apenas carregar o projeto.")
        return {"config": config, "state": state}

    bot = DiscordVoiceBot(config=config, state=state)
    bot.run()
    return {"config": config, "state": state, "bot": bot}


async def run_async(start_discord: bool = True):
    try:
        config = load_config()
    except Exception as exc:
        print(f"Erro ao carregar configuracoes: {exc}", file=sys.stderr)
        raise

    print_startup_summary(config)
    state = CentralState()

    if not start_discord:
        print("Modo sem Discord ativo. Configuracoes carregadas com sucesso.")
        return {"config": config, "state": state}

    if not config.discord_token:
        print("DISCORD_TOKEN nao configurado. Use await run_async(start_discord=False) para apenas carregar o projeto.")
        return {"config": config, "state": state}

    bot = DiscordVoiceBot(config=config, state=state)
    await bot.start()
    return {"config": config, "state": state, "bot": bot}


if __name__ == "__main__":
    run()
