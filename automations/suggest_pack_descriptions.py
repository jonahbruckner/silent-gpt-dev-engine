import os
from pathlib import Path
import yaml
import textwrap

# Falls du die openai-Python-Library nutzt:
# pip install openai
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "site" / "data" / "packs.yaml"
BLOG_DIR = ROOT / "site" / "content" / "blog"

OPENAI_MODEL = "gpt-4.1-mini"  # anpassen wenn gewünscht


def load_packs():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_article_title(slug: str) -> str:
    """
    Versucht, den Titel aus der Blog-Markdown-Datei zu lesen.
    Einfacher Parser für Hugo-Frontmatter.
    """
    # Unterstützung für slug.md und slug/index.md
    candidates = [
        BLOG_DIR / f"{slug}.md",
        BLOG_DIR / slug / "index.md",
    ]
    for path in candidates:
        if path.exists():
            break
    else:
        return slug  # Fallback: slug selbst

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # sehr einfacher Frontmatter-Parser
    if not lines or not lines[0].strip().startswith("+++"):
        return slug

    for line in lines[1:]:
        if line.strip().startswith("title"):
            # title = "Foo Bar"
            parts = line.split("=", 1)
            if len(parts) == 2:
                return parts[1].strip().strip('"').strip("'")
        if line.strip().startswith("+++"):
            break

    return slug


def build_prompt(pack, article_titles):
    title = pack["title"]
    short = pack.get("short_description", "")
    articles = "\n".join(f"- {t}" for t in article_titles)

    return textwrap.dedent(
        f"""
        You are helping write product copy for a developer micro-tutorial bundle.

        Pack title: {title}
        Short description: {short}

        The pack contains the following micro-tutorials:
        {articles}

        Task:
        - Write a concise 2–3 sentence product description.
        - Target audience: experienced developers working with AI / Python / FastAPI etc.
        - Focus on practical value, not hype.
        - Use "you" perspective and sound like a helpful expert.
        - Keep it under 80–100 words.

        Return ONLY the description text, no bullet points, no headings.
        """
    ).strip()


def suggest_description(pack):
    article_slugs = pack.get("article_slugs", [])
    titles = [load_article_title(s) for s in article_slugs]

    prompt = build_prompt(pack, titles)

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    resp = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
    )
    return resp.output[0].content[0].text  # ggf. an neues API-Format anpassen


def run():
    packs = load_packs()

    for pack in packs:
        if pack.get("long_description"):
            print(f"[suggest] Skip {pack['slug']} (already has long_description)")
            continue

        print(f"\n=== {pack['title']} ({pack['slug']}) ===")
        try:
            desc = suggest_description(pack)
        except Exception as e:
            print(f"ERROR generating description: {e}")
            continue

        print("\nSuggested description:\n")
        print(desc)
        print("\nCopy this into packs.yaml under long_description.\n")

    print("\n[suggest_pack_descriptions] Done.")


if __name__ == "__main__":
    run()
