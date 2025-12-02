import os
import sys
from datetime import datetime
import subprocess
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from sqlmodel import select
from app.db import get_session
from app.models.content import ContentItem
from app.db import init_db

POSTS_DIR = os.path.join(ROOT_DIR, "site", "posts")
MAX_POSTS_PER_RUN = 3  # balanced: up to 3/day

init_db()


def slugify(title: str) -> str:
    return (
        title.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("?", "")
        .replace("#", "")
        .replace(":", "")
    )


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

    # 2) Git-Identität setzen – aus ENV, sonst Fallback
    author_name = os.getenv("GIT_AUTHOR_NAME", "SilentGPT Bot")
    author_email = os.getenv("GIT_AUTHOR_EMAIL", "243322325+jonahbruckner@users.noreply.github.com")

    print(f"[publish_blog] Configuring git user: {author_name} <{author_email}>")

    subprocess.run(
        ["git", "config", "user.name", author_name],
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", author_email],
        check=True,
    )

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
    subprocess.run(
        ["git", "commit", "-m", commit_message],
        check=True,
    )

    # 6) Remote konfigurieren
    remote_url = os.getenv("GIT_REMOTE_URL")
    if not remote_url:
        print("[publish_blog] GIT_REMOTE_URL not set – skipping push.")
        return

    print(f"[publish_blog] Setting git remote 'origin' to {remote_url}")
    # Falls schon existiert, ignorieren wir den Fehler
    subprocess.run(["git", "remote", "remove", "origin"], check=False)
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)

    # 7) Push (Branchname ggf. anpassen, falls nicht main)
    print("[publish_blog] Pushing to origin main...")
    subprocess.run(
        ["git", "push", "origin", "main"],
        check=True,
    )

    print("[publish_blog] Git push completed.")

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
            with open(path, "w", encoding="utf-8") as f:
                f.write(item.body_md or "")

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
