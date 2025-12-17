# Chat Applicatie - Installatie & Gebruik

## Overzicht
Dit is een volledige real-time chat applicatie gebouwd met FastAPI, WebSockets, SQLAlchemy en JWT authenticatie.

## Features
✅ Gebruikersregistratie en login met JWT authenticatie
✅ Real-time groepschats (meerdere kamers)
✅ Directe berichten tussen gebruikers (one-on-one)
✅ Berichtengeschiedenis opslag in database
✅ Online gebruikerslijst
✅ Responsive en modern UI met Tailwind CSS

## Installatie

### 1. Controleer je Python versie
```bash
python --version
```
Je hebt Python 3.8 of hoger nodig.

### 2. Installeer dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialiseer de database
Er zijn twee opties:

**Optie A: Gebruik het init script (Makkelijkst)**
```bash
python init_db.py
```

**Optie B: Gebruik Alembic migraties**
```bash
alembic revision --autogenerate -m "Add direct messages table"
alembic upgrade head
```

## De applicatie starten

```bash
python main.py
```

De applicatie draait nu op: http://127.0.0.1:8000

## Gebruik

### 1. Eerste keer - Registreren
- Ga naar http://127.0.0.1:8000 (wordt automatisch doorgestuurd naar login)
- Klik op "Registreer hier"
- Voer een gebruikersnaam en wachtwoord in
- Na registratie word je doorgestuurd naar login

### 2. Inloggen
- Voer je gebruikersnaam en wachtwoord in
- Je wordt doorgestuurd naar de chat

### 3. Groepschat
- Klik op "# Algemeen" of "# Dev Team" in de sidebar
- Type een bericht en druk op Enter of klik "Verzenden"
- Alle gebruikers in dezelfde kamer zien je berichten real-time

### 4. Directe Berichten
- Klik op "💬 Directe Berichten" in de sidebar
- Selecteer een gebruiker uit de lijst rechts
- Type een bericht en verzend
- Alleen jij en de geselecteerde gebruiker kunnen deze berichten zien

## Opgeloste Problemen

### 1. Bcrypt Password Error ✅
**Probleem:** `ValueError: password cannot be longer than 72 bytes`
**Oplossing:** Wachtwoorden worden nu automatisch getrunked tot 72 bytes in `security.py`

### 2. Websocket Authenticatie ✅
**Probleem:** Dummy gebruikers werden aangemaakt zonder authenticatie
**Oplossing:** JWT token wordt nu gestuurd bij websocket verbinding en geverifieerd

### 3. Geen Login/Register Pagina's ✅
**Probleem:** Applicatie had geen manier om gebruikers te registreren
**Oplossing:** Volledige login en registratie pagina's toegevoegd

### 4. Geen Directe Berichten ✅
**Probleem:** Alleen groepschats waren mogelijk
**Oplossing:** Volledig directe messaging systeem geïmplementeerd

## Applicatie Structuur

```
ChattApp/
├── main.py                     # Hoofdapplicatie entry point
├── init_db.py                  # Database initialisatie script
├── requirements.txt            # Python dependencies
├── alembic.ini                 # Alembic configuratie
├── alembic/                    # Database migraties
├── app/
│   ├── api/
│   │   ├── auth.py            # Authenticatie routes (login/register)
│   │   ├── chat.py            # WebSocket chat routes
│   │   ├── direct_messages.py # Directe berichten API
│   │   ├── pages.py           # HTML pagina routes
│   │   └── schemas.py         # Pydantic schemas
│   ├── auth/
│   │   └── security.py        # JWT & password hashing
│   ├── database/
│   │   └── database.py        # Database configuratie
│   ├── models/
│   │   ├── user.py            # User model
│   │   ├── room.py            # Chat room model
│   │   ├── message.py         # Group message model
│   │   └── direct_message.py  # Direct message model
│   └── services/
│       ├── chat_crud.py       # Database CRUD operaties
│       └── connection_manager.py # WebSocket verbindingsbeheer
└── templates/
    ├── login.html             # Login pagina
    ├── register.html          # Registratie pagina
    ├── index.html             # Hoofdchat pagina (groepen)
    └── direct_messages.html   # Directe berichten pagina
```

## API Endpoints

### Authenticatie
- `POST /auth/register` - Nieuwe gebruiker registreren
- `POST /auth/token` - Inloggen en JWT token ontvangen

### Chat Kamers
- `GET /api/rooms/{room_slug}/history` - Berichtgeschiedenis ophalen
- `WebSocket /api/ws/chat/{room_slug}` - WebSocket verbinding voor real-time chat

### Directe Berichten
- `GET /api/users` - Alle gebruikers ophalen
- `POST /api/direct-message` - Direct bericht versturen
- `GET /api/direct-messages/{username}` - Conversatie ophalen met specifieke gebruiker
- `GET /api/unread-count` - Aantal ongelezen berichten ophalen

### Pagina's
- `GET /` - Redirect naar login
- `GET /login` - Login pagina
- `GET /register` - Registratie pagina
- `GET /chat/{room_slug}` - Chat kamer pagina
- `GET /direct-messages` - Directe berichten pagina

## Security Features

- **Wachtwoord Hashing:** Bcrypt wordt gebruikt om wachtwoorden veilig op te slaan
- **JWT Authenticatie:** Alle beveiligde endpoints vereisen een geldig JWT token
- **WebSocket Authenticatie:** JWT token wordt geverifieerd bij websocket verbinding
- **Token Expiratie:** Tokens verlopen na 30 minuten


### WebSocket verbinding faalt
- Controleer of je bent ingelogd
- Check je browser console voor errors
- Refresh de pagina

### Token expired
- Login opnieuw
- De applicatie zou automatisch moeten redirecten naar login

## Nieuw Toegevoegde Features

✅ **Dark/Light Mode Toggle** - Theme switcher met persistent preference (localStorage)
✅ **Browser Notificaties** - Desktop notificaties voor nieuwe berichten (wanneer pagina niet zichtbaar is)
✅ **Emoji Picker** - Emoji selector in message input met 100+ populaire emojis
✅ **Typing Indicators** - Real-time "gebruiker is aan het typen..." indicators

### Hoe te gebruiken:

**Theme Toggle:**
- Klik op de zon/maan knop rechtsboven op elke pagina
- Je voorkeur wordt opgeslagen en toegepast op alle pagina's

**Notificaties:**
- Bij eerste gebruik vraagt de browser om toestemming
- Je krijgt alleen notificaties wanneer de chat niet zichtbaar is
- Klik op de notificatie om terug te gaan naar de chat

**Emoji Picker:**
- Klik op de 😀 knop naast het message input veld
- Selecteer een emoji om toe te voegen aan je bericht

**Typing Indicators:**
- Type in het message veld - anderen zien automatisch dat je aan het typen bent
- Stopt automatisch na 3 seconden inactiviteit

## JavaScript Utilities

De volgende herbruikbare utilities zijn beschikbaar in `/static/`:
- `theme-toggle.js` - Theme switching functionaliteit
- `notifications.js` - NotificationManager class
- `emoji-picker.js` - EmojiPicker component
- `typing-indicator.js` - TypingIndicator manager

## Toekomstige Verbeteringen

Mogelijke features om nog toe te voegen:
- [ ] Message reactions (emoji reactions op berichten)
- [ ] Online/offline status indicators (real-time groene/grijze dot)
- [ ] Groep aanmaken functionaliteit (custom chat rooms)
- [ ] User profielen met avatars
- [ ] Message search functionaliteit (zoeken in geschiedenis)
- [ ] File/Image upload in berichten
- [ ] Voice messages
- [ ] Read receipts (gezien/gelezen status)

