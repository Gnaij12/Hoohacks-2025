import os
from flask import Flask, render_template, request, abort, url_for, session, jsonify
from flask_session import Session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import uuid
template_dir = os.path.abspath("./templates")
app = Flask(__name__, template_folder="../templates/", static_folder="../static/")
app.secret_key = "oiufhvgi9ychfvguo9gvjhboiuhvgjbknpi0uvgjhbo0uygvhiu9yvghbu08gv"
serializer = URLSafeTimedSerializer(app.secret_key)
socketio = SocketIO(app)
rooms = {}

@app.route("/", methods=["GET"])
def main_page() -> str:
    return render_template("index.html")


@app.route('/create_room', methods=['POST'])
def create_room():
    room_name = request.form.get('room_name')
    room_id = str(uuid.uuid4())
    rooms[room_id] = {'name': room_name, 'messages': []}
    token = serializer.dumps(room_id, salt='room-access')
    room_url = url_for('join_room_page', token=token, _external=True)
    return f'Room "{room_name}" created successfully! Share this link: <a href="{room_url}">{room_url}</a>'

@app.route('/join_room/<token>')
def join_room_page(token):
    try:
        room_id = serializer.loads(token, salt='room-access', max_age=1800)
    except SignatureExpired:
        abort(403, description='The link has expired.')
    except BadSignature:
        abort(403, description='Invalid access token.')

    room = rooms.get(room_id)
    if room:
        session['room_id'] = room_id
        session['username'] = request.args.get('username')
        return render_template('chat_room.html', room_name=room['name'], room_id=room_id, token=token)
    else:
        abort(404, description='Room not found.')

@app.route('/calculate', methods=['POST'])
def calculate_length():
    data = request.get_json()
    message = data.get('message', '')
    room_id = session.get('room_id')
    username = session.get('username')

    if not room_id or not username:
        return jsonify({'error': 'User session data missing'}), 400

    room = rooms.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    # Calculate message length
    length = len(message)

    # Update the user's score
    room['scores'][username] = room['scores'].get(username, 0) + length

    # Check if the user has reached the score threshold
    if room['scores'][username] >= 50:
        socketio.emit('game_over', {'message': f'{username} has won the game!'}, room=room_id)
        # Optionally, reset or remove the room
        del rooms[room_id]
        return jsonify({'message': f'{username} has won the game!'}), 200

    return jsonify({'length': length, 'new_score': room['scores'][username]})

@socketio.on('join')
def handle_join(data):
    token = data.get('token')
    username = data.get('username')
    if not token or not username:
        emit('error', {'message': 'Missing token or username.'})
        return

    try:
        room_id = serializer.loads(token, salt='room-access', max_age=1800)
    except SignatureExpired:
        emit('error', {'message': 'The link has expired.'})
        return
    except BadSignature:
        emit('error', {'message': 'Invalid access token.'})
        return

    if room_id in rooms:
        join_room(room_id)
        send(f'{username} has entered the room.', to=room_id)
    else:
        emit('error', {'message': 'Room not found.'})

@socketio.on('message')
def handle_message(data):
    room_id = data.get('room')
    message = data.get('message')
    length = data.get('length')
    username = session.get('username')

    if room_id in rooms:
        room = rooms[room_id]
        room['messages'].append(message)
        send(f'{username}: {message}', to=room_id)

        # Update the user's score
        if username not in room['scores']:
            room['scores'][username] = 0
        room['scores'][username] += length

        # Check if the user has reached the score threshold
        if room['scores'][username] >= 50:
            emit('game_over', {'message': f'{username} has won the game!'}, to=room_id)
    else:
        emit('error', {'message': 'Room not found.'})

@socketio.on('disconnect')
def handle_disconnect():
    room_id = session.get('room_id')
    username = session.get('username')
    if room_id and username:
        leave_room(room_id)
        send(f'{username} has left the room.', to=room_id)
        # Optionally, remove user from any tracking structures here
    print(f'Client {request.sid} disconnected.')

if __name__ == '__main__':
    socketio.run(app, debug=True)