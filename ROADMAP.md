# Roadmap do projeto

Este arquivo serve como guia de execucao do projeto. Ele deve permitir retomar o desenvolvimento mesmo depois de resetar a conversa.

## Visao geral

Queremos criar um bot de Discord que rode no Google Colab, seja importado como repositorio Python por um notebook e tenha um painel de controle acessivel via ngrok.

O bot deve atuar como uma pessoa dentro de uma chamada de voz do Discord. Todo o fluxo de conversa deve ser em portugues do Brasil.

Foco inicial:

- Entrar em chamada de voz.
- Ouvir membros da call.
- Transcrever audio em PT-BR.
- Gerar resposta curta com personalidade.
- Falar na call usando TTS em PT-BR com clonagem de voz.
- Ter painel para configurar nome, foto, descricao, personalidade, volume, memorias e parametros tecnicos.

## Stack escolhida para o MVP

- Python como linguagem principal.
- Google Colab como ambiente de execucao.
- Notebook externo apenas como launcher.
- `py-cord` para Discord.
- `faster-whisper` para STT em PT-BR.
- `Coqui XTTS-v2` para TTS com clonagem de voz em PT-BR.
- `FastAPI` + WebSocket para painel.
- `pyngrok` para expor o painel.
- LLM via API externa no MVP.
- JSON ou SQLite para memoria inicial.

## Escala de dificuldade

- Facil: tarefa direta, pouco risco, boa para modelos menores.
- Media: exige integrar algumas partes ou tomar decisoes tecnicas.
- Dificil: envolve audio, concorrencia, Colab, Discord ou dependencia pesada.
- Critica: alto risco tecnico; deve ser testada cedo e com modelo mais forte.

Sugestao de modelo:

- Facil: modelo pequeno/rapido.
- Media: modelo intermediario.
- Dificil: modelo forte.
- Critica: melhor modelo disponivel.

## Fase 0 - Base do repositorio

Objetivo: preparar estrutura minima do projeto.

Tarefas:

1. [x] Criar estrutura de pastas:
   - `src/`
   - `src/bot_discord_colab/`
   - `config/`
   - `memories/`
   - `voices/`
   - `notebooks/`
   - `scripts/`

   Dificuldade: Facil.

2. [x] Criar arquivos base:
   - `requirements.txt`
   - `.env.example`
   - `config/bot_profile.yaml`
   - `config/settings.yaml`
   - `memories/memories.json`
   - `src/bot_discord_colab/__init__.py`

   Dificuldade: Facil.

3. [x] Definir entrada principal do pacote:
   - `src/bot_discord_colab/main.py`
   - funcao `run()` para ser chamada pelo notebook.

   Dificuldade: Facil.

4. [x] Atualizar README com modo de execucao pelo Colab.

   Dificuldade: Facil.

Pronto quando:

- O repositorio tiver estrutura clara.
- O pacote puder ser importado localmente.
- O README explicar que o notebook apenas importa e executa o projeto.

## Fase 1 - Configuracao e estado central

Objetivo: criar base configuravel para persona, audio, painel e runtime.

Tarefas:

1. [x] Criar modelo de configuracao do bot:
   - nome
   - descricao
   - personalidade
   - idioma fixo `pt-BR`
   - wake word
   - volume
   - tempo de silencio antes de falar
   - caminho do audio de referencia para voz
   - selecao do modelo de TTS e do modelo de IA
   - selecao da call/canal de voz do servidor
   - filtro de quem o bot vai escutar

   Dificuldade: Facil.

2. [x] Criar loader de YAML:
   - carregar `config/bot_profile.yaml`
   - carregar `config/settings.yaml`
   - permitir override por variaveis de ambiente.

   Dificuldade: Media.

3. [x] Criar estado central:
   - `human_speaking`
   - `bot_thinking`
   - `bot_speaking`
   - `stt_ready`
   - `tts_ready`
   - `active_voice_channel`
   - `current_speakers`
   - `recent_transcripts`
   - `recent_responses`
   - `last_message_time`

   Dificuldade: Media.

4. [x] Criar fila de eventos:
   - eventos do Discord
   - eventos de transcricao
   - eventos de painel
   - eventos de TTS

   Dificuldade: Media.

Pronto quando:

- O projeto carrega configuracoes.
- O estado central pode ser lido pelo painel e pelos modulos.
- O idioma padrao fica fixado em PT-BR.

## Fase 2 - Discord voice

Objetivo: implementar a parte de voz do Discord.

Tarefas:

1. [x] Criar bot com `py-cord`.

   Dificuldade: Media.

2. [x] Criar comandos slash:
   - `/join`: bot entra na call do usuario.
   - `/leave`: bot sai da call.
   - `/status`: mostra status basico.

   Dificuldade: Media.

3. [x] Implementar reproducao de audio fixo na call:
   - usar arquivo `.wav` simples.
   - confirmar a saida de audio no canal.

   Dificuldade: Dificil.

4. [x] Implementar captura de audio da call:
   - usar `start_recording`.
   - usar `WaveSink` ou sink customizado.
   - verificar se o audio vem separado por usuario.

   Dificuldade: Critica.

5. [x] Criar log tecnico:
   - usuario detectado
   - inicio/fim de fala
   - tamanho do chunk
   - caminho do arquivo/chunk salvo temporariamente

   Dificuldade: Media.

Pronto quando:

- Bot entra e sai da call.
- Bot toca audio na call.
- Bot recebe audio de pelo menos uma pessoa.
- Se possivel, identifica qual usuario falou.

Risco principal:

- Recebimento de audio em tempo real no Discord pode ser instavel. Se `py-cord` nao atender, avaliar forks ou outra biblioteca antes de continuar.

## Fase 3 - DAVE Workaround (Web Panel)

Objetivo: Suprir a falha atual do py-cord em transcrever audio nativamente pelas restrições do protocolo DAVE do Discord.

Tarefas:

1. [x] Criar interface HTML para captura de microfone.
   Dificuldade: Fácil.
   
2. [x] Criar módulo FastAPI para receber e processar audio (Upload e STT via faster-whisper)
   Dificuldade: Média.

3. [x] Criar fluxo LLM (Groq) e TTS (gTTS para fallback).
   Dificuldade: Média.

4. [x] Integrar Ngrok Tunnel e Uvicorn concorrentemente ao loop do Discord e usar `play_audio_on_active_call`.
   Dificuldade: Crítica.

Pronto quando:
- Painel Web acessível compila fala e toca resposta de volta no Discord.
- Contornamos o problema de recebimento nativo do Discord (DAVE).

## Fase 4 - STT em PT-BR

Objetivo: transformar audio da call em texto em portugues do Brasil.

Tarefas:

1. Instalar e configurar `faster-whisper` no Colab.

   Dificuldade: Media.

2. Criar modulo `stt.py`:
   - carregar modelo `small` por padrao.
   - usar `language="pt"`.
   - usar `vad_filter=True`.
   - aceitar chunks de audio.

   Dificuldade: Dificil.

3. Criar fila de transcricao:
   - receber chunks da call.
   - descartar silencio.
   - transcrever em ordem.
   - salvar resultado no historico recente.

   Dificuldade: Dificil.

4. Ajustar modelos:
   - `base` para modo leve.
   - `small` como padrao.
   - `medium` se a qualidade em PT-BR estiver ruim.

   Dificuldade: Media.

5. Registrar transcricao com metadados:
   - usuario
   - timestamp
   - texto
   - confianca, se disponivel
   - origem do audio

   Dificuldade: Media.

Pronto quando:

- Fala em PT-BR e transcrita corretamente em frases curtas.
- O sistema aguenta pelo menos mais de uma pessoa participando, mesmo que nao fale ao mesmo tempo.
- O estado central mostra ultimas transcricoes.

## Fase 4 - TTS em PT-BR com clonagem

Objetivo: fazer o bot falar na call com voz clonada.

Tarefas:

1. [x] Instalar e configurar `Coqui TTS` com XTTS-v2 no Colab.

   Dificuldade: Dificil.

2. [x] Criar modulo `tts.py`:
   - carregar XTTS-v2.
   - usar `language="pt"`.
   - usar `speaker_wav` configuravel.
   - gerar arquivo de audio temporario.

   Dificuldade: Dificil.

3. [x] Criar limite de texto para TTS:
   - maximo inicial: 220 caracteres.
   - cortar ou pedir resposta menor quando passar disso.

   Dificuldade: Facil.

4. Tocar audio gerado na call.

   Dificuldade: Dificil.

5. [x] Criar fallback para TTS:
   - gTTS como fallback quando XTTS nao estiver disponivel.

   Dificuldade: Media.

6. Evoluir para streaming de TTS:
   - MVP pode gerar WAV completo.
   - Depois implementar streaming/chunks para reduzir latencia.
   - Inspiracao: Neuro usa abordagem com RealtimeTTS.
   - Esta e uma implementacao futura, nao a primeira versao.

   Dificuldade: Critica.

Pronto quando:

- XTTS-v2 gera fala em PT-BR.
- A voz usa audio de referencia.
- O Discord reproduz a fala gerada.
- O usuario consegue trocar o arquivo de referencia depois pelo painel.

## Fase 5 - LLM e prompt builder

Objetivo: gerar respostas curtas, naturais e em PT-BR.

Tarefas:

1. Criar cliente LLM abstrato:
   - API externa OpenAI-compatible.
   - configuracao por `.env`.
   - metodo `generate_reply(context)`.

   Dificuldade: Media.

2. Criar `prompt_builder.py` por camadas:
   - persona fixa.
   - configuracoes da call.
   - historico recente.
   - memorias relevantes.
   - prompt customizado do painel.
   - instrucao final de resposta curta.

   Dificuldade: Media.

3. Forcar PT-BR no prompt:
   - "Responda sempre em portugues do Brasil."
   - "Use fala natural de chamada de voz."
   - "Nao responda em ingles."

   Dificuldade: Facil.

4. Criar regras de fala:
   - maximo 1 ou 2 frases.
   - evitar monologos.
   - nao inventar falas de membros.
   - nao interromper usuarios.
   - responder como pessoa do grupo, nao como assistente corporativo.

   Dificuldade: Facil.

5. Criar gatilhos de resposta:
   - wake word.
   - pergunta direta.
   - mencao ao nome do bot.
   - silencio configurado.
   - botao "falar agora" no painel.

   Dificuldade: Dificil.

Pronto quando:

- O bot responde em PT-BR.
- Respostas sao curtas e adequadas para TTS.
- O prompt final pode ser visualizado.

## Fase 6 - Pipeline completo da call

Objetivo: conectar Discord voice, STT, LLM e TTS.

Fluxo desejado:

```text
audio da call
  -> VAD
  -> faster-whisper
  -> historico recente
  -> decisor de resposta
  -> prompt builder
  -> LLM
  -> XTTS-v2
  -> audio no Discord
```

Tarefas:

1. Criar orquestrador da conversa.

   Dificuldade: Dificil.

2. Impedir sobreposicao:
   - nao responder se humano esta falando.
   - nao gerar nova resposta se bot esta falando.
   - permitir cancelar resposta.

   Dificuldade: Dificil.

3. Criar "patience loop":
   - se passar X segundos sem fala, bot pode falar.
   - configuravel no painel.
   - desligavel.

   Dificuldade: Media.

4. Criar historico de call:
   - ultimas N transcricoes.
   - ultimas N respostas.
   - nomes dos membros.

   Dificuldade: Media.

5. Testar com 1 pessoa.

   Dificuldade: Dificil.

6. Testar com mais de 1 pessoa.

   Dificuldade: Critica.

Pronto quando:

- Usuario fala em PT-BR.
- Bot entende.
- Bot gera resposta.
- Bot fala na call.
- O loop nao entra em eco infinito.

Risco principal:

- O bot pode ouvir a propria voz se a captura nao separar bem fontes. Precisamos impedir que o audio do TTS volte para o STT.

## Fase 7 - Painel de controle via ngrok

Objetivo: criar interface de configuracao e monitoramento.

Tarefas:

1. Criar backend `FastAPI`.

   Dificuldade: Media.

2. Criar pagina inicial do painel:
   - status do bot.
   - status Discord.
   - status STT.
   - status TTS.
   - status LLM.

   Dificuldade: Media.

3. Criar WebSocket para eventos ao vivo:
   - transcricoes.
   - resposta atual.
   - bot pensando.
   - bot falando.
   - membro falando.

   Dificuldade: Dificil.

4. Criar controles:
   - entrar/sair da call.
   - ativar/desativar STT.
   - ativar/desativar TTS.
   - ativar/desativar auto resposta.
   - cancelar proxima resposta.
   - interromper fala atual.
   - limpar historico.

   Dificuldade: Media.

5. Criar edicao de persona:
   - nome.
   - descricao.
   - personalidade.
   - estilo de fala.
   - wake word.

   Dificuldade: Media.

6. Criar upload/configuracao de voz:
   - arquivo `.wav` de referencia.
   - teste de frase.
   - volume.
   - importacao de audio para clonagem.
   - gravacao direta da voz no painel.
   - escolha do modelo de clonagem/voz, se houver mais de um.

   Dificuldade: Dificil.

7. Expor via `pyngrok` no notebook.

   Dificuldade: Media.

Pronto quando:

- Painel abre por URL do ngrok.
- Painel mostra status em tempo real.
- Configuracoes alteradas no painel afetam o bot sem reiniciar, quando possivel.

## Fase 8 - Memorias

Objetivo: permitir que o bot guarde e use informacoes relevantes.

Tarefas:

1. Criar memoria simples em JSON ou SQLite.

   Dificuldade: Media.

2. Criar tipos de memoria:
   - `perfil_membro`
   - `preferencia`
   - `fato_importante`
   - `resumo_call`
   - `temporaria`

   Dificuldade: Facil.

3. Criar CRUD de memorias:
   - criar.
   - listar.
   - editar.
   - apagar.

   Dificuldade: Media.

4. Integrar memoria ao prompt:
   - no MVP, selecionar por nome do usuario ou busca simples.
   - depois usar embeddings.

   Dificuldade: Media.

5. Criar reflexao periodica:
   - a cada bloco de conversa, perguntar ao LLM o que vale salvar.
   - nao salvar informacao sensivel desnecessaria.
   - pedir confirmacao no painel antes de tornar memoria permanente, se desejado.

   Dificuldade: Dificil.

6. Evoluir para memoria vetorial:
   - ChromaDB ou FAISS.
   - embeddings.
   - busca semantica.

   Dificuldade: Dificil.

Pronto quando:

- Painel mostra memorias.
- Bot usa memorias relevantes em respostas.
- Usuario pode apagar memoria manualmente.

## Fase 9 - Notebook launcher do Colab

Objetivo: criar um notebook limpo que execute o repositorio.

Tarefas:

1. Criar notebook ou roteiro em `notebooks/`.

   Dificuldade: Media.

2. Celulas esperadas:
   - clonar repositorio.
   - instalar dependencias.
   - instalar FFmpeg, se necessario.
   - configurar `.env`.
   - autenticar ngrok.
   - iniciar painel.
   - iniciar bot.

   Dificuldade: Media.

3. Garantir que tokens nao sejam commitados:
   - Discord token.
   - ngrok auth token.
   - API key do LLM.

   Dificuldade: Facil.

Pronto quando:

- Um usuario consegue abrir Colab, rodar as celulas e iniciar o projeto.
- O repositorio continua sendo a fonte do codigo.

## Fase 10 - Streaming e otimizacao

Objetivo: reduzir latencia e melhorar experiencia na call.

Tarefas:

1. Medir latencias:
   - captura de audio.
   - STT.
   - LLM.
   - TTS.
   - envio ao Discord.

   Dificuldade: Media.

2. Adicionar streaming no LLM:
   - receber tokens aos poucos.
   - acumular por frase.
   - enviar trechos para TTS.

   Dificuldade: Dificil.

3. Adicionar streaming/chunks no TTS:
   - avaliar XTTS-v2 direto.
   - avaliar RealtimeTTS.
   - tocar audio antes da frase inteira terminar.
   - Esta fase vem depois do MVP de TTS tradicional funcionando.

   Dificuldade: Critica.

4. Cache de falas comuns:
   - saudacoes.
   - frases curtas.
   - respostas de sistema.

   Dificuldade: Media.

5. Otimizar modelos:
   - STT `base` vs `small` vs `medium`.
   - TTS XTTS-v2 vs fallback.
   - LLM externo com resposta curta.

   Dificuldade: Media.

Pronto quando:

- O tempo entre fala do usuario e resposta do bot for aceitavel para call.
- O bot nao parece travado.
- O painel mostra metricas basicas.

## Fase 11 - Seguranca, privacidade e moderacao

Objetivo: evitar comportamentos ruins e dar controle ao usuario.

Tarefas:

1. Criar blacklist configuravel.

   Dificuldade: Facil.

2. Criar botao de emergencia:
   - mutar TTS.
   - sair da call.
   - pausar LLM.

   Dificuldade: Media.

3. Criar regras de memoria:
   - nao salvar informacoes sensiveis por padrao.
   - permitir apagar tudo.
   - permitir exportar/importar memorias.

   Dificuldade: Media.

4. Criar limites de resposta:
   - tamanho maximo.
   - timeout de LLM.
   - timeout de TTS.

   Dificuldade: Media.

5. Criar logs sem expor tokens.

   Dificuldade: Facil.

Pronto quando:

- Usuario consegue interromper o bot rapidamente.
- Memorias podem ser apagadas.
- Tokens nao aparecem em logs.

## Fase 12 - Refinamento da personalidade

Objetivo: tornar o bot mais natural como pessoa em call.

Tarefas:

1. Criar presets de personalidade:
   - calmo.
   - engracado.
   - sarcastico leve.
   - companheiro de gameplay.
   - assistente tecnico casual.

   Dificuldade: Facil.

2. Criar exemplos de dialogo por persona.

   Dificuldade: Media.

3. Criar ajuste de espontaneidade:
   - baixo: so responde quando chamado.
   - medio: responde a perguntas e algumas deixas.
   - alto: participa mais da call.

   Dificuldade: Media.

4. Criar avaliacao manual:
   - resposta foi natural?
   - falou demais?
   - interrompeu?
   - usou memoria corretamente?

   Dificuldade: Media.

Pronto quando:

- O bot parece menos um comando e mais um participante.
- O painel permite ajustar o estilo sem mexer no codigo.

## Ordem recomendada para trabalhar

Ordem mais segura:

1. Fase 0 - Base do repositorio.
2. Fase 1 - Configuracao e estado central.
3. Fase 2 - Discord voice.
4. Fase 4 - TTS em PT-BR com clonagem.
5. Fase 3 - STT em PT-BR.
6. Fase 5 - LLM e prompt builder.
7. Fase 6 - Pipeline completo.
8. Fase 7 - Painel.
9. Fase 8 - Memorias.
10. Fase 9 - Notebook launcher.
11. Fase 10 - Streaming e otimizacao.
12. Fase 11 - Seguranca e moderacao.
13. Fase 12 - Refinamento da personalidade.

## Primeira tarefa real recomendada

Criar a estrutura base do repositorio e um bot minimo com `py-cord` que:

- le token do Discord via `.env`;
- registra comandos slash;
- entra na call com `/join`;
- sai com `/leave`;
- responde `/status`;
- nao implementa IA ainda.

Dificuldade: Media.

Modelo recomendado: intermediario ou forte.

## Maiores riscos tecnicos

1. Captura de audio do Discord em tempo real.
   - Dificuldade: Critica.
   - Deve ser priorizada antes de investir muito em memoria ou painel.

2. Latencia STT + LLM + TTS.
   - Dificuldade: Critica.
   - Mitigacao: respostas curtas, LLM externo, VAD, modelos menores.

3. Colab reiniciar ou perder arquivos temporarios.
   - Dificuldade: Media.
   - Mitigacao: salvar configuracoes importantes no repo, Drive ou export.

4. XTTS-v2 consumir muita VRAM.
   - Dificuldade: Dificil.
   - Mitigacao: resposta curta, fallback Piper, LLM externo.

5. Bot ouvir a propria voz.
   - Dificuldade: Critica.
   - Mitigacao: ignorar audio enquanto `bot_speaking=True`, separar fontes por usuario, filtrar o proprio bot.

## Checklist de retomada em nova conversa

Ao resetar a conversa, pedir para o modelo ler:

1. `README.md`
2. `INSPIRACOES_NEURO.md`
3. `TECNOLOGIAS_RECOMENDADAS.md`
4. `ROADMAP.md`

Depois continuar a partir da fase atual.

Antes de editar codigo, o modelo deve:

- verificar estrutura atual do repo;
- checar arquivos ja existentes;
- nao sobrescrever alteracoes do usuario;
- implementar uma etapa pequena por vez;
- registrar bloqueios tecnicos no README ou em arquivo de notas.

## Definicao de MVP

O MVP esta pronto quando:

- O notebook do Colab importa o repositorio.
- O painel abre via ngrok.
- O bot entra em uma call do Discord.
- O bot recebe audio de pelo menos um usuario.
- O bot transcreve PT-BR.
- O bot gera resposta curta em PT-BR.
- O bot fala na call com XTTS-v2 ou fallback.
- O usuario consegue configurar persona basica pelo painel.
- Existe memoria simples editavel.

## Nao fazer no inicio

- Nao criar sistema visual complexo.
- Nao implementar avatar VTuber.
- Nao rodar LLM local pesado no Colab no MVP.
- Nao comecar por memoria vetorial.
- Nao comecar por streaming TTS.
- Nao depender de diarizacao pesada.
- Nao colocar segredos no repositorio.

## Comandos e arquivos esperados futuramente

Arquivos principais esperados:

```text
src/bot_discord_colab/main.py
src/bot_discord_colab/config.py
src/bot_discord_colab/state.py
src/bot_discord_colab/discord_voice.py
src/bot_discord_colab/stt.py
src/bot_discord_colab/tts.py
src/bot_discord_colab/llm.py
src/bot_discord_colab/prompt_builder.py
src/bot_discord_colab/memory.py
src/bot_discord_colab/panel.py
```

Comandos esperados:

```bash
pip install -r requirements.txt
python -m bot_discord_colab.main
```

No Colab, o ideal sera chamar uma funcao:

```python
from bot_discord_colab.main import run
run()
```
