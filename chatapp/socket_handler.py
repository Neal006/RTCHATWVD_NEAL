from chatapp import sio, db
from flask_socketio import send, emit, join_room, leave_room
from flask import request
from chatapp.models import Message
from flask_login import current_user
from datetime import datetime

connected_users = {}

def get_room_name(user1, user2):
    return '_'.join(sorted([user1, user2]))

@sio.on('connect')
def handle_connect():
    print(f"User connected: {request.sid}")

@sio.on('disconnect')
def handle_disconnect():
    username = connected_users.pop(request.sid, None)
    print(f"User disconnected: {username} - {request.sid}")

@sio.on('join_room')
def handle_join(data):
    user1 = data['username']
    user2 = data['target']
    room = get_room_name(user1, user2)
    connected_users[request.sid] = user1
    join_room(room)
    print(f"{user1} joined room {room}")

@sio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)  # <-- Use this instead of sio.enter_room

@sio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    print(f"User {request.sid} left room {room}")
    
@sio.on('send_message')
def handle_send_message(data):
    room = data['room']
    message = data['message']
    sender = current_user.username
    # Save message to DB here if needed
    sio.emit('receive_message', {
        'sender': sender,
        'message': message
    }, room=room)
    
@sio.on('private_message')
def handle_private_message(data):
    sender = data['sender']
    receiver = data['receiver']
    message = data['message']
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

@sio.on('webrtc_offer')
def handle_webrtc_offer(data):
    to_user = data['to']
    from_user = data['from']
    offer = data['offer']
    room = get_room_name(to_user, from_user)
    emit('webrtc_offer', {'offer': offer, 'from': from_user}, room=room, include_self=False)

@sio.on('webrtc_answer')
def handle_webrtc_answer(data):
    to_user = data['to']
    from_user = data['from']
    answer = data['answer']
    room = get_room_name(to_user, from_user)
    emit('webrtc_answer', {'answer': answer, 'from': from_user}, room=room, include_self=False)

@sio.on('webrtc_ice')
def handle_webrtc_ice(data):
    to_user = data['to']
    from_user = data['from']
    candidate = data['candidate']
    room = get_room_name(to_user, from_user)
    emit('webrtc_ice', {'candidate': candidate, 'from': from_user}, room=room, include_self=False)

@sio.on('webrtc_end')
def handle_webrtc_end(data):
    to_user = data['to']
    from_user = data['from']
    room = get_room_name(to_user, from_user)
    emit('webrtc_end', {}, room=room, include_self=False)

