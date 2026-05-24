import os
import tempfile
import threading
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pyngrok import ngrok
import uvicorn

from .stt import transcribe_audio
from .llm import generate_reply

from .tts import TTSManager
from .config import load_config
from .state import CentralState

app = FastAPI()
bot_instance = None
public_url = ""
tts_mgr = None

# Serializa o processamento
pipeline_lock = asyncio.Lock()

@app.on_event("startup")
async def startup_event():
    global tts_mgr
    config = load_config()
    while bot_instance is None:
        await asyncio.sleep(0.1)
    tts_mgr = TTSManager(config, bot_instance.state)
    await tts_mgr.initialize()

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
    return {"ngrok_url": public_url, "status": "online"}

@app.post("/audio/upload")
async def upload_audio(file: UploadFile = File(...), username: str = Form("WebUser")):
    if not bot_instance:
        return {"message": "Erro: O Bot discord nao esta linkado"}
        
    if not bot_instance.state.active_voice_channel:
        return {"message": "Erro: O bot precisa entrar em uma call (use /join no Discord)", "transcription": "", "reply": ""}

    async with pipeline_lock:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(await file.read())
            temp_path = temp_audio.name

        tts_path = None
        try:
            print("\n[PIPELINE] Comecando STT...")
            transcribed_info = transcribe_audio(temp_path)
            transcribed_text = transcribed_info["text"]
            print(f"[PIPELINE] Ouvido ({transcribed_info['avg_logprob']:.2f}): {transcribed_text}")
            
            if not transcribed_text or transcribed_text.strip() == "":
                return {"message": "Silencio identificado ou audio ruim.", "transcription": "", "reply": ""}
            
            # Atualizar historico (Seguro)
            if bot_instance and bot_instance.state:
                await bot_instance.state.add_transcript(user_id=1, username=username, text=transcribed_text)
                
            print("[PIPELINE] Comecando LLM (Gerando resposta)...")
            reply = generate_reply(transcribed_text, bot_instance.config, bot_instance.state)
            print(f"[PIPELINE] Neuro respondeu: {reply}")
            
            print("[PIPELINE] Comecando TTS...")
            global tts_mgr
            tts_path_gen = tempfile.mktemp(suffix=".wav")
            tts_path = await tts_mgr.generate_speech(reply, tts_path_gen)
            
            if tts_path is None:
               return {"message": "Erro fatal no TTS", "transcription": transcribed_text, "reply": reply}

            print("[PIPELINE] Redirecionando p/ chamada de Voz do Discord...")
            bot_instance.play_audio_on_active_call(tts_path)
            
            if bot_instance and bot_instance.state:
                await bot_instance.state.add_response(text=reply)
            
            # Limpeza do WAV nao pode ser imediata aqui pois o bot precisa reproduzir.
            # O ideal seria deletar apos a conclusao da reproducao no discord_voice
            return {
                "message": "Enviado com sucesso pra chamada!",
                "transcription": transcribed_text,
                "reply": reply
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"message": f"Falha: {str(e)}", "transcription": "", "reply": ""}
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

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
