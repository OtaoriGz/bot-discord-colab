import time
import asyncio
from typing import Dict, List, Set, Any, Optional
from pydantic import BaseModel, Field

class TranscriptItem(BaseModel):
    user_id: int
    username: str
    text: str
    timestamp: float = Field(default_factory=time.time)

class ResponseItem(BaseModel):
    text: str
    timestamp: float = Field(default_factory=time.time)

class BotEvent(BaseModel):
    event_type: str  # ex: "discord", "stt", "tts", "panel"
    name: str        # ex: "join_channel", "transcription_received", "tts_started", "status_update"
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

class CentralState:
    def __init__(self):
        # Flags de status em tempo real
        self.human_speaking: bool = False
        self.bot_thinking: bool = False
        self.bot_speaking: bool = False
        self.stt_ready: bool = False
        self.tts_ready: bool = False
        
        # Conexão de voz e participantes ativos
        self.active_voice_channel: Optional[int] = None
        self.current_speakers: Set[int] = set()  # IDs de usuários falando no momento
        
        # Históricos recentes de conversa
        self.recent_transcripts: List[TranscriptItem] = []
        self.recent_responses: List[ResponseItem] = []
        
        # Registro de tempo para paciência/silêncio
        self.last_message_time: float = time.time()
        
        # Fila central de eventos assíncronos
        self.event_queue: Optional[asyncio.Queue[BotEvent]] = None
        
        # Lock assíncrono para garantir operações atômicas no estado
        self._lock = asyncio.Lock()

    def init_queue(self):
        """Inicializa a fila de eventos no event loop atual (deve ser chamado dentro de uma função assíncrona)."""
        if self.event_queue is None:
            self.event_queue = asyncio.Queue()

    async def update_speaking_state(self, is_speaking: bool, source: str = "human"):
        """Atualiza o estado de quem está falando de forma thread/async-safe."""
        async with self._lock:
            if source == "human":
                self.human_speaking = is_speaking
            elif source == "bot":
                self.bot_speaking = is_speaking
            self.last_message_time = time.time()

    async def add_speaker(self, user_id: int):
        """Adiciona um usuário à lista de falantes ativos na chamada."""
        async with self._lock:
            self.current_speakers.add(user_id)
            self.human_speaking = True
            self.last_message_time = time.time()

    async def remove_speaker(self, user_id: int):
        """Remove um usuário da lista de falantes ativos."""
        async with self._lock:
            self.current_speakers.discard(user_id)
            if not self.current_speakers:
                self.human_speaking = False
            self.last_message_time = time.time()

    async def add_transcript(self, user_id: int, username: str, text: str):
        """Registra uma fala transcrita no histórico de conversação recente."""
        item = TranscriptItem(user_id=user_id, username=username, text=text)
        async with self._lock:
            self.recent_transcripts.append(item)
            # Limita a memória aos últimos 50 registros para evitar consumo excessivo de RAM
            if len(self.recent_transcripts) > 50:
                self.recent_transcripts.pop(0)
            self.last_message_time = time.time()

    async def add_response(self, text: str):
        """Registra uma fala gerada pelo bot no histórico recente."""
        item = ResponseItem(text=text)
        async with self._lock:
            self.recent_responses.append(item)
            if len(self.recent_responses) > 50:
                self.recent_responses.pop(0)
            self.last_message_time = time.time()

    async def dispatch_event(self, event_type: str, name: str, data: Dict[str, Any] = None):
        """Coloca um novo evento na fila de processamento central."""
        if self.event_queue is None:
            self.init_queue()
        event = BotEvent(event_type=event_type, name=name, data=data or {})
        await self.event_queue.put(event)

    async def get_next_event(self) -> BotEvent:
        """Aguarda e retorna o próximo evento da fila."""
        if self.event_queue is None:
            self.init_queue()
        return await self.event_queue.get()

    def get_summary(self) -> Dict[str, Any]:
        """Retorna um resumo de leitura rápida para o painel web ou monitoramento."""
        return {
            "human_speaking": self.human_speaking,
            "bot_thinking": self.bot_thinking,
            "bot_speaking": self.bot_speaking,
            "stt_ready": self.stt_ready,
            "tts_ready": self.tts_ready,
            "active_voice_channel": self.active_voice_channel,
            "current_speakers": list(self.current_speakers),
            "recent_transcripts": [t.model_dump() for t in self.recent_transcripts[-10:]],
            "recent_responses": [r.model_dump() for r in self.recent_responses[-10:]],
            "last_message_time": self.last_message_time
        }
