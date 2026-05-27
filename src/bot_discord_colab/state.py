import time
import asyncio
import threading
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
    event_type: str
    name: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

class CentralState:
    def __init__(self):
        self.human_speaking: bool = False
        self.bot_thinking: bool = False
        self.bot_speaking: bool = False
        self.stt_ready: bool = False
        self.tts_ready: bool = False
        self.new_message: bool = False
        self.cancel_requested: bool = False
        
        self.stt_enabled: bool = True
        self.tts_enabled: bool = True
        self.auto_respond: bool = True
        
        self.active_voice_channel: Optional[int] = None
        self.current_speakers: Set[int] = set()
        
        self.recent_transcripts: List[TranscriptItem] = []
        self.recent_responses: List[ResponseItem] = []
        
        self.last_message_time: float = time.time()
        self.event_queue: Optional[asyncio.Queue[BotEvent]] = None
        self._lock = threading.Lock()

    def init_queue(self):
        if self.event_queue is None:
            self.event_queue = asyncio.Queue()

    async def update_speaking_state(self, is_speaking: bool, source: str = "human"):
        with self._lock:
            if source == "human":
                self.human_speaking = is_speaking
            elif source == "bot":
                self.bot_speaking = is_speaking
            self.last_message_time = time.time()

    async def set_active_voice_channel(self, channel_id: Optional[int]):
        with self._lock:
            self.active_voice_channel = channel_id
            
    async def add_speaker(self, user_id: int):
        with self._lock:
            self.current_speakers.add(user_id)
            self.human_speaking = True
            self.last_message_time = time.time()

    async def remove_speaker(self, user_id: int):
        with self._lock:
            self.current_speakers.discard(user_id)
            if not self.current_speakers:
                self.human_speaking = False
            self.last_message_time = time.time()

    async def add_transcript(self, user_id: int, username: str, text: str):
        item = TranscriptItem(user_id=user_id, username=username, text=text)
        with self._lock:
            self.recent_transcripts.append(item)
            if len(self.recent_transcripts) > 50:
                self.recent_transcripts.pop(0)
            self.last_message_time = time.time()

    async def add_response(self, text: str):
        item = ResponseItem(text=text)
        with self._lock:
            self.recent_responses.append(item)
            if len(self.recent_responses) > 50:
                self.recent_responses.pop(0)
            self.last_message_time = time.time()

    async def dispatch_event(self, event_type: str, name: str, data: Dict[str, Any] = None):
        if self.event_queue is None:
            self.init_queue()
        event = BotEvent(event_type=event_type, name=name, data=data or {})
        await self.event_queue.put(event)

    async def get_next_event(self) -> BotEvent:
        if self.event_queue is None:
            self.init_queue()
        return await self.event_queue.get()

    async def set_new_message(self, val: bool):
        with self._lock:
            self.new_message = val

    async def set_cancel_requested(self, val: bool):
        with self._lock:
            self.cancel_requested = val

    async def set_stt_enabled(self, val: bool):
        with self._lock:
            self.stt_enabled = val

    async def set_tts_enabled(self, val: bool):
        with self._lock:
            self.tts_enabled = val

    async def set_auto_respond(self, val: bool):
        with self._lock:
            self.auto_respond = val

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "human_speaking": self.human_speaking,
                "bot_thinking": self.bot_thinking,
                "bot_speaking": self.bot_speaking,
                "stt_ready": self.stt_ready,
                "tts_ready": self.tts_ready,
                "stt_enabled": self.stt_enabled,
                "tts_enabled": self.tts_enabled,
                "auto_respond": self.auto_respond,
                "new_message": self.new_message,
                "cancel_requested": self.cancel_requested,
                "active_voice_channel": self.active_voice_channel,
                "current_speakers": list(self.current_speakers),
                "recent_transcripts": [t.model_dump() for t in self.recent_transcripts[-10:]],
                "recent_responses": [r.model_dump() for r in self.recent_responses[-10:]],
                "last_message_time": self.last_message_time
            }
