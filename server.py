from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import socketio

# Create a FastAPI instance
app = FastAPI()

# Create a Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*")
app.mount("/ws", socketio.ASGIApp(sio))

# Create a WebSocket handler
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: WebSocket):
    return templates.TemplateResponse("index.html", {"request": request})

# Connect event
@sio.on("connect")
async def connect(sid, environ):
    print(f"connect {sid}")
    return True

# Disconnect event
@sio.on("disconnect")
async def disconnect(sid):
    print(f"disconnect {sid}")

# Join room event
@sio.on("join-room")
async def join_room(sid, data):
    room_id = data["room_id"]
    display_name = data["display_name"]
    mute_audio = data["mute_audio"]
    mute_video = data["mute_video"]

    # Add the client to the room
    sio.enter_room(sid, room_id)

    # Broadcast the user list to all clients in the room
    await sio.emit("user-list", {"list": list(sio.rooms[room_id])}, room=room_id)

    # Broadcast to other clients in the room that a new user has joined
    await sio.emit("user-connect", {"sid": sid, "name": display_name}, room=room_id)

# Leave room event
@sio.on("leave-room")
async def leave_room(sid, data):
    room_id = data["room_id"]
    display_name = data["display_name"]

    # Remove the client from the room
    sio.leave_room(sid, room_id)

    # Broadcast to other clients in the room that a user has left
    await sio.emit("user-disconnect", {"sid": sid, "name": display_name}, room=room_id)
