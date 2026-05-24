# Bot Discord Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/OtaoriGz/bot-discord-colab/blob/main/notebooks/bot_discord_colab_runner.ipynb)

## Contexto do projeto

Este projeto tem como objetivo criar um bot para Discord que rode no Google Colab e seja configurado por um painel de controle acessado via ngrok.

A ideia principal e que o bot funcione como uma especie de pessoa dentro do Discord. No inicio, o foco sera na experiencia em chamadas de voz: o bot podera entrar em uma call, ouvir os membros, guardar informacoes relevantes, gerenciar memorias e responder por voz usando TTS.

## Objetivo inicial

Construir uma primeira versao funcional focada em chamadas de voz no Discord, com:

- Entrada do bot em canais de voz.
- Captura ou processamento do audio dos membros.
- Armazenamento de informacoes importantes durante as conversas.
- Sistema de memorias para manter contexto entre interacoes.
- Respostas por voz usando TTS.
- Painel de controle web rodando no Colab e exposto via ngrok.

## Painel de controle

O painel de controle sera usado para configurar o comportamento e a identidade do bot sem precisar alterar o codigo manualmente.

Configuracoes previstas:

- Foto/avatar do bot.
- Nome exibido.
- Descricao.
- Personalidade.
- Volume da voz.
- Configuracoes tecnicas da call.
- Configuracoes de memoria.
- Configuracoes de TTS.
- Outras opcoes futuras conforme o projeto evoluir.

## Workaround Protocolo DAVE (Voz Multi-Acesso)

**Importante:** O Discord recentemente ativou o protocolo DAVE (End-to-End Encryption) que quebrou temporariamente todas as bibliotecas de captação de áudio nativas (como `py-cord[voice]`).
**Como workaround**, este projeto levanta um pequeno painel web (servido via Ngrok e FastAPI).
Esse painel possui duas rotas:
1. **/user**: Rota aberta para visitantes/usuários segurarem para enviar áudio ao Bot.
2. **/admin**: Rota fechada com senha (configurada no Colab via variável `ADMIN_PASSWORD`) onde futuramente configuraremos a memória/temperamento do bot, e que já permite que você envie áudios diretamente com o nome de Admin.

O usuário acessa o respectivo link, clica em "Segure para Falar", e o áudio é processado via Faster-Whisper + LLM + XTTS-v2/gTTS, com a resposta sendo tocada diretamente na call do Discord.

## Conceito do bot

O bot deve agir como um participante da chamada, nao apenas como um comando automatico. Ele deve conseguir:

- Ouvir o que esta acontecendo na call.
- Entender e resumir informacoes importantes.
- Lembrar dados relevantes para conversas futuras.
- Responder com voz.
- Ter uma personalidade configuravel.
- Ser ajustado pelo painel de controle.

## Arquitetura prevista

A arquitetura inicial deve considerar:

- Google Colab como ambiente de execucao.
- Discord API para conexao com o servidor e chamadas.
- ngrok para expor o painel web.
- Um painel web simples para configuracao.
- Modulo de memoria para armazenar contexto e informacoes.
- Modulo de audio para entrada e saida de voz.
- Modulo de TTS para fala do bot.

## Escopo atual

Por enquanto, o projeto deve priorizar a parte de chamada de voz. Outros recursos do Discord, como comandos de texto, automacoes de servidor ou moderacao, podem ser considerados depois.

## Observacoes

Este README serve como contexto inicial do projeto. A implementacao tecnica, bibliotecas escolhidas e organizacao dos arquivos serao definidas nas proximas etapas.
