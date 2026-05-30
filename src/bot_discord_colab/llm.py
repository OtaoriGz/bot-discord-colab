import os
import requests
import logging
from src.bot_discord_colab.memory import memory_manager

logger = logging.getLogger(__name__)

def generate_reply(text: str, config=None, state=None) -> str:
    """Usa a API externa via LLM para gerar uma fala natural"""
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    
    if not api_key:
        return "Desculpe, mas minha chave de inteligência não está configurada para eu responder adequadamente."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    bot_name = config.name if config else "Neuro"
    bot_description = getattr(config, "description", "") if config else ""
    bot_personality = getattr(config, "personality", "") if config else ""

    # Camada 10 - Identidade e Persona do Bot
    persona_prompt = (
        f"Você é {bot_name}. {bot_description}\n"
        f"Instruções de Personalidade:\n{bot_personality}\n\n"
        "Você deve falar e reagir de forma SUPER curta, casual, orgânica e humanizada. "
        "Não use emojis, markdown ou formatos difíceis de serem falados, pois a sua resposta será lida pelo seu clone de voz."
    )

    # Camada 40 - Contexto da Call (se houver state)
    call_context = ""
    if state and state.active_voice_channel:
        speakers_str = ", ".join(map(str, state.current_speakers)) if state.current_speakers else "nenhum detectado"
        call_context = f"\nContexto atual da chamada: Canal ID {state.active_voice_channel} ativo. Membros ativos: {speakers_str}."

    # Camada 60 - Memórias Recuperadas (Busca Semântica baseada na mensagem atual)
    memories_context = ""
    try:
        memories = memory_manager.recall_memories(text, limit=3)
        if memories:
            facts = "\n".join([f"- {mem['text']}" for mem in memories])
            memories_context = f"\n\n[MEMÓRIAS RELEVANTES DO PASSADO / CONTEXTO]\n{facts}"
    except Exception as e:
        logger.error(f"Erro ao recuperar memórias no LLM: {e}")

    system_prompt = f"{persona_prompt}{call_context}{memories_context}"
    history_messages = [{"role": "system", "content": system_prompt}]
    
    # Camada 80 - Histórico Recente de Conversas
    if state:
        combined = []
        for t in state.recent_transcripts:
            combined.append((t.timestamp, {"role": "user", "content": f"{t.username}: {t.text}"}))
        for r in state.recent_responses:
            combined.append((r.timestamp, {"role": "assistant", "content": r.text}))
            
        combined.sort(key=lambda x: x[0])
        history_messages.extend([item[1] for item in combined[-8:]])
        
    # Camada 100 - Nova Mensagem/Fala do Usuário
    history_messages.append({"role": "user", "content": text})

    # Camada 120 - Diretriz Final de Escrita e Idioma
    history_messages.append({
        "role": "system",
        "content": "Diretriz Final: Responda sempre em português do Brasil (pt-BR). Limite estritamente sua resposta a uma fala muito curta, contendo no máximo 1 ou 2 frases curtas e fluidas. Não use markdown, asteriscos ou emojis."
    })

    payload = {
        "model": model,
        "messages": history_messages,
        "max_tokens": 150,
        "temperature": 0.8
    }

    try:
        resp = requests.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        reply_text = resp.json()["choices"][0]["message"]["content"]
        return reply_text.strip()
    except Exception as e:
        print(f"Erro LLM: {str(e)}")
        return "Ih, acho que me perdi no pensamento agora."

def generate_reply_stream(text: str, config=None, state=None):
    """Usa a API externa com stream=True e gera frases/sentenças curtas completas à medida que saem do LLM."""
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    
    if not api_key:
        yield "Desculpe, mas minha chave de inteligência não está configurada."
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    bot_name = config.name if config else "Neuro"
    bot_description = getattr(config, "description", "") if config else ""
    bot_personality = getattr(config, "personality", "") if config else ""

    persona_prompt = (
        f"Você é {bot_name}. {bot_description}\n"
        f"Instruções de Personalidade:\n{bot_personality}\n\n"
        "Você deve falar e reagir de forma SUPER curta, casual, orgânica e humanizada. "
        "Não use emojis, markdown ou formatos difíceis de serem falados, pois a sua resposta será lida pelo seu clone de voz."
    )

    call_context = ""
    if state and state.active_voice_channel:
        speakers_str = ", ".join(map(str, state.current_speakers)) if state.current_speakers else "nenhum detectado"
        call_context = f"\nContexto atual da chamada: Canal ID {state.active_voice_channel} ativo. Membros ativos: {speakers_str}."

    memories_context = ""
    try:
        memories = memory_manager.recall_memories(text, limit=3)
        if memories:
            facts = "\n".join([f"- {mem['text']}" for mem in memories])
            memories_context = f"\n\n[MEMÓRIAS RELEVANTES DO PASSADO / CONTEXTO]\n{facts}"
    except Exception as e:
        logger.error(f"Erro ao recuperar memórias no LLM: {e}")

    system_prompt = f"{persona_prompt}{call_context}{memories_context}"
    history_messages = [{"role": "system", "content": system_prompt}]
    
    if state:
        combined = []
        for t in state.recent_transcripts:
            combined.append((t.timestamp, {"role": "user", "content": f"{t.username}: {t.text}"}))
        for r in state.recent_responses:
            combined.append((r.timestamp, {"role": "assistant", "content": r.text}))
            
        combined.sort(key=lambda x: x[0])
        history_messages.extend([item[1] for item in combined[-8:]])
        
    history_messages.append({"role": "user", "content": text})
    history_messages.append({
        "role": "system",
        "content": "Diretriz Final: Responda sempre em português do Brasil (pt-BR). Limite estritamente sua resposta a uma fala muito curta, contendo no máximo 1 ou 2 frases curtas e fluidas. Não use markdown, asteriscos ou emojis."
    })

    payload = {
        "model": model,
        "messages": history_messages,
        "max_tokens": 150,
        "temperature": 0.8,
        "stream": True
    }

    try:
        resp = requests.post(f"{base_url}/chat/completions", json=payload, headers=headers, stream=True, timeout=15)
        resp.raise_for_status()
        
        current_sentence = ""
        # Pontuações que marcam o final de uma oração/frase
        sentence_enders = {".", "!", "?", "\n", ";"}
        
        for line in resp.iter_lines():
            if not line:
                continue
                
            decoded_line = line.decode("utf-8").strip()
            if decoded_line.startswith("data: "):
                data_str = decoded_line[6:]
                if data_str == "[DONE]":
                    break
                    
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    
                    if content:
                        current_sentence += content
                        # Se encontrou um pontuador de fim de frase, envia o bloco gerado até agora
                        if any(ender in content for ender in sentence_enders):
                            # Limpa emojis e markdown antes de enviar
                            clean = current_sentence.replace("*", "").replace("`", "").strip()
                            if len(clean) > 2:
                                yield clean
                                current_sentence = ""
                except Exception:
                    continue
                    
        # Retorna o que restou caso não termine com pontuação explícita
        if current_sentence.strip():
            clean = current_sentence.replace("*", "").replace("`", "").strip()
            if len(clean) > 2:
                yield clean
                
    except Exception as e:
        logger.error(f"Erro no streaming do LLM: {e}")
        yield "Ih, acho que me perdi no pensamento agora."

def reflect_on_conversation(history_entries: List[str]) -> List[str]:
    """Usa o LLM de forma síncrona/assíncrona para extrair novos fatos/memórias do histórico recente"""
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
    
    if not api_key or not history_entries:
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    conversation_text = "\n".join(history_entries)
    
    prompt = (
        "Analise o seguinte trecho de conversa do Discord e extraia no máximo de 1 a 3 fatos importantes, "
        "preferências, nomes de usuários ou interações relevantes de longo prazo que devem ser lembrados pelo bot.\n"
        "Ignore brincadeiras ou falas vazias. Retorne APENAS uma lista contendo os fatos objetivos formatados por linhas simples, "
        "sem numeração, sem marcadores de markdown, sem tags, sem introduções. Exemplo:\n"
        "Pedro revelou que tem um cachorro chamado Thor\n"
        "Lucas disse que programa em Go no trabalho\n\n"
        "Histórico de conversa:\n"
        f"{conversation_text}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Você é um assistente analítico encarregado de resumir e extrair fatos importantes de diálogos para a memória de longo prazo do bot."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.3
    }

    try:
        resp = requests.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=12)
        resp.raise_for_status()
        result_text = resp.json()["choices"][0]["message"]["content"].strip()
        
        facts = []
        for line in result_text.split("\n"):
            line_cleaned = line.strip()
            # Remove marcadores comuns caso o modelo desobedeça
            for prefix in ["- ", "* ", "1. ", "2. ", "3. "]:
                if line_cleaned.startswith(prefix):
                    line_cleaned = line_cleaned[len(prefix):]
            if line_cleaned and len(line_cleaned) > 5:
                facts.append(line_cleaned)
        return facts
    except Exception as e:
        logger.error(f"Erro na reflexão do LLM: {e}")
        return []

