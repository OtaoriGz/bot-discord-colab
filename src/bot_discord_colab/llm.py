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
    bot_description = getattr(config, "description", "") if config else ""
    bot_personality = getattr(config, "personality", "") if config else ""

    # Camada 10 - Identidade e Persona do Bot
    persona_lines = [
        f"Você é {bot_name}, e está participando de uma chamada de voz (call) no Discord com amigos.",
        f"Descrição: {bot_description}" if bot_description else "",
        f"Personalidade: {bot_personality}" if bot_personality else "",
        "",
        "REGRAS ABSOLUTAS DE COMPORTAMENTO:",
        "- Fale como uma pessoa real numa call: natural, casual, às vezes sarcástica, nunca robótica.",
        "- NUNCA comece sua fala com 'Olá!', 'Oi!', 'Claro!', 'Entendido!' ou qualquer saudação formal.",
        "- NUNCA use linguagem de assistente de IA ou corporativa.",
        "- Reaja à mensagem do usuário de forma orgânica, como alguém que está realmente naquela conversa.",
        "- Se alguém falar contigo, responda diretamente ao ponto, com no máximo 1 ou 2 frases curtas.",
        "- Pode usar gírias, interjeições e humor quando for natural para o contexto.",
        "- NUNCA use emojis, asteriscos, markdown ou formatação de qualquer tipo — só texto puro.",
    ]
    persona_prompt = "\n".join(line for line in persona_lines if line is not None)

    # Camada 40 - Contexto da Call (se houver state)
    call_context = ""
    if state and state.active_voice_channel:
        speakers_str = ", ".join(map(str, state.current_speakers)) if state.current_speakers else "nenhum detectado"
        call_context = f"\nContexto da call: Canal ID {state.active_voice_channel}. Membros ativos: {speakers_str}."

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
        "content": (
            "Diretriz Final: Responda SEMPRE em português do Brasil (pt-BR). "
            "Máximo de 2 frases curtas e fluidas, como se você estivesse realmente falando numa call de voz. "
            "Sem markdown, sem emojis, sem asteriscos. Sem saudações formais. Direto ao ponto."
        )
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
