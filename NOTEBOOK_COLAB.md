# Notebook do Google Colab

Este arquivo descreve como deve ser o notebook completo do Google Colab para rodar o projeto.

O notebook nao deve conter a logica principal do bot. Ele deve funcionar como launcher:

- prepara o ambiente;
- instala dependencias;
- clona ou atualiza o repositorio;
- configura variaveis e tokens;
- sobe o painel via ngrok;
- importa o pacote Python do repositorio;
- executa testes isolados;
- inicia o bot.

Todo o codigo real deve ficar neste repositorio.

## Principios do notebook

- O notebook deve ser simples de rodar de cima para baixo.
- Tokens devem ser inseridos no ambiente do Colab, nunca commitados no repo.
- O repositorio deve ser a fonte da verdade do codigo.
- O painel deve ser exposto por ngrok.
- O idioma padrao do bot deve ser `pt-BR`.
- O STT deve usar `language="pt"` sempre que possivel.
- O TTS deve usar `language="pt"` com XTTS-v2.
- O LLM deve ser API externa no MVP.
- As escolhas de canal, membros escutados e modelo devem vir da configuracao do painel.

## Ordem geral das celulas

1. Verificar GPU e ambiente.
2. Instalar dependencias de sistema.
3. Clonar ou atualizar o repositorio.
4. Instalar dependencias Python.
5. Configurar variaveis de ambiente.
6. Preparar pastas persistentes, se usar Google Drive.
7. Adicionar `src/` ao `PYTHONPATH`.
8. Validar imports.
9. Configurar ngrok.
10. Subir painel.
11. Rodar testes isolados.
12. Iniciar bot completo.
13. Encerrar recursos quando necessario.

## Celula 1 - Verificar GPU e ambiente

Objetivo: confirmar se o Colab esta com GPU e mostrar informacoes uteis de debug.

```python
import os
import sys
import torch

print("Python:", sys.version)
print("CUDA disponivel:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("CUDA:", torch.version.cuda)
else:
    print("Aviso: sem GPU. STT/TTS podem ficar lentos.")
```

Observacao:

- Para XTTS-v2 e faster-whisper, GPU e altamente recomendada.
- No Colab, ativar em `Runtime > Change runtime type > GPU`.

## Celula 2 - Instalar dependencias de sistema

Objetivo: instalar ferramentas que o Discord/audio/STT/TTS precisam.

```python
!apt-get update -y
!apt-get install -y ffmpeg git
```

Possiveis dependencias futuras:

```python
!apt-get install -y libsndfile1
```

## Celula 3 - Clonar ou atualizar o repositorio

Objetivo: baixar este repositorio para dentro do Colab.

Substituir a URL pelo repositorio real quando ele estiver no GitHub.

```python
REPO_URL = "https://github.com/SEU_USUARIO/bot-discord-colab.git"
REPO_DIR = "/content/bot-discord-colab"

import os

if os.path.exists(REPO_DIR):
    %cd {REPO_DIR}
    !git pull
else:
    !git clone {REPO_URL} {REPO_DIR}
    %cd {REPO_DIR}
```

Durante desenvolvimento privado, tambem da para enviar arquivos pelo Colab ou montar o Drive, mas o caminho recomendado e GitHub.

## Celula 4 - Instalar dependencias Python

Objetivo: instalar dependencias do projeto.

Quando `requirements.txt` existir:

```python
%cd /content/bot-discord-colab
!pip install -U pip
!pip install -r requirements.txt
```

Dependencias esperadas no MVP:

```python
!pip install py-cord
!pip install fastapi uvicorn pyngrok python-dotenv pyyaml
!pip install faster-whisper
!pip install TTS
!pip install openai
```

Dependencias possiveis para audio:

```python
!pip install pydub soundfile numpy
```

Observacoes:

- `TTS` pode demorar bastante para instalar.
- Dependencias de audio podem conflitar; se acontecer, registrar a versao que funcionou no `requirements.txt`.
- Se XTTS-v2 pesar muito, usar fallback de TTS para teste de Discord.

## Celula 5 - Configurar variaveis de ambiente

Objetivo: colocar tokens e chaves no runtime sem salvar no repositorio.

```python
import os
from getpass import getpass

os.environ["DISCORD_TOKEN"] = getpass("Discord bot token: ")
os.environ["NGROK_AUTHTOKEN"] = getpass("ngrok auth token: ")
os.environ["LLM_API_KEY"] = getpass("LLM API key: ")

os.environ["BOT_LANGUAGE"] = "pt-BR"
os.environ["STT_LANGUAGE"] = "pt"
os.environ["TTS_LANGUAGE"] = "pt"
```

Se o LLM for OpenAI-compatible:

```python
os.environ["LLM_BASE_URL"] = "https://api.groq.com/openai/v1"
os.environ["LLM_MODEL"] = "llama-3.1-8b-instant"
```

Para OpenRouter:

```python
os.environ["LLM_BASE_URL"] = "https://openrouter.ai/api/v1"
os.environ["LLM_MODEL"] = "openai/gpt-4o-mini"
```

Se usar outro provider OpenAI-compatible, trocar `LLM_BASE_URL` e `LLM_MODEL`.

Variaveis esperadas pelo projeto:

```text
DISCORD_TOKEN
NGROK_AUTHTOKEN
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
BOT_LANGUAGE
STT_LANGUAGE
TTS_LANGUAGE
guild_id
voice_channel_id
listen_member_ids
tts_model
llm_model
speaker_wav
```

## Celula 6 - Montar Google Drive opcional

Objetivo: persistir vozes, memorias e configs entre sessoes do Colab.

```python
from google.colab import drive
drive.mount("/content/drive")
```

Pastas recomendadas:

```python
DRIVE_PROJECT_DIR = "/content/drive/MyDrive/bot-discord-colab"
DRIVE_VOICES_DIR = f"{DRIVE_PROJECT_DIR}/voices"
DRIVE_MEMORIES_DIR = f"{DRIVE_PROJECT_DIR}/memories"

os.makedirs(DRIVE_VOICES_DIR, exist_ok=True)
os.makedirs(DRIVE_MEMORIES_DIR, exist_ok=True)

os.environ["BOT_VOICES_DIR"] = DRIVE_VOICES_DIR
os.environ["BOT_MEMORIES_DIR"] = DRIVE_MEMORIES_DIR
```

Uso recomendado:

- guardar `speaker_wav` no Drive;
- exportar memorias para o Drive;
- nao guardar tokens em arquivo dentro do Drive se ele for compartilhado.

O painel deve poder enviar uma nova voz de referencia por upload ou por gravacao. O notebook precisa considerar essa pasta persistente como destino final do audio recebido.

## Celula 7 - Adicionar src ao path

Objetivo: permitir import do pacote do repositorio.

```python
import sys

REPO_DIR = "/content/bot-discord-colab"
SRC_DIR = f"{REPO_DIR}/src"

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

print("src adicionado:", SRC_DIR)
```

Quando o projeto tiver `pyproject.toml`, poderemos trocar isso por:

```python
!pip install -e .
```

## Celula 8 - Validar imports do projeto

Objetivo: detectar erro de pacote antes de subir Discord/ngrok.

```python
import importlib

modules = [
    "bot_discord_colab",
    "bot_discord_colab.main",
]

for module_name in modules:
    module = importlib.import_module(module_name)
    print("OK:", module_name, module)
```

Quando os modulos existirem, adicionar:

```python
modules = [
    "bot_discord_colab.config",
    "bot_discord_colab.state",
    "bot_discord_colab.discord_voice",
    "bot_discord_colab.stt",
    "bot_discord_colab.tts",
    "bot_discord_colab.llm",
    "bot_discord_colab.panel",
]
```

## Celula 9 - Configurar ngrok

Objetivo: autenticar e preparar tunnel publico para o painel.

```python
import os
from pyngrok import ngrok

ngrok.set_auth_token(os.environ["NGROK_AUTHTOKEN"])

PORT = 8000
public_url = ngrok.connect(PORT, "http")

print("Painel publico:", public_url)
os.environ["PUBLIC_PANEL_URL"] = str(public_url)
os.environ["PANEL_PORT"] = str(PORT)
```

Observacoes:

- O painel local deve rodar em `0.0.0.0:8000`.
- A URL publica do ngrok muda a cada runtime, a menos que use dominio reservado.
- WebSocket costuma funcionar via ngrok, mas deve ser testado cedo.

## Celula 10 - Subir painel

Objetivo: iniciar FastAPI sem travar o notebook.

Forma esperada quando `panel.py` existir:

```python
import threading
import uvicorn

from bot_discord_colab.panel import create_app

app = create_app()

def run_panel():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

panel_thread = threading.Thread(target=run_panel, daemon=True)
panel_thread.start()

print("Painel local: http://127.0.0.1:8000")
print("Painel publico:", os.environ["PUBLIC_PANEL_URL"])
```

Alternativa se o projeto expuser uma funcao propria:

```python
from bot_discord_colab.panel import start_panel

panel = start_panel(host="0.0.0.0", port=8000)
print("Painel publico:", os.environ["PUBLIC_PANEL_URL"])
```

## Celula 11 - Teste rapido do painel

Objetivo: verificar se o painel responde.

```python
import requests

url = "http://127.0.0.1:8000"
response = requests.get(url, timeout=10)

print("Status:", response.status_code)
print(response.text[:300])
```

Quando houver endpoint de healthcheck:

```python
response = requests.get("http://127.0.0.1:8000/health", timeout=10)
print(response.json())
```

## Celula 12 - Teste isolado de TTS

Objetivo: confirmar que XTTS-v2 gera audio em PT-BR antes de integrar Discord.

Forma esperada quando `tts.py` existir:

```python
from bot_discord_colab.tts import TTSService

tts = TTSService(
    language="pt",
speaker_wav="/content/drive/MyDrive/bot-discord-colab/voices/referencia.wav",
)

output_path = "/content/teste_tts.wav"
tts.synthesize_to_file(
    text="Oi, eu estou falando em portugues do Brasil dentro do Colab.",
    output_path=output_path,
)

print("Audio gerado:", output_path)
```

Quando o painel permitir upload ou gravacao de voz:

- salvar o arquivo na pasta persistente do Drive;
- atualizar o caminho configurado do `speaker_wav`;
- rodar um teste curto com a mesma frase para validar a nova voz.

Reproducao no Colab:

```python
from IPython.display import Audio, display

display(Audio(output_path))
```

Fallback para teste simples:

```python
print("Se XTTS-v2 falhar, testar um WAV fixo primeiro para validar Discord.")
```

## Celula 13 - Teste isolado de STT

Objetivo: confirmar que faster-whisper transcreve audio em PT-BR.

Forma esperada quando `stt.py` existir:

```python
from bot_discord_colab.stt import STTService

stt = STTService(model_size="small", language="pt")

audio_path = "/content/teste_ptbr.wav"
segments = stt.transcribe_file(audio_path)

for segment in segments:
    print(segment)
```

Teste direto com faster-whisper, antes do modulo existir:

```python
from faster_whisper import WhisperModel

model = WhisperModel("small", device="cuda", compute_type="float16")
segments, info = model.transcribe(
    "/content/teste_ptbr.wav",
    language="pt",
    vad_filter=True,
)

print("Idioma detectado:", info.language)
for segment in segments:
    print(segment.start, segment.end, segment.text)
```

## Celula 14 - Teste isolado do Discord

Objetivo: iniciar o bot minimo e testar `/join`, `/leave` e `/status`.

Forma esperada quando `discord_voice.py` existir:

```python
from bot_discord_colab.discord_voice import DiscordVoiceBot

bot = DiscordVoiceBot(
    token=os.environ["DISCORD_TOKEN"],
)

bot.run()
```

Como `bot.run()` normalmente bloqueia a celula, o projeto pode expor uma funcao de start em thread:

```python
from bot_discord_colab.discord_voice import start_discord_bot

discord_thread = start_discord_bot(token=os.environ["DISCORD_TOKEN"])
print("Bot Discord iniciado.")
```

Teste manual no Discord:

```text
/status
/join
/leave
```

Depois adicionar:

```text
/play_test_audio
/record_test
```

## Celula 15 - Teste de audio fixo na call

Objetivo: validar saida de audio antes de TTS/LLM.

Forma esperada:

```python
TEST_AUDIO_PATH = "/content/teste_tts.wav"
os.environ["TEST_AUDIO_PATH"] = TEST_AUDIO_PATH

print("No Discord, usar /play_test_audio depois que o bot entrar na call.")
```

O comando `/play_test_audio` deve:

- pegar `TEST_AUDIO_PATH`;
- tocar no voice channel atual;
- registrar sucesso ou erro no painel/log.

## Celula 16 - Teste de captura de audio da call

Objetivo: validar a parte mais arriscada do projeto.

Forma esperada:

```python
print("No Discord, usar /record_test para capturar alguns segundos da call.")
```

O comando `/record_test` deve:

- iniciar captura com `py-cord`;
- gravar audio temporario;
- tentar separar por usuario;
- salvar arquivos em `/content/discord_recordings`;
- mostrar no painel/log o que foi capturado.

Depois testar STT em cima dos arquivos capturados:

```python
recorded_audio = "/content/discord_recordings/usuario.wav"
segments = stt.transcribe_file(recorded_audio)

for segment in segments:
    print(segment)
```

## Celula 17 - Teste de LLM

Objetivo: validar resposta curta em PT-BR sem audio.

Forma esperada quando `llm.py` existir:

```python
from bot_discord_colab.llm import LLMClient

llm = LLMClient(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["LLM_BASE_URL"],
    model=os.environ["LLM_MODEL"],
)

reply = llm.generate_reply(
    system_prompt="Responda sempre em portugues do Brasil, com no maximo duas frases.",
    user_message="Alguem na call perguntou se voce esta funcionando.",
)

print(reply)
```

## Celula 18 - Teste do prompt builder

Objetivo: verificar se persona, historico e memorias entram no prompt.

Forma esperada quando `prompt_builder.py` existir:

```python
from bot_discord_colab.prompt_builder import PromptBuilder

builder = PromptBuilder()

prompt = builder.build(
    bot_name="Lia",
    description="Uma IA de voz para calls no Discord.",
    personality="curiosa, bem humorada, direta",
    recent_history=[
        {"speaker": "Pedro", "text": "Lia, voce esta me ouvindo?"},
    ],
    memories=[
        "Pedro esta criando um bot de Discord que roda no Colab.",
    ],
)

print(prompt)
```

Verificar:

- prompt esta em PT-BR;
- resposta pedida e curta;
- nao inventa falas;
- inclui memorias relevantes.

## Celula 19 - Iniciar bot completo

Objetivo: rodar o pipeline real.

Forma ideal:

```python
from bot_discord_colab.main import run

runtime = run(
    panel_public_url=os.environ["PUBLIC_PANEL_URL"],
    discord_token=os.environ["DISCORD_TOKEN"],
)
```

Antes de chamar `run()`, o notebook deve garantir que a configuracao do painel foi carregada e aplicada:

- `guild_id`
- `voice_channel_id`
- `listen_member_ids`
- `tts_model`
- `llm_model`
- `speaker_wav`

Se `run()` bloquear, tudo bem. O bot principal pode ficar rodando na ultima celula.

Forma alternativa em thread:

```python
import threading
from bot_discord_colab.main import run

bot_thread = threading.Thread(
    target=run,
    kwargs={
        "panel_public_url": os.environ["PUBLIC_PANEL_URL"],
        "discord_token": os.environ["DISCORD_TOKEN"],
    },
    daemon=True,
)

bot_thread.start()
print("Bot completo iniciado.")
```

## Celula 20 - Encerrar ngrok e runtime

Objetivo: limpar tunnels e recursos quando terminar.

```python
from pyngrok import ngrok

ngrok.kill()
print("Tunnels ngrok encerrados.")
```

Quando o projeto tiver shutdown:

```python
runtime.stop()
```

## Fluxo completo esperado no notebook

```text
Colab inicia
  -> instala sistema
  -> instala Python deps
  -> clona repo
  -> configura tokens
  -> adiciona src ao path
  -> sobe ngrok
  -> sobe painel
  -> testa TTS
  -> testa STT
  -> testa Discord
  -> inicia pipeline completo
```

## Dependencias esperadas no requirements.txt

Lista inicial provavel:

```text
py-cord
fastapi
uvicorn
pyngrok
python-dotenv
pyyaml
faster-whisper
TTS
openai
numpy
soundfile
pydub
requests
```

Possiveis dependencias futuras:

```text
chromadb
faiss-cpu
python-multipart
websockets
aiofiles
```

Observacao:

- `python-multipart` sera necessario para upload de arquivo no painel.
- `chromadb` ou `faiss-cpu` so entram quando memoria vetorial for implementada.

## Variaveis de ambiente completas

```text
DISCORD_TOKEN
NGROK_AUTHTOKEN
PUBLIC_PANEL_URL
PANEL_PORT
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
BOT_LANGUAGE
STT_LANGUAGE
TTS_LANGUAGE
BOT_VOICES_DIR
BOT_MEMORIES_DIR
TEST_AUDIO_PATH
```

## Arquivos que o notebook deve esperar no repositorio

```text
requirements.txt
config/bot_profile.yaml
config/settings.yaml
src/bot_discord_colab/main.py
src/bot_discord_colab/panel.py
src/bot_discord_colab/discord_voice.py
src/bot_discord_colab/stt.py
src/bot_discord_colab/tts.py
src/bot_discord_colab/llm.py
src/bot_discord_colab/prompt_builder.py
src/bot_discord_colab/memory.py
```

## Regras para o notebook

- Nao colocar token direto em celula.
- Nao implementar logica grande dentro do notebook.
- Nao depender de arquivo temporario para memoria importante.
- Nao iniciar streaming TTS antes do TTS normal estar funcionando.
- Nao rodar LLM local pesado no MVP.
- Nao iniciar o bot completo antes de testar painel, TTS, STT e Discord isoladamente.

## Checklist de validacao no Colab

Antes de considerar o notebook pronto:

- GPU detectada.
- Dependencias instaladas.
- Repositorio clonado.
- Imports do pacote funcionando.
- ngrok gerou URL publica.
- Painel respondeu localmente.
- Painel abriu pela URL publica.
- TTS gerou audio em PT-BR.
- STT transcreveu audio em PT-BR.
- Bot Discord conectou.
- `/status` respondeu.
- `/join` entrou na call.
- Bot tocou audio na call.
- Bot capturou audio da call.
- Pipeline completo funcionou pelo menos uma vez.

## Primeira versao minima do notebook

Para o primeiro teste real, o notebook pode ter apenas:

1. Verificar GPU.
2. Instalar `ffmpeg`, `git` e dependencias Python.
3. Clonar repo.
4. Configurar `DISCORD_TOKEN`, `NGROK_AUTHTOKEN` e `LLM_API_KEY`.
5. Adicionar `src/` ao path.
6. Subir ngrok.
7. Subir painel.
8. Iniciar bot minimo do Discord.

Depois adicionar STT, TTS e pipeline completo.
