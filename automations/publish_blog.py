import re
import unicodedata
import os
import sys
from datetime import datetime
import subprocess

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select
from app.db import get_session
from app.models.content import ContentItem
from app.db import init_db

# Hugo erwartet Content unter site/content/<section>
POSTS_DIR = os.path.join(ROOT_DIR, "site", "content", "blog")
MAX_POSTS_PER_RUN = 3  # balanced: up to 3/day

init_db()


def slugify(text: str) -> str:
    # 1. Normalize (entfernt z. B. Akzente, „ü“ → „u“)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # 2. Lowercase
    text = text.lower()

    # 3. Alles, was nicht a-z, 0-9 oder '-' ist, durch '-' ersetzen
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # 4. Mehrere '-' zu einem '-' zusammenfassen
    text = re.sub(r"-+", "-", text)

    # 5. Leading/trailing '-' entfernen
    text = text.strip("-")

    return text


def ensure_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def run_git_commands(commit_message: str = "auto: new posts"):
    """
    Setzt git user.name / user.email, committet Änderungen (site/)
    und pusht sie nach origin main.
    """

    # 1) In Repo-Root wechseln (da dort .git liegt)
    repo_root = ROOT_DIR
    os.chdir(repo_root)
    print(f"[publish_blog] Changed working directory to {repo_root}")

    # 1b) Sicherstellen, dass wir auf dem Branch 'main' sind
    subprocess.run(
        ["git", "checkout", "-B", "main"],
        check=True,
    )

    # 2) Git-Identität setzen – aus ENV, sonst Fallback
    author_name = os.getenv("GIT_AUTHOR_NAME", "SilentGPT Bot")
    author_email = os.getenv(
        "GIT_AUTHOR_EMAIL",
        "243322325+jonahbruckner@users.noreply.github.com",
    )

    print(f"[publish_blog] Configuring git user: {author_name} <{author_email}>")

    subprocess.run(["git", "config", "user.name", author_name], check=True)
    subprocess.run(["git", "config", "user.email", author_email], check=True)

    # 3) Prüfen, ob es überhaupt Änderungen gibt
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )

    if not status.stdout.strip():
        print("[publish_blog] No changes to commit, skipping git commit & push.")
        return

    # 4) Änderungen adden (nur site/, damit nur Hugo-Content drin ist)
    print("[publish_blog] Adding changes in site/ to git...")
    subprocess.run(["git", "add", "site"], check=True)

    # 5) Commit
    print(f"[publish_blog] Committing with message: {commit_message!r}")
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # 6) Remote konfigurieren
    remote_url = os.getenv("GIT_REMOTE_URL")
    if not remote_url:
        print("[publish_blog] GIT_REMOTE_URL not set – skipping push.")
        return

    print("[publish_blog] Setting git remote 'origin' (URL from GIT_REMOTE_URL).")
    # Falls schon existiert, entfernen wir ihn leise
    subprocess.run(
        ["git", "remote", "remove", "origin"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)

    # 7) Push
    print("[publish_blog] Pushing to origin main...")
    subprocess.run(["git", "push", "origin", "main"], check=True)

    print("[publish_blog] Git push completed.")


def build_description_from_body(body: str, max_len: int = 240) -> str:
    """
    Nimmt den Body (ohne H1) und baut eine kurze Description
    aus dem ersten sinnvollen Absatz.
    """
    lines = [l.strip() for l in body.splitlines()]
    # erste nicht-leere Zeile als Basis nehmen
    first = next((l for l in lines if l), "")
    if not first:
        return ""

    desc = first.replace("#", "").replace("*", "").strip()
    if len(desc) > max_len:
        desc = desc[: max_len - 3].rstrip() + "..."
    return desc


def strip_leading_h1(body: str) -> str:
    """
    Entfernt eine führende H1-Überschrift (# ...) aus dem Body,
    damit der Titel nicht doppelt (Template + Body) erscheint.
    """
    lines = body.splitlines()
    if not lines:
        return body

    first = lines[0].lstrip()
    if first.startswith("#"):
        # H1 entfernen, Rest zurückgeben
        rest = "\n".join(lines[1:])
        return rest.lstrip("\n")
    return body


def run():
    ensure_dir(POSTS_DIR)

    with get_session() as session:
        q = (
            select(ContentItem)
            .where(ContentItem.status.in_(("draft", "reviewed")))
            .limit(MAX_POSTS_PER_RUN)
        )
        items = session.exec(q).all()

        if not items:
            print("[publish_blog] No draft/reviewed content to publish.")
            return

        for item in items:
            created = item.created_at or datetime.utcnow()
            date_str = created.strftime("%Y-%m-%d")
            slug = slugify(item.title or f"post-{item.id}")
            filename = f"{date_str}-{slug}-{item.id}.md"
            path = os.path.join(POSTS_DIR, filename)

            print(f"[publish_blog] Writing {path}")

            title = item.title or f"Post {item.id}"
            safe_title = title.replace('"', '\\"')

            # Body vorbereiten
            raw_body = (item.body_md or "").strip()
            body_no_h1 = strip_leading_h1(raw_body)
            description = build_description_from_body(body_no_h1)

            # Hugo-Frontmatter (TOML)
            front_matter_lines = [
                "+++",
                f'title = "{safe_title}"',
                f'date = "{created.isoformat()}"',
                f'slug = "{slug}"',
            ]
            if description:
                safe_desc = description.replace('"', '\\"')
                front_matter_lines.append(f'description = "{safe_desc}"')
            front_matter_lines.append("+++")
            front_matter = "\n".join(front_matter_lines) + "\n\n"

            with open(path, "w", encoding="utf-8") as f:
                f.write(front_matter)
                f.write(body_no_h1.strip())
                f.write("\n")

            item.status = "published"

        session.commit()
        print("[publish_blog] Marked items as published.")

    # Auto-Git-Commit & Push
    try:
        run_git_commands()
    except Exception as e:
        print(f"[publish_blog] Git push failed: {e}")


if __name__ == "__main__":
    run()
