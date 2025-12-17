from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.schemas import UserCreate, UserLogin
from app.database.database import get_db
from app.models.user import User
from app.auth.security import hash_password, verify_password, create_access_token
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

# Router initialiseren
router = APIRouter(tags=["Auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Registreert een nieuwe gebruiker door het wachtwoord te hashen
    en de gebruiker in de database op te slaan.
    """
    # Controleer of de gebruikersnaam al bestaat
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Gebruikersnaam bestaat al")

    # Wachtwoord hashen
    hashed_pass = hash_password(user.password)

    # Nieuwe gebruiker aanmaken
    new_user = User(username=user.username, hashed_password=hashed_pass)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": f"Gebruiker '{new_user.username}' succesvol geregistreerd."}


@router.post("/token")
def login_for_access_token(
    # OAuth2PasswordRequestForm is de standaard manier van FastAPI om login-data te ontvangen
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Verifieert inloggegevens en geeft een JWT-token terug.
    """
    # Gebruiker zoeken
    user = db.query(User).filter(User.username == form_data.username).first()

    # Verificatie van gebruiker en wachtwoord
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrecte gebruikersnaam of wachtwoord",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token genereren
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # De response voldoet aan de OAuth2 specificatie
    return {"access_token": access_token, "token_type": "bearer"}