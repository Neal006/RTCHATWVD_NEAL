from chatapp import sio, db
from flask_socketio import emit, join_room, leave_room
from flask import request
from chatapp.models import Message
from flask_login import current_user
from datetime import datetime

# Track connected users by socket session ID
connected_users = {}

# Generate consistent room names for two users
def get_room_name(user1, user2):
    return '_'.join(sorted([user1, user2]))

# ----- Connection Events -----

@sio.on('connect')
def handle_connect():
    print(f"[+] User connected: {request.sid}")

@sio.on('disconnect')
def handle_disconnect():
    username = connected_users.pop(request.sid, None)
    print(f"[-] User disconnected: {username or 'Unknown'} - {request.sid}")

# ----- Room Management -----

@sio.on('join_room')
def handle_join_room(data):
    username = data.get('username')
    target = data.get('target')

    if not username or not target:
        return emit('error', {'error': 'Missing username or target for joining room'})

    room = get_room_name(username, target)
    connected_users[request.sid] = username
    join_room(room)
    print(f"[Room] {username} joined room {room}")

@sio.on('join')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)
        print(f"[Room] Socket {request.sid} joined {room}")
    else:
        emit('error', {'error': 'Room not specified for join'})

@sio.on('leave')
def on_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)
        print(f"[Room] Socket {request.sid} left {room}")
    else:
        emit('error', {'error': 'Room not specified for leave'})

# ----- Messaging Events -----

@sio.on('send_message')
def handle_send_message(data):
    room = data.get('room')
    message = data.get('message')

    if not room or not message:
        return emit('error', {'error': 'Room and message are required'})

    sender = getattr(current_user, 'username', 'Anonymous')

    sio.emit('receive_message', {
        'sender': sender,
        'message': message,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

@sio.on('private_message')
def handle_private_message(data):
    sender = data.get('sender')
    receiver = data.get('receiver')
    message = data.get('message')

    if not all([sender, receiver, message]):
        return emit('error', {'error': 'Missing fields in private message'})

    room = get_room_name(sender, receiver)

    msg = Message(room=room, sender=sender, receiver=receiver, content=message)
    db.session.add(msg)
    db.session.commit()

    emit('private_message', {
        'sender': sender,
        'receiver': receiver,
        'content': message,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

# ----- Video Call Events -----

@sio.on('call_user')
def handle_call_user(data):
    room = data.get('room')
    caller = data.get('caller')
    callee = data.get('callee')
    
    if not all([room, caller, callee]):
        return emit('error', {'error': 'Missing call information'})
    
    emit('incoming_call', {
        'caller': caller,
        'room': room
    }, room=room)

@sio.on('call_accepted')
def handle_call_accepted(data):
    room = data.get('room')
    if room:
        emit('call_accepted', room=room)

@sio.on('call_rejected')
def handle_call_rejected(data):
    room = data.get('room')
    if room:
        emit('call_rejected', room=room)

@sio.on('ice_candidate')
def handle_ice_candidate(data):
    room = data.get('room')
    candidate = data.get('candidate')
    if room and candidate:
        emit('ice_candidate', {
            'candidate': candidate
        }, room=room)

@sio.on('offer')
def handle_offer(data):
    room = data.get('room')
    offer = data.get('offer')
    if room and offer:
        emit('offer', {
            'offer': offer
        }, room=room)

@sio.on('answer')
def handle_answer(data):
    room = data.get('room')
    answer = data.get('answer')
    if room and answer:
        emit('answer', {
            'answer': answer
        }, room=room)

@sio.on('end_call')
def handle_end_call(data):
    room = data.get('room')
    if room:
        emit('call_ended', room=room)
