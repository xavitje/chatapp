from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set

class ConnectionManager:
    """
    Beheert actieve WebSocket-verbindingen, gegroepeerd per kamer.
    """
    def __init__(self):
        # Dict: {room_slug: [WebSocket, WebSocket, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Track online users: {username: Set of room_slugs}
        self.online_users: Dict[str, Set[str]] = {}
        # Track websocket to username mapping for direct messaging
        self.websocket_to_username: Dict[WebSocket, str] = {}
        # Track call room participants: {call_room_slug: Set of usernames}
        self.call_room_participants: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, room_slug: str, username: str = None):
        """Voegt een nieuwe verbinding toe aan een kamer."""
        # Don't accept here - it should be done before authentication
        if room_slug not in self.active_connections:
            self.active_connections[room_slug] = []
        self.active_connections[room_slug].append(websocket)

        # Track online status
        if username:
            if username not in self.online_users:
                self.online_users[username] = set()
            self.online_users[username].add(room_slug)
            # Map websocket to username
            self.websocket_to_username[websocket] = username

    def disconnect(self, websocket: WebSocket, room_slug: str, username: str = None):
        """Verwijdert een verbinding uit een kamer."""
        if room_slug in self.active_connections and websocket in self.active_connections[room_slug]:
            self.active_connections[room_slug].remove(websocket)
            if not self.active_connections[room_slug]:
                del self.active_connections[room_slug] # Verwijder de lijst als deze leeg is

        # Update online status
        if username and username in self.online_users:
            self.online_users[username].discard(room_slug)
            if not self.online_users[username]:
                del self.online_users[username]

        # Remove websocket mapping
        if websocket in self.websocket_to_username:
            del self.websocket_to_username[websocket]

    def is_user_online(self, username: str) -> bool:
        """Check if a user is online in any room."""
        return username in self.online_users and len(self.online_users[username]) > 0

    def get_online_users(self) -> List[str]:
        """Get list of all online usernames."""
        return list(self.online_users.keys())

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Stuurt een bericht naar één specifieke client."""
        await websocket.send_text(message)

    async def broadcast(self, message: str, room_slug: str):
        """Stuurt een bericht naar alle clients in een specifieke kamer."""
        if room_slug in self.active_connections:
            for connection in self.active_connections[room_slug]:
                # We gebruiken try/except voor het geval de verbinding net gesloten is
                try:
                    await connection.send_text(message)
                except RuntimeError:
                    # Log de fout of behandel deze, de disconnect() zal later de verbinding verwijderen
                    pass

    async def send_to_user(self, message: str, username: str):
        """Send a message to a specific user across all their connections."""
        sent_count = 0
        for websocket, ws_username in self.websocket_to_username.items():
            if ws_username == username:
                try:
                    await websocket.send_text(message)
                    sent_count += 1
                except RuntimeError:
                    pass
        print(f"[ConnectionManager] Sent message to {username} via {sent_count} websocket(s)")

    def join_call_room(self, call_room_slug: str, username: str):
        """Add user to call room participants."""
        if call_room_slug not in self.call_room_participants:
            self.call_room_participants[call_room_slug] = set()
        self.call_room_participants[call_room_slug].add(username)

    def leave_call_room(self, call_room_slug: str, username: str):
        """Remove user from call room participants."""
        if call_room_slug in self.call_room_participants:
            self.call_room_participants[call_room_slug].discard(username)
            if not self.call_room_participants[call_room_slug]:
                del self.call_room_participants[call_room_slug]

    def get_call_room_participants(self, call_room_slug: str) -> List[str]:
        """Get list of usernames in a call room."""
        return list(self.call_room_participants.get(call_room_slug, set()))

    async def broadcast_to_call_room(self, message: str, call_room_slug: str, exclude_username: str = None):
        """Send message to all participants in a call room."""
        print(f"[ConnectionManager] Broadcasting to call room {call_room_slug}, participants: {self.call_room_participants.get(call_room_slug, set())}, excluding: {exclude_username}")
        if call_room_slug in self.call_room_participants:
            for username in self.call_room_participants[call_room_slug]:
                if exclude_username and username == exclude_username:
                    print(f"[ConnectionManager] Skipping {username} (excluded)")
                    continue
                print(f"[ConnectionManager] Sending to {username}")
                await self.send_to_user(message, username)


manager = ConnectionManager() # Instantie van de manager voor gebruik in de router