from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.connection_manager import manager
from app.services import chat_crud # <-- NIEUW: Database functies
from app.api.schemas import MessageDisplay
import json

router = APIRouter(tags=["Chat"])

# HTTP Route om de berichtgeschiedenis op te halen (gebruikt door de frontend bij het laden)
@router.get("/rooms/{room_slug}/history", response_model=list[MessageDisplay])
def get_history(room_slug: str, db: Session = Depends(get_db)):
    """Haalt de geschiedenis van berichten op voor een kamer."""
    return chat_crud.get_message_history(db, room_slug)


@router.websocket("/ws/chat/{room_slug}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_slug: str,
    db: Session = Depends(get_db)
):
    # Accept the connection first to receive data
    await websocket.accept()

    client_username = None

    try:
        # Receive the token from the client
        auth_message = await websocket.receive_json()
        token = auth_message.get("token")

        if not token:
            await websocket.send_text("Authentication failed: No token provided")
            await websocket.close()
            return

        # Verify the JWT token
        from app.auth.security import SECRET_KEY, ALGORITHM
        from jose import jwt, JWTError

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            client_username = payload.get("sub")
            if not client_username:
                await websocket.send_text("Authentication failed: Invalid token")
                await websocket.close()
                return
        except JWTError:
            await websocket.send_text("Authentication failed: Invalid token")
            await websocket.close()
            return

        # Verify user exists
        user = chat_crud.get_user_by_username(db, client_username)
        if not user:
            await websocket.send_text("Authentication failed: User not found")
            await websocket.close()
            return

        # Update user online status
        user.is_online = True
        from datetime import datetime
        user.last_seen = datetime.utcnow()
        db.commit()

        # Connect to the room
        await manager.connect(websocket, room_slug, client_username)

        # Systeemmelding
        join_message = f"**{client_username}** is de chat binnengekomen."
        await manager.broadcast(join_message, room_slug)

        # Broadcast online status update
        online_users = manager.get_online_users()
        await manager.broadcast(
            f'{{"type":"online_status","online_users":{online_users}}}',
            room_slug
        )

        while True:
            # Ontvang data als JSON
            data_json = await websocket.receive_json()

            # Check if it's a typing indicator
            if data_json.get('type') == 'typing':
                # Broadcast typing status to room
                await manager.broadcast(
                    f'{{"type":"typing","username":"{data_json.get("username")}","isTyping":{str(data_json.get("isTyping")).lower()}}}',
                    room_slug
                )
                continue

            # Handle WebRTC call room signaling messages
            if data_json.get('type') == 'call-room-join':
                # User joined a call room
                call_room_slug = data_json.get('callRoom')
                print(f"[SERVER] {client_username} joining call room {call_room_slug}")

                # Get existing participants before adding new one
                existing_participants = manager.get_call_room_participants(call_room_slug)
                print(f"[SERVER] Existing participants in {call_room_slug}: {existing_participants}")

                # Add user to call room
                manager.join_call_room(call_room_slug, client_username)
                print(f"[SERVER] After adding {client_username}, participants: {manager.get_call_room_participants(call_room_slug)}")

                # Send existing participants to the new joiner
                if existing_participants:
                    try:
                        message = f'{{"type":"existing-participants","participants":{json.dumps(existing_participants)},"callRoom":"{call_room_slug}"}}'
                        print(f"[SERVER] Sending to {client_username}: {message}")
                        await manager.send_to_user(message, client_username)
                        print(f"[SERVER] Message sent successfully to {client_username}")
                    except Exception as e:
                        print(f"[SERVER ERROR] Failed to send existing-participants to {client_username}: {e}")
                else:
                    print(f"[SERVER] No existing participants to send to {client_username}")

                # Notify existing participants about new peer
                try:
                    peer_joined_msg = f'{{"type":"peer-joined","username":"{client_username}","callRoom":"{call_room_slug}"}}'
                    print(f"[SERVER] Broadcasting peer-joined to call room {call_room_slug} (excluding {client_username}): {peer_joined_msg}")
                    await manager.broadcast_to_call_room(
                        peer_joined_msg,
                        call_room_slug,
                        exclude_username=client_username
                    )
                    print(f"[SERVER] peer-joined broadcast completed")
                except Exception as e:
                    print(f"[SERVER ERROR] Failed to broadcast peer-joined: {e}")
                continue

            if data_json.get('type') == 'call-room-leave':
                # User left call room
                call_room_slug = data_json.get('callRoom')
                manager.leave_call_room(call_room_slug, client_username)

                # Notify others in call room
                await manager.broadcast_to_call_room(
                    f'{{"type":"peer-left","username":"{client_username}","callRoom":"{call_room_slug}"}}',
                    call_room_slug
                )
                continue

            # Handle WebRTC peer-to-peer signaling (within call room)
            if data_json.get('type') in ['call-offer', 'call-answer', 'ice-candidate']:
                # Forward signaling messages to the recipient
                recipient = data_json.get('to')
                if recipient:
                    import json
                    await manager.send_to_user(json.dumps(data_json), recipient)
                continue

            # Check if it's a regular message
            if data_json.get('type') == 'message':
                content = data_json.get('content')
                reply_to_id = data_json.get('reply_to_id')

                # 1. Bericht opslaan in DB
                saved_message = chat_crud.save_message(
                    db=db,
                    username=client_username,
                    room_slug=room_slug,
                    content=content,
                    reply_to_id=reply_to_id
                )

                if saved_message:
                    # 2. Formatteer de JSON voor de frontend
                    # We sturen een JSON-object, niet alleen tekst
                    broadcast_data = saved_message.model_dump_json()

                    # 3. Bericht doorsturen naar de hele kamer
                    await manager.broadcast(broadcast_data, room_slug)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_slug, client_username)
        # Update user status in database
        if client_username:
            user = chat_crud.get_user_by_username(db, client_username)
            if user:
                user.is_online = manager.is_user_online(client_username)
                user.last_seen = datetime.utcnow()
                db.commit()
        await manager.broadcast(f"**{client_username}** heeft de chat verlaten.", room_slug)
        # Broadcast online status update
        online_users = manager.get_online_users()
        await manager.broadcast(
            f'{{"type":"online_status","online_users":{online_users}}}',
            room_slug
        )

    except Exception as e:
        manager.disconnect(websocket, room_slug, client_username)
        if client_username:
            user = chat_crud.get_user_by_username(db, client_username)
            if user:
                user.is_online = False
                user.last_seen = datetime.utcnow()
                db.commit()
        # Optioneel: log de fout
        pass