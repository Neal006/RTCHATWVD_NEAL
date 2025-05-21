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

    # Save message to DB
    msg = Message(room=room, sender=sender, receiver=receiver, content=message)
    db.session.add(msg)
    db.session.commit()

    emit('private_message', {
        'sender': sender,
        'receiver': receiver,
        'content': message,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

# ----- WebRTC Signaling -----

@sio.on('webrtc_offer')
def handle_webrtc_offer(data):
    to_user = data.get('to')
    from_user = data.get('from')
    offer = data.get('offer')

    if not all([to_user, from_user, offer]):
        return emit('error', {'error': 'Missing fields in WebRTC offer'})

    room = get_room_name(to_user, from_user)
    emit('webrtc_offer', {'offer': offer, 'from': from_user}, room=room, include_self=False)

@sio.on('webrtc_answer')
def handle_webrtc_answer(data):
    to_user = data.get('to')
    from_user = data.get('from')
    answer = data.get('answer')

    if not all([to_user, from_user, answer]):
        return emit('error', {'error': 'Missing fields in WebRTC answer'})

    room = get_room_name(to_user, from_user)
    emit('webrtc_answer', {'answer': answer, 'from': from_user}, room=room, include_self=False)

@sio.on('webrtc_ice')
def handle_webrtc_ice(data):
    to_user = data.get('to')
    from_user = data.get('from')
    candidate = data.get('candidate')

    if not all([to_user, from_user, candidate]):
        return emit('error', {'error': 'Missing fields in WebRTC ICE'})

    room = get_room_name(to_user, from_user)
    emit('webrtc_ice', {'candidate': candidate, 'from': from_user}, room=room, include_self=False)

@sio.on('webrtc_end')
def handle_webrtc_end(data):
    to_user = data.get('to')
    from_user = data.get('from')

    if not all([to_user, from_user]):
        return emit('error', {'error': 'Missing fields in WebRTC end'})

    room = get_room_name(to_user, from_user)
    emit('webrtc_end', {}, room=room, include_self=False)