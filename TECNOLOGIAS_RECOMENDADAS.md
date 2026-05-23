# Tecnologias recomendadas

Este projeto deve ser pensado como um pacote Python importado por um notebook do Google Colab. O notebook sera apenas o "launcher": ele instala dependencias, clona/importa este repositorio, configura tokens, abre o painel via ngrok e inicia o bot.

Todo o fluxo de conversa deve ser em portugues do Brasil.

## Decisao principal

Stack recomendada para o MVP:

- Linguagem: Python.
- Ambiente de execucao: Google Colab com GPU quando disponivel.
- Bot Discord: `py-cord`.
- Painel: `FastAPI` + WebSocket ou Socket.IO.
- Tunnel do painel: `pyngrok`.
- STT: `faster-whisper`.
- TTS com clonagem de voz: `Coqui XTTS-v2`.
- VAD: Silero VAD, via `faster-whisper` ou modulo separado.
- Memoria inicial: JSON/SQLite.
- Memoria vetorial futura: ChromaDB ou FAISS.
- LLM: preferencialmente API externa no inicio, para deixar a GPU do Colab livre para STT/TTS.

## Arquitetura no Colab

O repositorio nao deve ser o notebook. A estrutura ideal e:

```text
notebook_colab.ipynb
  - clona/importa este repositorio
  - instala dependencias
  - define variaveis de ambiente
  - inicia ngrok
  - chama src/main.py ou uma funcao run()

repositorio/
  - codigo do bot
  - painel
  - configuracoes
  - modulos de audio
  - memoria
  - prompts
```

Isso deixa o projeto versionavel e evita prender a logica dentro do notebook.

## Discord

### Recomendado: py-cord

Motivo:

- Tem suporte pratico a comandos slash.
- Tem documentacao para receber audio de canais de voz usando `start_recording` e sinks.
- Permite criar ou customizar sinks para capturar audio por usuario.

Links:

- https://guide.pycord.dev/voice/receiving
- https://docs.pycord.dev/en/stable/api/voice.html
- https://docs.next.pycord.dev/en/latest/api/sinks.html

Uso esperado:

- Bot entra na call.
- Captura audio dos membros.
- Mantem identificacao por usuario quando possivel.
- Envia audio TTS para o canal de voz.

Risco:

- Receber audio do Discord e processar em tempo real e a parte mais sensivel do projeto.
- O primeiro teste tecnico deve validar entrada e saida de audio antes de implementar memoria ou painel avancado.

## STT em PT-BR

### Recomendado: faster-whisper

`faster-whisper` e uma implementacao do Whisper usando CTranslate2, geralmente mais eficiente que o Whisper original.

Configuracao inicial sugerida:

```python
model_size = "small"
language = "pt"
vad_filter = True
compute_type = "float16"  # GPU
```

Modelos sugeridos:

- `base`: mais leve, pior qualidade, bom para teste rapido.
- `small`: melhor equilibrio para PT-BR no MVP.
- `medium`: melhor qualidade, mas mais pesado.
- `large-v3` ou `turbo`: deixar para testes de qualidade, nao como padrao inicial.

Recomendacao pratica:

- Comecar com `small`.
- Se a transcricao ficar ruim em PT-BR, testar `medium`.
- Se o Colab ficar pesado com STT + TTS, voltar para `base`.

Para mais de uma pessoa falando:

- Nao usar diarizacao pesada no inicio.
- Tentar capturar audio separado por usuario pelo Discord.
- Rodar uma fila de transcricao por chunks curtos.
- Usar VAD para ignorar silencio e economizar GPU/CPU.
- Se duas pessoas falarem ao mesmo tempo, aceitar que a qualidade cai no MVP.

Links:

- https://github.com/SYSTRAN/faster-whisper
- https://github.com/openai/whisper

## TTS em PT-BR com clonagem de voz

### Recomendado: Coqui XTTS-v2

O XTTS-v2 e a melhor escolha inicial porque:

- Suporta portugues.
- Permite clonagem de voz com poucos segundos de audio de referencia.
- Roda localmente em GPU no Colab.
- Ja foi usado em projetos parecidos com assistentes de voz.
- Tem API Python simples.

Configuracao inicial sugerida:

```python
tts_model = "tts_models/multilingual/multi-dataset/xtts_v2"
language = "pt"
speaker_wav = "voices/referencia.wav"
```

Uso esperado:

- O painel permite escolher/enviar o audio de referencia.
- O backend usa esse audio como `speaker_wav`.
- As respostas devem ser curtas para diminuir latencia.
- O sistema pode cachear audios de frases comuns.

Importante:

- XTTS-v2 e bom, mas nao e super leve.
- Para Colab gratuito com GPU T4, deve funcionar melhor com respostas curtas.
- Se STT + TTS + LLM local ficarem pesados juntos, o LLM deve ir para API externa.

Links:

- https://huggingface.co/coqui/XTTS-v2
- https://github.com/coqui-ai/TTS

### Alternativa leve: Piper TTS

Piper e muito mais leve e rapido, bom para fallback.

Vantagens:

- Baixa latencia.
- Pode rodar em CPU.
- Bom para painel, testes e modo economico.

Desvantagem principal:

- Nao e a escolha ideal para clonagem de voz zero-shot.

Uso recomendado:

- Fallback quando XTTS estiver pesado.
- Voz padrao sem clonagem.
- Testes de envio de audio para Discord.

Link:

- https://github.com/rhasspy/piper

### Alternativa experimental: F5-TTS

F5-TTS pode ser interessante para pesquisa e qualidade, mas eu nao usaria como padrao do MVP.

Motivos:

- Mais instavel para empacotar em projeto simples.
- Suporte PT-BR pode depender de modelo/fine-tune especifico.
- Pode aumentar o tempo de instalacao no Colab.

Uso recomendado:

- Testar depois que o fluxo com XTTS-v2 estiver funcionando.

Link:

- https://github.com/SWivid/F5-TTS

## LLM

### Recomendado no MVP: API externa

Como o Colab vai precisar lidar com audio, a opcao mais estavel e usar uma API externa para o modelo de linguagem.

Motivo:

- STT e TTS ja consomem bastante recurso.
- Rodar LLM local junto com XTTS-v2 e Whisper pode estourar VRAM/RAM.
- API externa reduz latencia e simplifica o MVP.

O codigo deve ser abstrato o suficiente para trocar depois:

- OpenAI-compatible API.
- Modelo local via Ollama/text-generation-webui quando estiver fora do Colab.
- Modelo pequeno local se o Colab aguentar.

## Painel de controle

### Recomendado: FastAPI + WebSocket

Motivo:

- Leve.
- Simples de rodar no Colab.
- Facil de expor pelo ngrok.
- Permite atualizar status em tempo real.

Alternativa:

- `python-socketio`, se quisermos eventos nomeados como no Neuro.

Controles iniciais:

- Entrar/sair da call.
- Ativar/desativar STT.
- Ativar/desativar TTS.
- Ativar/desativar respostas automaticas.
- Configurar nome, descricao e personalidade.
- Configurar volume.
- Configurar tempo de silencio antes do bot falar.
- Enviar audio de referencia para clonagem.
- Ver transcricao recente.
- Ver resposta atual.
- Cancelar resposta.
- Interromper fala.
- Criar, editar e apagar memorias.
- Importar audio de referencia para clonagem de voz.
- Gravar audio de referencia direto no painel.

## Clonagem de voz no painel

### Recomendado: upload + gravacao

O painel deve oferecer duas formas de configurar a voz clonada:

- Upload de um arquivo de audio curto.
- Gravacao direta no browser, salva como audio de referencia.

Isso deixa o processo mais pratico porque:

- o usuario pode usar um `.wav` ja existente;
- o usuario pode gravar uma amostra nova sem sair do painel;
- o backend pode normalizar o audio antes de passar para o XTTS-v2.

Fluxo sugerido:

1. Usuario seleciona `upload` ou `gravacao`.
2. Painel envia o audio para o backend.
3. Backend valida duracao, formato e qualidade minima.
4. Backend converte para `.wav` se necessario.
5. Backend salva como `speaker_wav`.
6. TTS usa esse arquivo como referencia.

Regras recomendadas:

- Aceitar audio curto, tipicamente entre 5 e 30 segundos.
- Aceitar formatos comuns como `.wav`, `.mp3` e `.m4a`, convertendo para `.wav` no backend.
- Permitir escutar uma pre-visualizacao da voz antes de aplicar.
- Permitir trocar ou remover a voz clonada no painel.
- Guardar a voz de referencia em pasta persistente quando o projeto rodar no Colab.

Risco:

- Audio ruim de entrada derruba a qualidade da clonagem.
- O painel deve avisar se o audio estiver baixo, muito curto ou com ruido excessivo.

## ngrok

### Recomendado: pyngrok

O notebook pode abrir o tunnel automaticamente:

```python
from pyngrok import ngrok
public_url = ngrok.connect(8000)
print(public_url)
```

O painel roda localmente no Colab e o usuario acessa pela URL publica do ngrok.

## Memoria

### MVP: JSON ou SQLite

Comecar simples:

- `memories/memories.json`, ou
- SQLite local no ambiente do Colab.

Tipos de memoria:

- Perfil de membro.
- Preferencia.
- Fato importante.
- Resumo de call.
- Memoria temporaria.

### Depois: ChromaDB ou FAISS

Quando o bot ja estiver funcionando:

- Adicionar embeddings.
- Buscar memorias por similaridade.
- Injetar apenas memorias relevantes no prompt.

## Fluxo de audio recomendado

```text
Discord voice
  -> captura audio por usuario
  -> VAD remove silencio
  -> fila de chunks curtos
  -> faster-whisper transcreve em pt
  -> historico recente
  -> prompt builder monta contexto
  -> LLM gera resposta curta em pt-BR
  -> XTTS-v2 gera audio com voz clonada
  -> Discord voice toca audio na call
```

## Configuracoes padrao para o MVP

```yaml
language: pt
stt:
  provider: faster-whisper
  model: small
  vad_filter: true
  compute_type: float16

tts:
  provider: xtts-v2
  language: pt
  speaker_wav: voices/referencia.wav
  max_text_chars: 220

discord:
  library: py-cord
  receive_audio: true

panel:
  framework: fastapi
  realtime: websocket
  tunnel: pyngrok

llm:
  provider: external_api
  response_language: pt-BR
  max_response_sentences: 2
```

## Ordem de implementacao recomendada

1. Criar bot Discord com comando para entrar e sair da call.
2. Testar tocar um audio fixo na call.
3. Testar XTTS-v2 gerando uma frase curta em PT-BR.
4. Testar tocar o audio gerado pelo XTTS na call.
5. Testar captura de audio da call com `py-cord`.
6. Testar transcricao com `faster-whisper` em `language="pt"`.
7. Criar pipeline STT -> LLM -> TTS.
8. Criar painel FastAPI e expor com ngrok.
9. Adicionar configuracao de persona pelo painel.
10. Adicionar memoria simples.

## Decisoes importantes

- O bot deve falar sempre em PT-BR.
- O STT deve receber `language="pt"` sempre que possivel.
- O prompt do LLM deve reforcar que a resposta final deve ser em portugues do Brasil.
- As respostas de voz devem ser curtas para reduzir latencia.
- O LLM nao deve rodar localmente no MVP, a menos que sobre recurso.
- A primeira prova tecnica deve ser audio Discord, nao painel nem memoria.
