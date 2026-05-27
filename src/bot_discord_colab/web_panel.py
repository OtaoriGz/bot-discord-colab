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

app = FastAPI()
bot_instance = None
public_url = ""


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
        print("\n[PAINEL] Comecando STT...")
        transcribed_info = transcribe_audio(temp_path)
        transcribed_text = transcribed_info["text"]
        print(f"[PAINEL] Ouvido ({transcribed_info['avg_logprob']:.2f}): {transcribed_text}")
        
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
