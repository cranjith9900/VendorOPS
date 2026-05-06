import os

import models
from database import Base, SessionLocal, engine


def seed_reference_data():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        rows = [
            models.T001(bukrs="1000", name="PostgreSQL Test Company"),
            models.T052(zterm="NET30", description="Net 30 days"),
            models.T007A(mwskz="A1", rate=18),
            models.BNKA(bankl="BANK01", bank_name="PostgreSQL Test Bank"),
        ]

        for row in rows:
            db.merge(row)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    if not os.getenv("DATABASE_URL", "").startswith("postgresql"):
        raise SystemExit(
            "Set DATABASE_URL to your PostgreSQL URL before running this script."
        )

    seed_reference_data()
    print("PostgreSQL reference data seeded.")
