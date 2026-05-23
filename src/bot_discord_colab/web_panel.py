import os
import tempfile
import threading
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from pyngrok import ngrok
import uvicorn

from .stt import transcribe_audio
from .llm import generate_reply
from .tts import generate_tts

app = FastAPI()
bot_instance = None
public_url = ""

@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = Path("web/index.html")
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>Erro: web/index.html n\u00e3o encontrado no repositorio.</h1>"

@app.get("/status")
def status():
    return {"ngrok_url": public_url, "status": "online"}

@app.post("/audio/upload")
async def upload_audio(file: UploadFile = File(...)):
    if not bot_instance:
        return {"message": "Erro: O Bot discord nao esta linkado a subthread web."}

    # 1. Salvar o audio que o frontend mandou no disco para o faster-whisper ler
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(await file.read())
        temp_path = temp_audio.name

    try:
        print("\n[PIPELINE] Comecando STT...")
        transcribed_text = transcribe_audio(temp_path)
        print(f"[PIPELINE] Texto ouvido: {transcribed_text}")
        
        if not transcribed_text or transcribed_text.strip() == "":
            return {"message": "Silencio identificado ou audio ruim.", "transcription": "", "reply": ""}
        
        print("[PIPELINE] Comecando LLM (Gerando resposta)...")
        reply = generate_reply(transcribed_text)
        print(f"[PIPELINE] Neuro respondeu: {reply}")
        
        print("[PIPELINE] Comecando TTS...")
        tts_path = tempfile.mktemp(suffix=".wav")
        generate_tts(reply, tts_path)
        
        print("[PIPELINE] Redirecionando p/ chamada de Voz do Discord...")
        bot_instance.play_audio_on_active_call(tts_path)
        
        return {
            "message": "Enviado com sucesso pra chamada!",
            "transcription": transcribed_text,
            "reply": reply
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"message": f"Falha na arvore de Processamento: {str(e)}", "transcription": "", "reply": ""}
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def start_web_server(discord_bot):
    """Inicializa ngrok e levanta o painel web no FastAPI local"""
    global bot_instance, public_url
    bot_instance = discord_bot
    
    port = 8000
    
    auth_token = os.getenv("NGROK_AUTH_TOKEN")
    if auth_token:
        ngrok.set_auth_token(auth_token)
    
    try:
        tunnel = ngrok.connect(port)
        public_url = tunnel.public_url
        print("="*60)
        print(f"WEB PANEL DE VOZ (DAVE WORKAROUND) ABERTO EM:")
        print(f"--> {public_url} <--")
        print("Acesse este link no seu navegador para falar com o bot!")
        print("="*60)
    except Exception as e:
        print(f"Aviso Ngrok: {str(e)}")
        print("O servidor local subirá, mas não ficará acessível à internet.")
    
    # Bloqueia a Thread processando este servidor via uvicorn embutido
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")

def run_web_panel_thread(discord_bot):
    """Lanca o servidor e painel front/back end numa thread escondida para nao engolir o Discord."""
    t = threading.Thread(target=start_web_server, args=(discord_bot,), daemon=True)
    t.start()
    return t