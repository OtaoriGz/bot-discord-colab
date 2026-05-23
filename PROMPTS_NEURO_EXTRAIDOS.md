# Prompts extraidos do Neuro

Este arquivo organiza os prompts e injecoes de prompt que aparecem no projeto `Neuro`, para servir como referencia do que pode ser reaproveitado no nosso bot.

Nao e uma copia literal completa do projeto original. A ideia aqui e separar o papel de cada prompt e registrar a estrutura usada no runtime.

## Visao geral do fluxo

No Neuro, o prompt final nao vem de um unico texto fixo. Ele e montado por camadas:

- prompt base de personalidade;
- historico recente da conversa;
- memorias recuperadas;
- prompt customizado temporario;
- possiveis injecoes de plugins/modulos;
- instrucao final para resposta.

O sistema combina essas partes por prioridade, do menor para o maior valor.

## 1. Prompt base da personagem

Fonte principal:

- [Neuro.yaml](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/Neuro.yaml)
- [constants.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/constants.py)

O prompt base define:

- nome da personagem;
- personalidade;
- backstory;
- relacao com o criador;
- exemplo de conversa;
- estilo de fala curto;
- comportamento em stream/chat;
- regra para trocar de assunto se a conversa travar.

Resumo funcional:

- responder como uma vtuber de voz com personalidade bem marcada;
- manter respostas curtas, normalmente em uma frase;
- mudar de assunto se a outra pessoa nao continuar a conversa;
- reagir a chat e a fala das pessoas ao redor;
- parecer natural, rapida e conversacional.

## 2. Prompt de memoria

Fonte principal:

- [constants.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/constants.py)
- [modules/memory.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/modules/memory.py)

O prompt de memoria e usado para transformar trechos da conversa em memorias reutilizaveis.

Comportamento:

- recebe o historico recente;
- pede ao modelo que extraia memorias de alto nivel;
- gera 3 pares de pergunta e resposta;
- usa separador especial `{qa}`;
- retorna apenas o conteudo util, sem explicacao extra.

Resumo funcional:

- o bot faz uma especie de reflexao periodica;
- o que for importante vira memoria persistente;
- depois essas memorias sao injetadas no prompt principal.

## 3. Prompt de memoria recuperada

Fonte principal:

- [modules/memory.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/modules/memory.py)

Antes de responder, o Neuro busca memorias relevantes no banco vetorial e injeta um bloco de contexto no prompt.

O formato geral e:

- introduzir que a IA "conhece" certas coisas;
- listar memorias recuperadas;
- fechar a secao de conhecimento;
- seguir para a resposta.

Resumo funcional:

- memorias relevantes entram antes da resposta final;
- o bot usa contexto persistente para parecer consistente;
- o que nao e relevante nao entra.

## 4. Prompt customizado do painel

Fonte principal:

- [modules/customPrompt.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/modules/customPrompt.py)
- [socketioServer.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/socketioServer.py)

Esse prompt pode ser alterado dinamicamente pelo painel.

Ele serve para:

- injetar uma instruicao temporaria;
- mudar prioridade do bloco;
- sobrescrever ou complementar a persona por um periodo;
- testar comportamentos sem alterar o codigo.

Resumo funcional:

- e um prompt manual e temporario;
- vem do painel de controle;
- fica acima de varios blocos de contexto por prioridade.

## 5. Prompt de decisao de fala

Fonte principal:

- [prompter.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/prompter.py)

O Neuro nao pergunta ao modelo o tempo todo. Existe uma logica que decide quando gerar resposta.

Regras principais:

- nao promptar se STT ou TTS nao estiverem prontos;
- nao promptar enquanto alguem estiver falando;
- nao promptar enquanto a IA estiver pensando ou falando;
- promptar se houver nova mensagem humana;
- promptar se houver mensagens pendentes de chat;
- promptar depois de um tempo de silencio.

Resumo funcional:

- o bot fala no timing certo;
- o prompt so e enviado quando vale a pena;
- o modelo nao fica sendo acionado o tempo inteiro.

## 6. Prompt multimodal

Fonte principal:

- [modules/multimodal.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/modules/multimodal.py)

O Neuro tem uma estrategia para decidir se deve usar LLM de texto ou de imagem.

Resumo funcional:

- se o modo multimodal estiver ativo e a estrategia permitir, usa o modelo de imagem;
- caso contrario, usa o modelo de texto;
- isso e controlado por configuracao de runtime.

## 7. Prompt de blacklist

Fonte principal:

- [llmWrappers/abstractLLMWrapper.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/llmWrappers/abstractLLMWrapper.py)
- [llmWrappers/llmState.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/llmWrappers/llmState.py)

Nao e exatamente um prompt, mas e uma regra de filtragem que afeta a saida final.

Resumo funcional:

- certas palavras sao bloqueadas por blacklist;
- a resposta final pode ser filtrada antes de tocar no TTS;
- a blacklist pode ser alterada pelo painel.

## 8. Estrutura de montagem do prompt

Fonte principal:

- [llmWrappers/abstractLLMWrapper.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/llmWrappers/abstractLLMWrapper.py)
- [modules/injection.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/modules/injection.py)

O Neuro usa injecoes com prioridade. A ordem geral e:

- prioridade baixa para prompt base;
- prioridade media para historico e memoria;
- prioridade alta para chat recente e injecoes especificas;
- prioridade ainda mais alta para prompt manual do painel;
- texto final para abrir a resposta da IA.

Resumo funcional:

- o prompt final e uma composicao de blocos;
- o sistema pode adicionar e remover contexto sem reescrever tudo;
- cada modulo contribui com seu proprio pedaco de prompt.

## O que isso significa para o nosso projeto

Para o bot do Discord, o melhor caminho e copiar a filosofia, nao o texto literal:

- prompt base de persona em YAML;
- memoria separada do prompt principal;
- prompt temporario do painel;
- decisao de fala por estado;
- selecao de modelo por configuracao;
- montagem por prioridade.

## Arquivos do Neuro que concentram os prompts

- [Neuro.yaml](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/Neuro.yaml)
- [constants.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/constants.py)
- [prompter.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/prompter.py)
- [modules/memory.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/modules/memory.py)
- [modules/customPrompt.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/modules/customPrompt.py)
- [modules/multimodal.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/modules/multimodal.py)
- [llmWrappers/abstractLLMWrapper.py](C:/Users/pedro/OneDrive/Documentos/GitHub/Neuro/llmWrappers/abstractLLMWrapper.py)

## Prioridade para replicar no nosso bot

1. Prompt base da personalidade.
2. Prompt de memoria.
3. Prompt customizado do painel.
4. Logica de decisao de fala.
5. Montagem por prioridades.
