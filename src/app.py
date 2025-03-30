import os
from flask import Flask, render_template, request, abort, url_for, session, jsonify
from flask_session import Session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import fleep
from speech_to_text import audio_to_text
from text_to_keywords import text_to_keywords
from text_to_problems import text_to_problems
import uuid
import logging
import json


template_dir = os.path.abspath("./templates")
app = Flask(__name__, template_folder="../templates/", static_folder="../static/")
app.secret_key = "oiufhvgi9ychfvguo9gvjhboiuhvgjbknpi0uvgjhbo0uygvhiu9yvghbu08gv"
serializer = URLSafeTimedSerializer(app.secret_key)
socketio = SocketIO(app)
rooms = {}
room_keywords = {}
room_questions = {}
temp_keywords = {}
temp_questions = {}

@app.route("/", methods=["GET"])
def main_page() -> str:
    # return render_template("game_room.html")
    return render_template("index.html")


@app.route('/create_room', methods=['POST'])
def create_room():
    room_name = request.form.get('room_name')
    room_id = str(uuid.uuid4())
    rooms[room_id] = {'name': room_name, 'messages': []}
    room_keywords[room_id] = temp_keywords
    room_questions[room_id] = temp_questions
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
    print("Received calculate request")

    # Check content type
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    message = data.get('message', '')
    room_id = data.get('room_id')
    username = data.get('username')

    print(f"message: {message}, room_id: {room_id}, username: {username}")

    if not room_id or not username:
        return jsonify({'error': 'room_id or username missing'}), 400

    room = rooms.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    # Make sure 'scores' exists
    if 'scores' not in room:
        room['scores'] = {}

    # Calculate length and update score
    length = len(message)
    room['scores'][username] = room['scores'].get(username, 0) + length

    print(room['scores'][username])

    # Check for winner
    if room['scores'][username] >= 50:
        socketio.emit('game_over', {'message': f'{username} has won the game!'}, room=room_id)
        del rooms[room_id]  # Optionally clear room
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
    username = session.get('username')
    length = len(message)

    if room_id in rooms:
        room = rooms[room_id]
        room['messages'].append(message)
        send(f'{username}: {message}', to=room_id)

        # Update the user's score
        if username not in room['scores'] or isinstance(room['scores'][username],int):
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

@app.route('/loading', methods=["POST"])
def login():
    if request.files["file_input"]:  # File option
        file = request.files["file_input"]
        file.save(file.filename)
        with open("filename.txt", "w+") as txt_file:
            txt_file.write(file.filename)
    else:  # Text option
        user_text = request.form["text_input"]
        with open("user_text.txt", "w") as txt_file:
            txt_file.write(user_text)
        with open("filename.txt", "w") as txt_file:
            txt_file.write("user_text.txt")

    return render_template("loading.html")


@app.route("/parse_text")
def parse_text() -> str:
    with open("filename.txt", "r") as txt_file:
        filename = txt_file.read()
    with open(filename, "rb") as file:
        text = ""
        if "audio" in fleep.get(file.read(128)).type:  # audio file
            text = audio_to_text(filename)
        else:
            with open(filename, "r") as file2:
                text = file2.read()

    keyword_pairs = text_to_keywords(text)
    question_answer_pairs = text_to_problems(text)
    global temp_keywords
    global temp_questions
    temp_keywords = keyword_pairs
    temp_questions = question_answer_pairs
    return keyword_pairs

@app.route("/keyword_definition", methods=["POST"])
def keyword_definition():
    data = request.get_json()
    return render_template("keyword_definition.html", data=json.dumps(data))

if __name__ == '__main__':
    socketio.run(app, debug=True)