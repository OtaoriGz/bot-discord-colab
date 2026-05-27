import asyncio
import time
import tempfile
import os
from .llm import generate_reply
from .tts import TTSManager

class ConversationOrchestrator:
    """Orquestrador assíncrono que coordena o fluxo de conversa: STT -> LLM -> TTS -> Discord voice."""

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.state = bot.state
        self.tts_mgr = None
        self.active_task = None

    async def initialize(self):
        """Inicializa o gerenciador de TTS."""
        self.tts_mgr = TTSManager(self.config, self.state)
        await self.tts_mgr.initialize()

    async def start(self):
        """Inicia o loop contínuo do orquestrador em segundo plano."""
        print("[Orquestrador] Loop de conversa iniciado.")
        if self.tts_mgr is None:
            await self.initialize()

        # Tempo de silêncio (paciência) antes de assumir que o usuário terminou de falar
        patience_fala = 1.5

        while True:
            try:
                # 1. Verificar cancelamento manual ou interrupção ativa por fala humana
                if self.state.cancel_requested:
                    print("[Orquestrador] Cancelamento de fala solicitado pelo painel.")
                    await self.cancel_current_action()
                    await self.state.set_cancel_requested(False)

                if self.state.human_speaking and (self.state.bot_thinking or self.state.bot_speaking):
                    print("[Orquestrador] Interrupção detectada: Humano começou a falar. Cancelando fala do bot.")
                    await self.cancel_current_action()

                # 2. Processar novas mensagens pendentes
                if self.state.new_message:
                    last_time = self.state.last_message_time
                    time_since_last = time.time() - last_time

                    # Só responde se o humano tiver parado de falar e o tempo de silêncio exceder a paciência
                    if not self.state.human_speaking and time_since_last >= patience_fala:
                        await self.state.set_new_message(False)
                        
                        if self.state.auto_respond:
                            # Cancela qualquer tarefa anterior antes de começar a nova
                            if self.active_task and not self.active_task.done():
                                self.active_task.cancel()

                            # Dispara a geração de resposta em uma task cancelável
                            self.active_task = asyncio.create_task(self.process_response_pipeline())

            except Exception as e:
                print(f"[Orquestrador] Erro no loop de orquestração: {e}")

            await asyncio.sleep(0.1)

    async def cancel_current_action(self):
        """Cancela a tarefa de geração atual e para a reprodução de áudio."""
        if self.active_task and not self.active_task.done():
            print("[Orquestrador] Cancelando tarefa ativa de LLM/TTS...")
            self.active_task.cancel()
            try:
                await self.active_task
            except asyncio.CancelledError:
                pass
            self.active_task = None

        self.state.bot_thinking = False
        await self.state.update_speaking_state(False, source="bot")
        
        # Parar áudio no bot do Discord
        self.bot.stop_audio()

    async def process_response_pipeline(self):
        """Executa a pipeline de resposta de forma assíncrona."""
        try:
            if not self.state.recent_transcripts:
                return

            last_transcript = self.state.recent_transcripts[-1]
            text = last_transcript.text
            username = last_transcript.username

            print(f"[Orquestrador] Processando resposta para: {username}: '{text}'")

            # Seta bot_thinking = True
            self.state.bot_thinking = True

            # 1. Geração de resposta (LLM) executada em executor (não-bloqueante)
            loop = asyncio.get_running_loop()
            reply = await loop.run_in_executor(
                None,
                lambda: generate_reply(text, self.config, self.state)
            )

            if asyncio.current_task().cancelled():
                return

            print(f"[Orquestrador] Resposta gerada: '{reply}'")
            self.state.bot_thinking = False

            # 2. Geração do áudio falado (TTS)
            if self.state.tts_enabled:
                tts_path_gen = tempfile.mktemp(suffix=".wav")
                tts_path = await self.tts_mgr.generate_speech(reply, tts_path_gen)

                if tts_path is None:
                    print("[Orquestrador] Falha ao gerar fala via TTS.")
                    return

                if asyncio.current_task().cancelled():
                    try:
                        if os.path.exists(tts_path):
                            os.remove(tts_path)
                    except:
                        pass
                    return

                # 3. Adiciona a resposta gerada ao histórico
                await self.state.add_response(text=reply)

                # 4. Toca o áudio gerado no Discord
                print(f"[Orquestrador] Enviando áudio gerado ao Discord: {tts_path}")
                self.bot.play_audio_on_active_call(tts_path)
            else:
                # 3. Adiciona a resposta gerada ao histórico (apenas texto)
                print("[Orquestrador] TTS desativado. Pulando geração de áudio.")
                await self.state.add_response(text=reply)

        except asyncio.CancelledError:
            print("[Orquestrador] Pipeline de resposta cancelada.")
            raise
        except Exception as e:
            print(f"[Orquestrador] Erro na pipeline de resposta: {e}")
            self.state.bot_thinking = False
