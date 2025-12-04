# llm_client.py
import os
import json
import logging
from typing import Dict, Any, List

from dotenv import load_dotenv   # <--- NEU

import requests
from openai import OpenAI
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# .env laden (aus Projekt-Root)
load_dotenv()  # <--- NEU

# ---- OpenAI / GPT Client ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

_openai_client = None
if OPENAI_API_KEY:
    _openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    logger.warning("OPENAI_API_KEY not set. GPT-based functions will fail.")


# ---- Local LLM Client (Ollama / NIM / whatever) ----

LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/api/generate")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3")


def _call_local_llm(prompt: str, model: str = None) -> str:
    """
    Minimalistischer Wrapper um dein lokales LLM.
    Erwartet ein Ollama-kompatibles /generate-Endpoint.
    """
    model = model or LOCAL_LLM_MODEL
    try:
        resp = requests.post(
            LOCAL_LLM_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        # Ollama: 'response' enthält den Text
        text = data.get("response") or data.get("text") or ""
        return text.strip()
    except Exception as e:
        logger.error(f"[local_llm] Error: {e}")
        raise


def _call_gpt(prompt: str, system_prompt: str = None) -> str:
    """
    Standard GPT-Wrapper. Nutzt Chat Completions.
    """
    if not _openai_client:
        raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY.")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    resp = _openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


# ---- Public API: Local Draft Generation ----

def generate_local_article(question_id: str, question_text: str, engine_label: str = "local-llm") -> str:
    """
    Generiert einen Roh-Artikel.
    1. Versucht lokalen LLM (Ollama/NIM/…)
    2. Fällt auf GPT zurück, wenn lokal nicht erreichbar
    """
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

    base_prompt = f"""
You are a senior backend engineer writing a deep, practical blog post.

Question ID: {question_id}
Question:
{question_text}

Write a long-form technical article in Markdown with:

- Clear H1 title
- Short intro (2–3 sentences)
- 3–6 main sections with H2/H3
- Code examples where useful
- Section "Common pitfalls"
- Section "Best practices"
- Short conclusion

Language: English.
Target audience: intermediate backend developers.
Do NOT mention that you are an AI or that this is auto-generated.
    """.strip()

    logger.info(f"[generate_local_article] Generating draft for {question_id} via {engine_label}")

    # 1) Attempt local LLM
    try:
        article_md = _call_local_llm(base_prompt)
        header = f"<!-- engine: {engine_label} | created_at: {created_at} -->\n\n"
        return header + article_md
    except Exception as e:
        logger.error(f"[generate_local_article] Local LLM failed: {e}")

    # 2) Fallback: GPT
    if not _openai_client:
        raise RuntimeError(
            "Local LLM is not reachable AND OPENAI_API_KEY is not set. "
            "At least one engine must be available."
        )

    logger.info(f"[generate_local_article] Falling back to GPT ({OPENAI_MODEL}) for {question_id}")
    article_md = _call_gpt(
        base_prompt,
        system_prompt="You are a senior backend engineer and technical writer."
    )
    header = f"<!-- engine: gpt-fallback | created_at: {created_at} -->\n\n"
    return header + article_md


# ---- Public API: Scoring mit GPT ----

def score_article_with_gpt(article_md: str, question_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bewertet einen Artikel mit GPT nach den Dimensionen:
    quality, depth, seo, monetization, overall_score

    Nutzt JSON-Mode, damit garantiert ein parsebares JSON-Objekt zurückkommt.
    """
    if not _openai_client:
        raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY.")

    system_prompt = "You are an expert technical editor and SEO strategist for developer content."

    prompt = f"""
You receive a technical blog article in Markdown and metadata about the underlying user question.

Question metadata (JSON):
{json.dumps(question_meta, indent=2)}

Article (Markdown):
\"\"\"markdown
{article_md}
\"\"\"


Rate the article from 0 to 10 for:

1) quality         – Writing clarity, structure, correctness
2) depth           – Depth of explanation and coverage of edge cases
3) seo             – Searchability, keyword depth, long-tail potential
4) monetization    – Suitability for monetizable packs, consulting, or affiliate links

Return STRICTLY a single JSON object with this structure and nothing else:

{{
  "quality": <int>,
  "depth": <int>,
  "seo": <int>,
  "monetization": <int>,
  "overall_score": <float>
}}
    """.strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    resp = _openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"},  # <- erzwingt reines JSON
    )

    raw = resp.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"[score_article_with_gpt] JSON parse error. Raw: {raw}")
        raise

    # Fallback: overall_score berechnen, falls nicht gesetzt
    if "overall_score" not in data:
        q = float(data.get("quality", 0))
        d = float(data.get("depth", 0))
        s = float(data.get("seo", 0))
        m = float(data.get("monetization", 0))
        data["overall_score"] = round(q * 0.3 + d * 0.3 + s * 0.2 + m * 0.2, 2)

    return data

# ---- Public API: Social Snippets ----

def generate_social_snippets(article_md: str, question_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Erzeugt Social Media Snippets als Liste von Dicts:
    [
      {"platform": "twitter", "text": "..."},
      {"platform": "linkedin", "text": "..."},
      ...
    ]

    Nutzt JSON-Mode, gibt ein JSON-Objekt mit Feld "items" zurück.
    """
    if not _openai_client:
        raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY.")

    system_prompt = "You are a growth-focused content marketer for developer tools."

    prompt = f"""
Create social media snippets for this technical article.

Question metadata (JSON):
{json.dumps(question_meta, indent=2)}

Article (Markdown):
\"\"\"markdown
{article_md}
\"\"\"


Generate:

- 2 concise X/Twitter posts (max 260 characters each, with 1–2 relevant hashtags, no emojis)
- 1 LinkedIn post (3–6 sentences, with value + light CTA, no hashtag wall)
- 1 short Dev.to description (1–2 sentences, teaser for the article)
- 1 short Medium description (1–2 sentences, teaser)
- 1 Substack teaser (2–4 sentences, subtle newsletter CTA)

Return STRICTLY a JSON object with this structure and nothing else:

{{
  "items": [
    {{ "platform": "twitter",  "text": "..." }},
    {{ "platform": "twitter",  "text": "..." }},
    {{ "platform": "linkedin", "text": "..." }},
    {{ "platform": "devto",    "text": "..." }},
    {{ "platform": "medium",   "text": "..." }},
    {{ "platform": "substack", "text": "..." }}
  ]
}}
    """.strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    resp = _openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.4,
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except Exception:
        logger.error(f"[generate_social_snippets] JSON parse error. Raw: {raw}")
        raise

    items = data.get("items", [])
    if not isinstance(items, list):
        raise ValueError(f"[generate_social_snippets] Expected 'items' to be a list, got: {type(items)}")

    return items

