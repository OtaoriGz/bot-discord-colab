import os
import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from .config import AppConfig
from .state import CentralState


class TTSManager:
    """Gerenciador de Text-to-Speech com suporte a XTTS-v2 (Colab/GPU) e fallback gTTS (local/CPU)."""

    MAX_TEXT_CHARS = 220

    def __init__(self, config: AppConfig, state: CentralState):
        self.config = config
        self.state = state
        self.engine: str = "none"
        self._xtts_model = None

    async def initialize(self):
        """Tenta carregar o melhor motor TTS disponível no ambiente atual."""
        # Tentar XTTS-v2 primeiro (disponível apenas no Colab com GPU e Python <3.12)
        if await self._try_load_xtts():
            self.engine = "xtts-v2"
            print("[TTS] Motor carregado: Coqui XTTS-v2 (clonagem de voz)")
        elif self._check_gtts():
            self.engine = "gtts"
            print("[TTS] Motor carregado: gTTS (fallback, sem clonagem)")
        else:
            self.engine = "none"
            print("[TTS] AVISO: Nenhum motor TTS disponível.")

        self.state.tts_ready = self.engine != "none"
        return self.engine

    async def _try_load_xtts(self) -> bool:
        """Tenta carregar o modelo Coqui XTTS-v2. Retorna True se conseguiu."""
        try:
            import torch
            if not torch.cuda.is_available():
                print("[TTS] GPU não detectada, pulando XTTS-v2.")
                return False

            from TTS.api import TTS as CoquiTTS

            model_name = self.config.tts_model
            print(f"[TTS] Carregando modelo XTTS-v2: {model_name}...")
            self._xtts_model = CoquiTTS(model_name=model_name, gpu=True)
            return True
        except ImportError:
            print("[TTS] Coqui TTS não instalado, tentando fallback.")
            return False
        except Exception as e:
            print(f"[TTS] Erro ao carregar XTTS-v2: {e}")
            return False

    def _check_gtts(self) -> bool:
        """Verifica se o gTTS está disponível."""
        try:
            from gtts import gTTS  # noqa: F401
            return True
        except ImportError:
            return False

    def _truncate_text(self, text: str) -> str:
        """Limita o texto ao máximo de caracteres permitido para síntese de voz."""
        if len(text) <= self.MAX_TEXT_CHARS:
            return text

        truncated = text[:self.MAX_TEXT_CHARS]
        # Cortar na última palavra completa para não quebrar no meio
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]

        print(f"[TTS] Texto truncado de {len(text)} para {len(truncated)} caracteres.")
        return truncated

    async def generate_speech(self, text: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Gera um arquivo de áudio a partir do texto fornecido.

        Args:
            text: Texto em PT-BR para sintetizar.
            output_path: Caminho opcional para salvar o áudio. Se None, cria um arquivo temporário.

        Returns:
            Caminho do arquivo de áudio gerado, ou None se falhar.
        """
        if self.engine == "none":
            print("[TTS] Nenhum motor TTS disponível. Impossível gerar áudio.")
            return None

        text = self._truncate_text(text)

        if not text.strip():
            print("[TTS] Texto vazio após truncamento, ignorando.")
            return None

        # Definir caminho de saída
        if output_path is None:
            suffix = ".wav" if self.engine == "xtts-v2" else ".mp3"
            fd, output_path = tempfile.mkstemp(suffix=suffix, prefix="tts_")
            os.close(fd)

        try:
            if self.engine == "xtts-v2":
                return await self._generate_xtts(text, output_path)
            elif self.engine == "gtts":
                return await self._generate_gtts(text, output_path)
        except Exception as e:
            print(f"[TTS] Erro ao gerar áudio: {e}")
            return None

    async def _generate_xtts(self, text: str, output_path: str) -> str:
        """Gera áudio com XTTS-v2 usando clonagem de voz."""
        speaker_wav = self.config.voice_reference

        if not Path(speaker_wav).exists():
            print(f"[TTS] Arquivo de referência de voz não encontrado: {speaker_wav}")
            print("[TTS] Usando gTTS como fallback temporário.")
            return await self._generate_gtts(text, output_path)

        # Executar em thread separada para não bloquear o event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._xtts_model.tts_to_file(
                text=text,
                speaker_wav=speaker_wav,
                language="pt",
                file_path=output_path,
            ),
        )

        print(f"[TTS] Áudio XTTS-v2 gerado: {output_path}")
        return output_path

    async def _generate_gtts(self, text: str, output_path: str) -> str:
        """Gera áudio com gTTS (fallback leve, sem clonagem)."""
        from gtts import gTTS

        # Garantir extensão .mp3 para gTTS
        if not output_path.endswith(".mp3"):
            output_path = str(Path(output_path).with_suffix(".mp3"))

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: gTTS(text=text, lang="pt", slow=False).save(output_path),
        )

        print(f"[TTS] Áudio gTTS gerado: {output_path}")
        return output_path

    def get_status(self) -> dict:
        """Retorna o status atual do módulo TTS para exibição no painel."""
        return {
            "engine": self.engine,
            "ready": self.state.tts_ready,
            "max_chars": self.MAX_TEXT_CHARS,
            "voice_reference": self.config.voice_reference,
            "tts_model": self.config.tts_model,
        }
