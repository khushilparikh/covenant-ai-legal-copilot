"""
One-time setup script: creates all tables and a demo admin user so you can
log in immediately without going through /api/auth/register first.

Run after configuring .env and creating the Postgres database:
    python -m app.db.seed
"""
from app.core.security import hash_password
from app.db import models
from app.db.database import Base, SessionLocal, engine
from app.services.compliance_service import seed_default_playbook

DEMO_EMAIL = "admin@covenant.dev"
DEMO_PASSWORD = "ChangeMe123!"


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.email == DEMO_EMAIL).first():
            db.add(models.User(
                email=DEMO_EMAIL,
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name="Demo Admin",
                role=models.UserRole.ADMIN,
            ))
            db.commit()
            print(f"Created demo admin user: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            print("Demo admin user already exists — skipping.")

        seed_default_playbook(db)
        print("Seeded default compliance playbook rules.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
