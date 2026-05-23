import asyncio
import os
from pathlib import Path
from typing import Optional

from .config import AppConfig
from .state import CentralState


class DiscordVoiceBot:
    def __init__(self, config: AppConfig, state: CentralState):
        self.config = config
        self.state = state
        self.bot = None
        self.voice_clients = {}

    def _require_discord(self):
        try:
            import discord
        except ImportError as exc:
            raise RuntimeError(
                "py-cord is not installed. Install dependencies with: pip install -r requirements.txt"
            ) from exc
        return discord

    async def _get_voice_client(self, guild_id: int):
        return self.voice_clients.get(guild_id)

    async def _disconnect_guild(self, guild_id: int):
        voice_client = await self._get_voice_client(guild_id)
        if voice_client:
            if getattr(voice_client, "recording", False):
                voice_client.stop_recording()
            await voice_client.disconnect(force=True)
            self.voice_clients.pop(guild_id, None)
        self.state.active_voice_channel = None

    def create_bot(self):
        discord = self._require_discord()

        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True

        bot = discord.Bot(intents=intents)
        self.bot = bot

        @bot.event
        async def on_ready():
            print(f"Discord bot online as {bot.user}")

        @bot.slash_command(name="status", description="Mostra o status atual do bot.")
        async def status(ctx):
            summary = self.state.get_summary()
            active_channel = summary.get("active_voice_channel") or "nenhum"
            await ctx.respond(
                (
                    f"Online. Canal de voz ativo: {active_channel}. "
                    f"STT: {summary.get('stt_ready')}. TTS: {summary.get('tts_ready')}."
                ),
                ephemeral=True,
            )

        @bot.slash_command(name="join", description="Faz o bot entrar na call.")
        async def join(ctx):
            voice_state = getattr(ctx.author, "voice", None)
            channel = voice_state.channel if voice_state else None

            if channel is None and self.config.active_voice_channel_id:
                channel = bot.get_channel(self.config.active_voice_channel_id)

            if channel is None:
                await ctx.respond("Entre em uma call ou configure active_voice_channel_id.", ephemeral=True)
                return

            existing = await self._get_voice_client(ctx.guild.id)
            if existing and existing.is_connected():
                await existing.move_to(channel)
                voice_client = existing
            else:
                voice_client = await channel.connect()

            self.voice_clients[ctx.guild.id] = voice_client
            self.state.active_voice_channel = channel.id
            await ctx.respond(f"Entrei na call: {channel.name}", ephemeral=True)

        @bot.slash_command(name="leave", description="Faz o bot sair da call.")
        async def leave(ctx):
            await self._disconnect_guild(ctx.guild.id)
            await ctx.respond("Sai da call.", ephemeral=True)

        @bot.slash_command(name="play_test_audio", description="Toca um arquivo de audio na call atual.")
        async def play_test_audio(ctx, path: Optional[str] = None):
            voice_client = await self._get_voice_client(ctx.guild.id)
            if not voice_client or not voice_client.is_connected():
                await ctx.respond("O bot precisa estar em uma call primeiro. Use /join.", ephemeral=True)
                return

            audio_path = Path(path or os.getenv("TEST_AUDIO_PATH", "voices/test.wav"))
            if not audio_path.exists():
                await ctx.respond(f"Arquivo nao encontrado: {audio_path}", ephemeral=True)
                return

            if voice_client.is_playing():
                voice_client.stop()

            source = discord.FFmpegPCMAudio(str(audio_path))
            voice_client.play(source)
            await ctx.respond(f"Tocando audio: {audio_path}", ephemeral=True)

        @bot.slash_command(name="record_test", description="Grava alguns segundos da call em WAV.")
        async def record_test(ctx, seconds: Optional[int] = 5):
            voice_client = await self._get_voice_client(ctx.guild.id)
            if not voice_client or not voice_client.is_connected():
                await ctx.respond("O bot precisa estar em uma call primeiro. Use /join.", ephemeral=True)
                return

            if getattr(voice_client, "recording", False):
                await ctx.respond("Ja existe uma gravacao em andamento.", ephemeral=True)
                return

            seconds = max(1, min(int(seconds or 5), 30))
            output_dir = Path(os.getenv("DISCORD_RECORDINGS_DIR", "recordings"))
            output_dir.mkdir(parents=True, exist_ok=True)

            async def finished_callback(sink, channel):
                saved = []
                for user_id, audio in sink.audio_data.items():
                    file_path = output_dir / f"{user_id}.wav"
                    audio.file.seek(0)
                    file_path.write_bytes(audio.file.read())
                    saved.append(str(file_path))
                message = "Gravacao finalizada: " + (", ".join(saved) if saved else "sem audio capturado")
                await channel.send(message)

            sink = discord.sinks.WaveSink()
            voice_client.start_recording(sink, finished_callback, ctx.channel)
            await ctx.respond(f"Gravando por {seconds}s.", ephemeral=True)

            await asyncio.sleep(seconds)
            if getattr(voice_client, "recording", False):
                voice_client.stop_recording()

        return bot

    def run(self):
        if not self.config.discord_token:
            raise RuntimeError("DISCORD_TOKEN nao configurado.")

        bot = self.bot or self.create_bot()
        bot.run(self.config.discord_token)

    async def start(self):
        if not self.config.discord_token:
            raise RuntimeError("DISCORD_TOKEN nao configurado.")

        bot = self.bot or self.create_bot()
        await bot.start(self.config.discord_token)


def run_discord_bot(config: AppConfig, state: CentralState):
    return DiscordVoiceBot(config=config, state=state).run()


async def start_discord_bot(config: AppConfig, state: CentralState):
    return await DiscordVoiceBot(config=config, state=state).start()
