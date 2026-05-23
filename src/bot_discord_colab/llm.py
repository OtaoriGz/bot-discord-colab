import os
import requests

def generate_reply(text: str) -> str:
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

    # Contexto base (simplificado para o MVP)
    system_prompt = (
        "Você é Neuro, uma pessoa participando de uma chamada de voz (call) no Discord conversando com amigos. "
        "Você deve falar e reagir de forma SUPER curta, casual, orgânica e humanizada. "
        "Responda sempre em português do Brasil (pt-BR). Tente limitar a resposta a 1 ou no máximo 2 frases fluidas. "
        "Não use emojis, markdown ou formatos difíceis de serem falados, pois a sua resposta será lida pelo seu clone de vóz."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
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