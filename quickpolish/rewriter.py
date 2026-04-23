import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

MODES = ["natural", "professional", "shorter"]

SYSTEM_PROMPT = """You are a text rewriter. The user will give you text that may be in English, Chinese, or a mix of both.

Your job: understand the intended meaning and express it in natural American English.

Rules:
- Always output English only.
- Do not translate literally. Understand the intent and express it the way a native speaker would.
- Do not add meaning that wasn't there.
- Do not sound like AI. No "Certainly!", no "I hope this helps", no filler.
- Never use em dashes (—) or en dashes (–) anywhere in the output. Use a comma, period, or parentheses instead. Regular hyphens in compound words like "well-known" are fine.
- Return ONLY the rewritten text, nothing else. No quotes, no explanation."""

USER_PROMPTS = {
    "natural": (
        "Rewrite this in casual, natural American English, the way you'd text a friend. "
        "Keep it chill and real.\n\nText: {text}"
    ),
    "professional": (
        "Rewrite this for a professional email. Sound confident, direct, and warm, like a real person, not a robot. "
        "No corporate filler: no 'I hope this email finds you well', no 'please don't hesitate to reach out', "
        "no 'as per my previous email'.\n\nText: {text}"
    ),
    "shorter": (
        "Rewrite this in natural American English, then trim it down. "
        "Keep the meaning and tone. Remove redundancy without losing the point.\n\nText: {text}"
    ),
}


# Matches em dash / en dash / horizontal bar, optionally surrounded by spaces.
# We leave regular ASCII hyphens ("-") alone so compound words like
# "well-known" aren't destroyed.
_DASH_RE = re.compile(r"\s*[\u2014\u2013\u2015]\s*")


def strip_ai_dashes(text: str) -> str:
    """Replace em/en dashes with a comma+space; collapse accidental doubles."""
    if not text:
        return text
    cleaned = _DASH_RE.sub(", ", text)
    # Avoid ", ," / " , " artifacts if a dash was adjacent to existing punctuation.
    cleaned = re.sub(r"\s+,", ",", cleaned)
    cleaned = re.sub(r",\s*,", ",", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


class Rewriter:
    def __init__(self, client: OpenAI = None, model: str = "gpt-4o"):
        self._client = client
        self._model = model

    def _call_one(self, mode: str, text: str) -> tuple[str, str]:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPTS[mode].format(text=text)},
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            content = resp.choices[0].message.content.strip()
            return mode, strip_ai_dashes(content)
        except Exception as e:
            return mode, f"[error: {e}]"

    def rewrite_all(self, text: str) -> dict[str, str]:
        results = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(self._call_one, mode, text): mode for mode in MODES}
            for future in as_completed(futures):
                mode, result = future.result()
                results[mode] = result
        return results
