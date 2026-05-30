import os
import tempfile
import threading
import asyncio
import yaml
import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pyngrok import ngrok
from typing import Optional
from .stt import transcribe_audio

app = FastAPI()
bot_instance = None
public_url = ""
active_connections = []

# Criar pasta estática caso não exista
static_dir = Path("web/static")
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="web/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = Path("web/index.html")
    if index_path.exists():
        try:
            return index_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return index_path.read_text(encoding="utf-16", errors="replace")
    return "<h1>Erro</h1>"

@app.get("/user", response_class=HTMLResponse)
def view_user():
    user_path = Path("web/user.html")
    if user_path.exists():
        try:
            return user_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return user_path.read_text(encoding="utf-16", errors="replace")
    return "<h1>Erro</h1>"

@app.get("/admin", response_class=HTMLResponse)
def view_admin():
    admin_path = Path("web/admin.html")
    if admin_path.exists():
        try:
            return admin_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return admin_path.read_text(encoding="utf-16", errors="replace")
    return "<h1>Erro</h1>"

@app.get("/api/check_admin")
def check_admin(pw: str = ""):
    right_pw = os.getenv("ADMIN_PASSWORD", "1234")
    return {"success": pw == right_pw}

@app.get("/status")
def status():
    summary = {}
    if bot_instance and bot_instance.state:
        summary = bot_instance.state.get_summary()
    return {"ngrok_url": public_url, "status": "online", "state": summary}

@app.post("/api/cancel")
async def cancel_response():
    """Cancela a próxima fala/resposta do bot."""
    if bot_instance and bot_instance.state:
        await bot_instance.state.set_cancel_requested(True)
        return {"message": "Cancelamento solicitado."}
    return {"message": "Erro: bot não conectado."}

@app.post("/audio/upload")
async def upload_audio(file: UploadFile = File(...), username: str = Form("WebUser")):
    """Recebe áudio do painel, transcreve (STT) e sinaliza ao orquestrador para gerar resposta."""
    if not bot_instance:
        return {"message": "Erro: O Bot discord nao esta linkado"}
        
    if not bot_instance.state.active_voice_channel:
        return {"message": "Erro: O bot precisa entrar em uma call (use /join no Discord)", "transcription": "", "reply": ""}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_path = temp_audio.name

    try:
        import time
        start_time = time.time()
        print("\n[PAINEL] Comecando STT...")
        transcribed_info = transcribe_audio(temp_path)
        transcribed_text = transcribed_info["text"]
        stt_duration = time.time() - start_time
        print(f"[PAINEL] Ouvido ({transcribed_info['avg_logprob']:.2f}) em {stt_duration:.2fs}: {transcribed_text}")
        
        if bot_instance and bot_instance.state:
            await bot_instance.state.set_stt_duration(stt_duration)
            
        if not transcribed_text or transcribed_text.strip() == "":
            return {"message": "Silencio identificado ou audio ruim.", "transcription": "", "reply": ""}
        
        # Adiciona transcrição ao histórico e sinaliza ao orquestrador
        if bot_instance and bot_instance.state:
            await bot_instance.state.add_transcript(user_id=1, username=username, text=transcribed_text)
            await bot_instance.state.set_new_message(True)
            
        # Retorna imediatamente com a transcrição.
        # O orquestrador cuida da geração de resposta (LLM -> TTS -> Discord) em segundo plano.
        return {
            "message": "Transcricao recebida! Resposta sendo gerada pelo orquestrador.",
            "transcription": transcribed_text,
            "reply": "(processando em segundo plano)"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"message": f"Falha: {str(e)}", "transcription": "", "reply": ""}
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            summary = {}
            if bot_instance and bot_instance.state:
                summary = bot_instance.state.get_summary()
            await websocket.send_json({
                "ngrok_url": public_url,
                "status": "online",
                "state": summary
            })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        print(f"[Painel WS] Erro: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.post("/api/control/join")
async def join_channel(channel_id: Optional[int] = None):
    if not bot_instance:
        return {"success": False, "message": "Bot não inicializado."}
    
    async def _do_join():
        discord, commands = bot_instance._require_discord()
        channel = None
        if channel_id:
            channel = bot_instance.bot.get_channel(channel_id)
        
        if not channel and bot_instance.config.active_voice_channel_id:
            channel = bot_instance.bot.get_channel(bot_instance.config.active_voice_channel_id)
            
        if not channel:
            for guild in bot_instance.bot.guilds:
                for vc in guild.voice_channels:
                    channel = vc
                    break
                if channel:
                    break
        
        if not channel:
            return {"success": False, "message": "Nenhum canal de voz encontrado."}
            
        guild_id = channel.guild.id
        existing = await bot_instance._get_voice_client(guild_id)
        if existing and existing.is_connected():
            await existing.move_to(channel)
            voice_client = existing
        else:
            voice_client = await channel.connect()
            
        bot_instance.voice_clients[guild_id] = voice_client
        await bot_instance.state.set_active_voice_channel(channel.id)
        return {"success": True, "message": f"Conectado ao canal {channel.name}"}

    try:
        if bot_instance.bot and bot_instance.bot.loop:
            fut = asyncio.run_coroutine_threadsafe(_do_join(), bot_instance.bot.loop)
            return fut.result(timeout=10.0)
        else:
            return await _do_join()
    except Exception as e:
        return {"success": False, "message": f"Erro ao conectar: {str(e)}"}

@app.post("/api/control/leave")
async def leave_channel():
    if not bot_instance:
        return {"success": False, "message": "Bot não inicializado."}
    
    async def _do_leave():
        active_channel_id = bot_instance.state.active_voice_channel
        if not active_channel_id:
            return {"success": False, "message": "O bot não está em nenhuma call."}
            
        for guild_id, voice_client in list(bot_instance.voice_clients.items()):
            if voice_client.channel.id == active_channel_id:
                await bot_instance._disconnect_guild(guild_id)
                return {"success": True, "message": "Desconectado da chamada de voz."}
        return {"success": False, "message": "Conexão de áudio ativa não encontrada."}

    try:
        if bot_instance.bot and bot_instance.bot.loop:
            fut = asyncio.run_coroutine_threadsafe(_do_leave(), bot_instance.bot.loop)
            return fut.result(timeout=10.0)
        else:
            return await _do_leave()
    except Exception as e:
        return {"success": False, "message": f"Erro ao desconectar: {str(e)}"}

@app.post("/api/control/toggle_feature")
async def toggle_feature(feature: str, enabled: bool):
    if not bot_instance or not bot_instance.state:
        return {"success": False, "message": "Estado não disponível."}
        
    if feature == "stt":
        await bot_instance.state.set_stt_enabled(enabled)
    elif feature == "tts":
        await bot_instance.state.set_tts_enabled(enabled)
    elif feature == "auto_respond":
        await bot_instance.state.set_auto_respond(enabled)
    else:
        return {"success": False, "message": f"Feature desconhecida: {feature}"}
        
    return {"success": True, "message": f"Feature '{feature}' configurada para {enabled}."}

@app.post("/api/control/clear_history")
async def clear_history():
    if not bot_instance or not bot_instance.state:
        return {"success": False, "message": "Estado não disponível."}
        
    with bot_instance.state._lock:
        bot_instance.state.recent_transcripts.clear()
        bot_instance.state.recent_responses.clear()
        
    return {"success": True, "message": "Histórico de conversas limpo."}

@app.get("/api/config")
def get_config():
    try:
        profile_path = Path("config/bot_profile.yaml")
        settings_path = Path("config/settings.yaml")
        
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) if profile_path.exists() else {}
        settings = yaml.safe_load(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
        
        return {
            "success": True,
            "profile": profile,
            "settings": settings
        }
    except Exception as e:
        return {"success": False, "message": f"Erro ao ler configurações: {str(e)}"}

@app.post("/api/config/update")
async def update_config(data: dict):
    if not bot_instance or not bot_instance.config:
        return {"success": False, "message": "Bot não configurado."}
        
    try:
        profile_data = data.get("profile")
        settings_data = data.get("settings")
        
        if profile_data:
            profile_path = Path("config/bot_profile.yaml")
            profile_path.write_text(yaml.dump(profile_data, allow_unicode=True, default_flow_style=False), encoding="utf-8")
            
        if settings_data:
            settings_path = Path("config/settings.yaml")
            settings_path.write_text(yaml.dump(settings_data, allow_unicode=True, default_flow_style=False), encoding="utf-8")
            
        from .config import load_config
        new_config = load_config()
        
        bot_instance.config = new_config
        if hasattr(bot_instance, 'orchestrator') and bot_instance.orchestrator:
            bot_instance.orchestrator.config = new_config
            if bot_instance.orchestrator.tts_mgr:
                bot_instance.orchestrator.tts_mgr.config = new_config
                
        return {"success": True, "message": "Configurações atualizadas e recarregadas com sucesso!"}
    except Exception as e:
        return {"success": False, "message": f"Erro ao atualizar configurações: {str(e)}"}

@app.post("/api/voice/upload")
async def voice_upload(file: UploadFile = File(...)):
    if not bot_instance:
        return {"success": False, "message": "Bot não inicializado."}
        
    try:
        voices_dir = Path("voices")
        voices_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = voices_dir / file.filename
        content = await file.read()
        file_path.write_bytes(content)
        
        settings_path = Path("config/settings.yaml")
        settings = yaml.safe_load(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
        settings["voice_reference"] = str(file_path.as_posix())
        
        settings_path.write_text(yaml.dump(settings, allow_unicode=True, default_flow_style=False), encoding="utf-8")
        
        from .config import load_config
        bot_instance.config = load_config()
        if hasattr(bot_instance, 'orchestrator') and bot_instance.orchestrator:
            bot_instance.orchestrator.config = bot_instance.config
            if bot_instance.orchestrator.tts_mgr:
                bot_instance.orchestrator.tts_mgr.config = bot_instance.config
                
        return {"success": True, "filename": file.filename, "message": f"Voz de referência alterada para {file.filename}"}
    except Exception as e:
        return {"success": False, "message": f"Erro ao fazer upload de voz: {str(e)}"}

@app.post("/api/voice/test")
async def voice_test(text: str = Form(...)):
    if not bot_instance or not hasattr(bot_instance, 'orchestrator') or not bot_instance.orchestrator or not bot_instance.orchestrator.tts_mgr:
        return {"success": False, "message": "TTSManager não inicializado no bot."}
        
    try:
        test_file_path = static_dir / "tts_test.wav"
        tts_path = await bot_instance.orchestrator.tts_mgr.generate_speech(text, str(test_file_path))
        if tts_path:
            return {"success": True, "audio_url": "/static/tts_test.wav", "message": "Fala de teste gerada!"}
        else:
            return {"success": False, "message": "Falha na síntese de áudio de teste."}
    except Exception as e:
        return {"success": False, "message": f"Erro no teste de voz: {str(e)}"}

@app.get("/api/memories")
def get_memories():
    try:
        from .memory import memory_manager
        mems = memory_manager.get_all_memories()
        return {"success": True, "memories": mems}
    except Exception as e:
        return {"success": False, "message": f"Erro ao obter memórias: {str(e)}"}

@app.post("/api/memories/add")
async def add_memory(data: dict):
    try:
        from .memory import memory_manager
        text = data.get("text")
        if not text or text.strip() == "":
            return {"success": False, "message": "Texto de memória vazio."}
            
        mem_id = memory_manager.add_memory(text, metadata={"source": "manual_panel"})
        return {"success": True, "message": "Memória adicionada com sucesso!", "id": mem_id}
    except Exception as e:
        return {"success": False, "message": f"Erro ao adicionar memória: {str(e)}"}

@app.post("/api/memories/delete")
async def delete_memory(data: dict):
    try:
        from .memory import memory_manager
        mem_id = data.get("id")
        if not mem_id:
            return {"success": False, "message": "ID da memória não informado."}
            
        success = memory_manager.delete_memory(mem_id)
        if success:
            return {"success": True, "message": "Memória deletada com sucesso!"}
        return {"success": False, "message": "Memória não encontrada."}
    except Exception as e:
        return {"success": False, "message": f"Erro ao deletar memória: {str(e)}"}

@app.post("/api/memories/clear")
async def clear_memories():
    try:
        from .memory import memory_manager
        memory_manager.clear_memories()
        return {"success": True, "message": "Todas as memórias foram removidas!"}
    except Exception as e:
        return {"success": False, "message": f"Erro ao limpar banco de memórias: {str(e)}"}

def start_web_server(discord_bot):
    global bot_instance, public_url
    bot_instance = discord_bot
    port = 8000
    
    auth_token = os.getenv("NGROK_AUTH_TOKEN")
    if auth_token:
        ngrok.set_auth_token(auth_token)
    
    try:
        tunnel = ngrok.connect(port)
        public_url = tunnel.public_url
        print(f"WEB PANEL DE VOZ ABERTO EM: {public_url}")
    except Exception as e:
        print(f"Aviso Ngrok: {str(e)}")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")

def run_web_panel_thread(discord_bot):
    global bot_instance
    bot_instance = discord_bot
    t = threading.Thread(target=start_web_server, args=(discord_bot,), daemon=True)
    t.start()
    return t
