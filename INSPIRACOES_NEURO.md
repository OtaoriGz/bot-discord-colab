# Inspiracoes do projeto Neuro

Este arquivo resume ideias do projeto `Neuro` que podem inspirar o bot de Discord deste repositorio. A intencao nao e copiar o projeto inteiro, mas aproveitar tecnicas boas para um bot de voz com personalidade, memoria e painel de controle.

## Ideias principais aproveitaveis

### 1. Persona configuravel em arquivo

O projeto Neuro usa um arquivo de configuracao para definir nome, saudacao, contexto, personalidade e exemplo de conversa.

Para este bot, podemos seguir uma ideia parecida:

- `name`: nome do bot.
- `avatar`: imagem/foto configurada no painel.
- `description`: descricao curta.
- `personality`: lista de tracos de personalidade.
- `backstory`: contexto opcional da personagem.
- `speaking_style`: regras de como responder.
- `example_dialogue`: exemplos de conversa para guiar o modelo.

Isso combina bem com o painel de controle, porque o usuario poderia editar a personalidade sem mexer no codigo.

## Prompt base inspirado

Um prompt inicial para o nosso bot poderia seguir este formato:

```text
Voce e {bot_name}, uma presenca de voz dentro de uma chamada do Discord.

Identidade:
- Nome: {bot_name}
- Descricao: {description}
- Personalidade: {personality}
- Relacao com os membros: voce participa da call como uma pessoa do grupo, nao como um assistente formal.

Comportamento:
- Responda de forma natural, curta e conversacional.
- Evite monologos longos durante a call.
- Se ninguem responder uma pergunta, mude de assunto naturalmente.
- Quando houver varias pessoas falando, considere o contexto recente antes de responder.
- Nao invente mensagens ou falas de membros que nao aconteceram.
- Use as memorias disponiveis apenas quando forem relevantes.
- Se nao tiver certeza de algo, fale de forma simples e honesta.

Contexto atual da chamada:
{call_context}

Memorias relevantes:
{memories}

Historico recente:
{recent_history}

Agora responda como {bot_name}, em apenas uma fala curta.
```

## Tecnicas de prompt

### Prompt por camadas

O Neuro separa o prompt em partes chamadas de "injections", cada uma com uma prioridade. A ideia e montar o prompt final juntando blocos como:

- Prompt de sistema/persona.
- Historico recente.
- Mensagens externas ou eventos.
- Memorias recuperadas.
- Prompt customizado temporario.
- Instrucao final de resposta.

Para o nosso bot, isso pode virar:

- Prioridade baixa: identidade fixa do bot.
- Prioridade media: historico da call.
- Prioridade alta: memorias relevantes.
- Prioridade mais alta: configuracao temporaria do painel.
- Final: instrucao de resposta curta em voz.

Essa arquitetura facilita adicionar recursos depois sem reescrever toda a logica de prompt.

### Exemplo de prioridades

```text
10  - Persona fixa
40  - Configuracoes tecnicas da chamada
60  - Memorias relevantes
80  - Historico recente da call
100 - Prompt customizado do painel
120 - Instrucao final de resposta
```

## Sistema de memoria

O Neuro usa uma tecnica de memoria baseada em:

- Historico recente de conversa.
- Banco vetorial para buscar memorias semanticamente parecidas.
- Injecao das memorias relevantes no prompt.
- Reflexao periodica para transformar conversas em novas memorias.

Para o nosso bot, podemos dividir memoria em tipos:

- `perfil_membro`: informacoes sobre pessoas do servidor.
- `preferencia`: gostos, apelidos, horarios, temas preferidos.
- `fato_importante`: informacoes que o bot deve lembrar.
- `resumo_call`: resumo de uma chamada.
- `memoria_temporaria`: contexto util apenas por pouco tempo.

## Prompt de reflexao para criar memorias

Inspirado na tecnica de reflexao do Neuro:

```text
Com base apenas na conversa abaixo, extraia ate 3 memorias uteis para interacoes futuras.

Regras:
- Cada memoria deve ser curta.
- Nao salve informacoes sensiveis desnecessarias.
- Nao invente fatos.
- Se nao houver nada util, responda: SEM_MEMORIAS.
- Inclua o nome do membro quando a informacao for sobre alguem.

Conversa:
{conversation_chunk}

Formato de saida:
- tipo: ...
  pessoa: ...
  memoria: ...
```

## Recuperacao de memorias

Antes de responder, o bot pode montar uma consulta usando:

- Ultimas falas transcritas.
- Nome dos membros ativos na call.
- Topico detectado.
- Pergunta feita ao bot.

Depois busca as memorias mais relevantes e injeta no prompt.

Exemplo:

```text
{bot_name} sabe estas coisas relevantes:
- Pedro prefere respostas diretas quando esta programando.
- Joao gosta de ser chamado pelo apelido Jota.
- Na ultima call, o grupo estava planejando um bot de Discord com painel.
Fim das memorias relevantes.
```

## Ciclo de fala e paciencia

O Neuro tem uma logica de "paciencia": a IA fala quando existe uma nova mensagem, quando ha mensagens pendentes ou quando passa certo tempo sem ninguem falar.

Para chamada do Discord, isso pode virar:

- Nao responder enquanto alguem esta falando.
- Nao interromper o proprio TTS.
- Responder quando alguem chamar o bot pelo nome.
- Responder quando uma pergunta parecer direcionada ao bot.
- Falar espontaneamente apenas depois de um tempo de silencio.
- Permitir configurar esse tempo no painel.

Configuracoes possiveis:

- `auto_reply_enabled`: responder automaticamente.
- `wake_word`: nome ou apelido que ativa o bot.
- `silence_patience_seconds`: tempo de silencio antes de falar sozinho.
- `interruptions_enabled`: se o bot pode ser interrompido.
- `max_reply_seconds`: limite aproximado de fala.

## Estados compartilhados

O Neuro usa um objeto central de sinais para coordenar STT, TTS, LLM e painel.

Estados uteis para o nosso bot:

- `human_speaking`: alguem esta falando.
- `bot_thinking`: bot esta gerando resposta.
- `bot_speaking`: bot esta falando via TTS.
- `stt_ready`: transcricao pronta.
- `tts_ready`: voz pronta.
- `new_transcript`: ha fala nova para processar.
- `last_message_time`: ultima fala relevante.
- `active_voice_channel`: canal de voz atual.
- `current_speakers`: membros detectados falando.

Isso ajuda o painel a mostrar o que esta acontecendo em tempo real.

## Painel de controle

O Neuro usa Socket.IO para enviar eventos entre backend e frontend. Isso e util porque o painel precisa tanto mandar comandos quanto receber atualizacoes ao vivo.

Controles que podemos adaptar:

- Ativar/desativar LLM.
- Ativar/desativar STT.
- Ativar/desativar TTS.
- Cancelar proxima resposta.
- Interromper fala atual.
- Limpar historico recente.
- Criar memoria manual.
- Editar ou apagar memoria.
- Ajustar prompt customizado.
- Ver prompt final montado.
- Ver transcricao recente.
- Ver status da call.

## Audio, STT e TTS

O Neuro separa entrada de voz, saida de voz e geracao de texto em modulos diferentes.

Para o nosso bot, a separacao ideal seria:

- `discord_voice`: conecta na call, recebe e envia audio.
- `stt`: transforma fala em texto.
- `llm`: decide a resposta.
- `memory`: busca e salva memorias.
- `tts`: transforma resposta em audio.
- `control_panel`: configura e monitora tudo.

Essa divisao deixa mais facil trocar tecnologias depois.

## Tecnicas para respostas naturais em call

Regras importantes para o bot parecer uma pessoa em chamada:

- Falar pouco e com timing bom.
- Evitar responder tudo se a conversa estiver muito rapida.
- Usar nomes dos membros quando fizer sentido.
- Nao narrar o que esta fazendo tecnicamente.
- Nao soar como painel de atendimento.
- Ter opinioes/persona, mas respeitar limites configurados.
- Manter memoria de preferencias e contexto do grupo.

## Cuidados importantes

O projeto Neuro comenta que receber audio de voz do Discord pode ser uma parte delicada dependendo da biblioteca usada. Para este projeto, precisamos validar bem a biblioteca de Discord escolhida antes de fechar a arquitetura.

Pontos para testar cedo:

- Bot consegue entrar em canal de voz no Colab?
- Bot consegue receber audio dos membros?
- Bot consegue identificar quem falou?
- Bot consegue enviar audio TTS para a call?
- ngrok consegue expor o painel sem quebrar websocket ou Socket.IO?
- O Colab aguenta STT, LLM e TTS ao mesmo tempo?

## Possivel estrutura inicial do projeto

```text
bot-discord-colab/
  README.md
  INSPIRACOES_NEURO.md
  config/
    bot_profile.yaml
    settings.yaml
  src/
    main.py
    discord_voice.py
    control_panel.py
    prompt_builder.py
    memory.py
    stt.py
    tts.py
    state.py
  memories/
    memory_init.json
  notebooks/
    run_bot_colab.ipynb
```

## Primeiro MVP sugerido

1. Criar configuracao da persona em YAML.
2. Criar painel simples no Colab via Flask/FastAPI.
3. Expor painel pelo ngrok.
4. Conectar bot ao Discord.
5. Fazer bot entrar e sair de call.
6. Testar envio de audio TTS para a call.
7. Testar captura/transcricao de audio.
8. Montar prompt com persona, historico e resposta curta.
9. Adicionar memoria simples em JSON.
10. Evoluir para memoria vetorial depois.

## O que vale copiar como filosofia

- Separar cada responsabilidade em modulo.
- Usar um estado central para sincronizar audio, IA e painel.
- Construir prompt final por blocos.
- Dar prioridade a respostas curtas.
- Ter controles manuais no painel para moderar o bot.
- Tratar memoria como parte central da personalidade.
- Criar uma persona configuravel, nao fixa no codigo.
