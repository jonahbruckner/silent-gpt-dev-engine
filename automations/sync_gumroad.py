import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

# from app.db import get_session
# from app.models.product import Product  # only if you create such a model


def run():
    # Placeholder: implement Gumroad sync later
    print("[sync_gumroad] Not implemented yet. Skipping.")


if __name__ == "__main__":
    run()
