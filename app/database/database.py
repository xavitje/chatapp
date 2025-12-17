from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Gebruik een SQLite-databasebestand
SQLALCHEMY_DATABASE_URL = "sqlite:///./chat_app.db"

# De engine wordt gemaakt (connectie naar de DB)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# De sessie-maker: elke keer dat we met de DB willen praten, creëren we een sessie.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# De basisklasse voor al onze ORM-modellen
Base = declarative_base()

# Dependency: Een functie om een nieuwe DB-sessie te krijgen voor elke route
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()