import os
import requests

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

    # Camada 10 - Identidade e Persona do Bot
    persona_prompt = (
        f"Você é {bot_name}, uma pessoa participando de uma chamada de voz (call) no Discord conversando com amigos. "
        "Você deve falar e reagir de forma SUPER curta, casual, orgânica e humanizada. "
        "Não use emojis, markdown ou formatos difíceis de serem falados, pois a sua resposta será lida pelo seu clone de voz."
    )

    # Camada 40 - Contexto da Call (se houver state)
    call_context = ""
    if state and state.active_voice_channel:
        speakers_str = ", ".join(map(str, state.current_speakers)) if state.current_speakers else "nenhum detectado"
        call_context = f"\nContexto atual da chamada: Canal ID {state.active_voice_channel} ativo. Membros ativos: {speakers_str}."

    system_prompt = f"{persona_prompt}{call_context}"
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
