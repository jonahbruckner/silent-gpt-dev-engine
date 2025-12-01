from backend.app.db.session import init_db
from backend.app.models import content  # noqa: F401  # wichtig: Modelle registrieren

if __name__ == "__main__":
    # Erstellt alle Tabellen in der Datenbank, falls sie noch nicht existieren
    init_db()
    print("Database initialized.")
