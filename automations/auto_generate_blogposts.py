#!/usr/bin/env python3
import os
import sys
from typing import List, Dict, Any

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select  # noqa
from app.db import get_session, init_db
from app.models.content import ContentItem

from openai import OpenAI
import yaml

init_db()

TEMPLATES_PATH = os.path.join(ROOT_DIR, "automations", "pack_templates.yaml")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
POSTS_PER_TOPIC = int(os.environ.get("AUTO_POSTS_PER_TOPIC", "1"))

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def load_templates() -> List[Dict[str, Any]]:
    if not os.path.isfile(TEMPLATES_PATH):
        raise FileNotFoundError(f"Template file not found: {TEMPLATES_PATH}")
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    if not isinstance(data, list):
        raise ValueError("pack_templates.yaml must contain a top-level list")
    return data


def generate_article_markdown(template: Dict[str, Any]) -> Dict[str, str]:
    if not client:
        raise RuntimeError("OPENAI_API_KEY is not set – cannot generate content.")

    topic = template.get("topic", "")
    title = template.get("title", "")
    description_prompt = (template.get("description_prompt") or "").strip()
    keywords = template.get("keywords") or []

    guidance_lines = []
    guidance_lines.append(f"Topic: {topic}")
    if title:
        guidance_lines.append(f"Pack title: {title}")
    if description_prompt:
        guidance_lines.append(f"High-level focus: {description_prompt}")
    if keywords:
        guidance_lines.append("Keywords to weave in naturally: " + ", ".join(keywords))

    guidance = "\n".join(guidance_lines)

    user_prompt = (
        "Schreibe ein eigenständiges technisches Micro-Tutorial in Markdown "
        "für Entwickler:innen mit mittlerem Niveau.\n\n"
        "Sprache: Deutsch.\n"
        "Länge: ca. 600–900 Wörter.\n"
        "Struktur:\n"
        "- Eine einzige H1-Überschrift als Titel.\n"
        "- Problem erklären.\n"
        "- Konkrete Codebeispiele.\n"
        "- Kurze Zusammenfassung am Ende.\n"
        "Fokus: praxisnah, keine theoretische Vorlesung.\n\n"
        f"{guidance}\n\n"
        "Gib NUR den Artikel in Markdown aus, ohne weitere Erklärungen."
    )

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Du bist Senior-Entwickler:in und schreibst klare, praxisnahe Tutorials.",
            },
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1400,
        temperature=0.7,
    )
    content = (resp.choices[0].message.content or "").strip()

    lines = content.splitlines()
    if not lines:
        raise RuntimeError("Model returned empty content.")

    # Titel aus erster Überschrift extrahieren
    first_heading_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("#"):
            first_heading_idx = idx
            break

    if first_heading_idx is None:
        title_text = (template.get("title") or "Untitled Tutorial").strip()
        body_md = content
    else:
        title_line = lines[first_heading_idx]
        title_text = title_line.lstrip("#").strip()
        body_md = "\n".join(lines[first_heading_idx + 1 :]).strip()

    return {"title": title_text, "body_md": body_md}


def create_content_item(title: str, body_md: str, template: Dict[str, Any]) -> None:
    tags = template.get("keywords") or []
    tags_str = ",".join(tags)

    with get_session() as session:
        item = ContentItem(
            raw_id=None,
            type="tutorial",
            title=title,
            body_md=body_md,
            tags=tags_str,
            status="published",
        )
        session.add(item)
        session.commit()
        print(f"[auto_generate_blogposts] Created ContentItem id={item.id} title={title!r}")


def run():
    templates = load_templates()
    if not templates:
        print("[auto_generate_blogposts] No templates found, nothing to do.")
        return

    for template in templates:
        topic = template.get("topic", "")
        pack_slug = template.get("pack_slug", "")
        print(
            f"[auto_generate_blogposts] Generating {POSTS_PER_TOPIC} posts "
            f"for topic={topic!r} ({pack_slug})"
        )

        for i in range(POSTS_PER_TOPIC):
            try:
                md = generate_article_markdown(template)
                create_content_item(md["title"], md["body_md"], template)
            except Exception as exc:
                print(f"[auto_generate_blogposts] Error for topic={topic} run={i+1}: {exc}")


if __name__ == "__main__":
    run()
