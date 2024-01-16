from fastapi import FastAPI ,Cookie, File, UploadFile,APIRouter, Request,Response
from fastapi.responses import FileResponse,HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import socketio
import uvicorn
from collections import  defaultdict
import os
from fastapi.middleware.cors import CORSMiddleware
import threading 
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, Request, Depends, HTTPException, Cookie
from typing import Optional, List
app : FastAPI = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# 비동기 서버 생성
sio : socketio.AsyncServer = socketio.AsyncServer(async_mode='asgi',  
                          credits=True,
                           cors_allowed_origins = [
    "*",
    'http://localhost:5000',
    'https://admin.socket.io',
    'http://127.0.0.1:5000',  # 콤마(,) 추가
    'http://localhost:3000',  # 클라이언트 애플리케이션 주소 추가
    'http://192.168.137.1:3000'
]
)  
app.add_middleware( ##
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5000',
        'https://admin.socket.io',
        'http://127.0.0.1:5000',
        'http://localhost:3000',  # 클라이언트 애플리케이션 주소 추가
        'http://192.168.137.1:3000'
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#관리자 모드 인증 설정
# sio.instrument(auth=False) # 권한 없이 접속하기
# sio.instrument({'username':'WB38' , 'password':os.environ['WB38']})
#password = os.environ.get('WB38', 'default_password')

#socketIO와 FastAPI를 합치기
combined_asgi_app = socketio.ASGIApp(sio, app)

#매니저 가져오기
manager = sio.manager
 #WB38                           your_password
users_in_room = {} # users_in_room[room_id] =[] sid]
rooms_sid = {} # rooms_sid[sid] = room_id
names_sid = {} # names_sid[sid] = client_name
sessions = {}# 사용자 정보를 저장할 딕셔너리
combined_asgi_app = socketio.ASGIApp(sio, app)

# @app.post('/upload')
# async def upload_file(file: UploadFile = File(...)):
#     file_path = os.path.join('저장', file.filename)
#     with open(file_path, 'wb') as f:
#         f.write(await file.read())
#     return {"filename": file.filename}

@app.post('/upload')
async def upload_file(files: UploadFile = File(...)):
    file_path = os.path.join('저장', files.filename)
    with open(file_path, 'wb') as f:
        f.write(await files.read())
    return {"filename": files.filename}


@app.get('/join',response_class=HTMLResponse,name='join')
async def index(request:Request,
          room_id:Optional[str]=None,
          display_name:Optional[str]=None,
          mute_audio:Optional[str]=None,
          mute_video:Optional[str]=None
 
            ):
    # display_name = request.query_params.get('display_name')
    # mute_audio = request.query_params.get('mute_audio')  # 1 or 0
    # mute_video = request.query_params.get('mute_video')  # 1 or 0
    # room_id = request.query_params.get('room_id')
    sessions[room_id]= {"name": display_name,
                        "mute_audio": mute_audio, "mute_video": mute_video}
    # 세션에 사용자 정보 저장
    response =   templates.TemplateResponse(
        "join.html", {"request": request,"room_id": room_id, "display_name": sessions[room_id]["name"], "mute_audio": sessions[room_id]["mute_audio"], "mute_video": sessions[room_id]["mute_video"]})
    return response

myRoomID = "your_room_id"
    
@sio.on("connect")
async def connected(sid,*args, **kwargs):     
    room_id = kwargs.get("room_id")  # 예시로 kwargs에서 가져오는 방식
    print("New socket connected ", sid)
    await sio.emit("connected", to=sid)
    await sio.emit("user-list", {"list": users_in_room.get(room_id, {}), "my_id": sid}, to=sid)

      
@sio.on("join-room")
async def on_join_room(sid, data):
    print(f"Received join-room event from {sid}: {data}")
    room_id = data.get["room_id"]
    display_name = sessions[room_id]["name"]

    await sio.enter_room(room=room_id, sid=sid)
    rooms_sid[sid] = room_id
    names_sid[sid] = display_name
    ####
    print("[{}] New member joined: {}<{}>".format(room_id, display_name, sid))
    await sio.emit("user-connect", {"sid": sid, "name": display_name}, room=room_id, skip_sid=sid)
    
    if room_id not in users_in_room:
        users_in_room[room_id] = [sid]
        await sio.emit("user-list", {"my_id": sid}, to=sid)  # send own id only
    else:
        usrlist = {u_id: names_sid[u_id] for u_id in users_in_room[room_id]}
        await sio.emit("user-list", {"list": usrlist, "my_id": sid}, to=sid)
        # add new member to user list maintained on the server
        users_in_room[room_id].append(sid)
        
    print("\nusers: ", users_in_room, "\n")


@sio.on("disconnect")
async def on_disconnect(sid,*args, **kwargs):
    room_id =  rooms_sid.get(sid)
    display_name =  names_sid.get(sid)

    print("[{}] Member left: {}<{}>".format(room_id, display_name, sid))
    await sio.emit("user-disconnect",{"sid": sid} 
                   ,room=room_id,skip_sid=sid)

    users_in_room[room_id].pop(sid,None)
    if len(users_in_room[room_id]) == 0:
        users_in_room.pop(room_id,None)

    rooms_sid.pop(sid,None)
    names_sid.pop(sid,None)
    
    await sio.leave_room(sid=sid,room=room_id)
    print("\nusers: ", users_in_room, "\n")

@sio.on("data")
async def on_data(sid,data):
    sender_sid = data['sender_id']
    target_sid = data['target_id']
    if sender_sid != sid:
        print("[Not supposed to happen!] request.sid and sender_id don't match!!!")

    if data["type"] != "new-ice-candidate":
        print('{} message from {} to {}'.format(
            data["type"], sender_sid, target_sid))
    await sio.emit('data', data, to=target_sid)
 



if __name__ == '__main__':

    uvicorn.run(combined_asgi_app, host='127.0.0.1', port=5000)