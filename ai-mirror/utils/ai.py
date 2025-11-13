from openai import OpenAI
import os

class AIResponder:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            print("[AI] No API key found in environment — using offline fallback.")
        else:
            print(f"[AI] Connected with key prefix: {key[:10]}...")
        self.client = OpenAI(api_key=key)
        print(f"[AI] Model: {self.model}")

    def reply(self, user_text: str, context: dict | None = None) -> str | None:
        sys_prompt = (
            "You are a calm, concise AI mirror assistant. "
            "Respond in 1–2 short sentences with helpful, actionable guidance. "
            "Avoid filler. Use the context if relevant."
        )
        ctx_line = ""
        if context:
            try:
                parts = [f"{k}={v}" for k, v in context.items() if v is not None]
                if parts:
                    ctx_line = "Context: " + ", ".join(parts) + "\n"
            except Exception:
                pass
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.5,
                max_tokens=80,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": ctx_line + f"User: {user_text}"},
                ],
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print("[AI] Error:", repr(e))
            return None
