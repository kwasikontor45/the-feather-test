from flask_socketio import emit, join_room, leave_room
from . import socketio
from .routes.game_routes import active_rooms
from .ai_bird import get_bird_response


@socketio.on('judge_join')
def on_judge_join(data):
    room_code = data.get('room_code')
    room = active_rooms.get(room_code)
    if not room:
        emit('error', {'message': 'room not found'})
        return

    from flask import request
    room['judge_sid'] = request.sid
    join_room(room_code)

    bird_connected = room.get('human_sid') is not None
    emit('status', {
        'bird_connected': bird_connected,
        'round': room['round'],
    })


@socketio.on('bird_join')
def on_bird_join(data):
    room_code = data.get('room_code')
    room = active_rooms.get(room_code)
    if not room:
        emit('error', {'message': 'room not found'})
        return

    from flask import request
    room['human_sid'] = request.sid
    join_room(room_code)

    # tell the judge the bird has arrived
    emit('bird_arrived', {}, to=room_code, skip_sid=request.sid)
    emit('connected', {'message': 'You are connected. The ornithologist will ask soon.'})


@socketio.on('send_question')
def on_send_question(data):
    """
    Judge sends a question.
    - Emit it to the human bird.
    - Call Claude in a background thread.
    - Send both replies back to judge labeled Bird A / Bird B.
    """
    room_code = data.get('room_code')
    question = data.get('question', '').strip()
    room = active_rooms.get(room_code)

    if not room or not question:
        return

    if room['round'] >= 5:
        return

    room['round'] += 1
    current_round = room['round']

    # tell the judge the round started
    emit('round_started', {'round': current_round, 'question': question}, to=room_code)

    # send question to human bird
    if room.get('human_sid'):
        emit('question_received', {
            'round': current_round,
            'question': question,
        }, to=room['human_sid'])
    else:
        # no human — mark their slot as no-show
        _route_response(room_code, room, current_round, is_human=True, text='[bird did not respond]')

    # call Claude in background — start_background_task uses eventlet.spawn()
    # so it yields correctly to the event loop (raw threading.Thread blocks httpx)
    def fetch_ai_response():
        try:
            reply = get_bird_response(room['species'], question, room['history'])
            room['history'].append({'role': 'user', 'content': question})
            room['history'].append({'role': 'assistant', 'content': reply})
        except Exception:
            reply = f'[the {room["species"]} ruffled its feathers and said nothing]'

        _route_response(room_code, room, current_round, is_human=False, text=reply)

    socketio.start_background_task(fetch_ai_response)


@socketio.on('bird_reply')
def on_bird_reply(data):
    room_code = data.get('room_code')
    reply = data.get('reply', '').strip()
    current_round = data.get('round')
    room = active_rooms.get(room_code)

    if not room or not reply:
        return

    _route_response(room_code, room, current_round, is_human=True, text=reply)


def _route_response(room_code, room, round_num, is_human, text):
    """
    Decides whether this response goes to Bird A or Bird B slot
    and emits it to the judge's room.
    """
    # human_is_bird_a == True → human goes to A, AI goes to B
    if is_human:
        slot = 'A' if room['human_is_bird_a'] else 'B'
    else:
        slot = 'B' if room['human_is_bird_a'] else 'A'

    socketio.emit('bird_response', {
        'round': round_num,
        'slot': slot,
        'text': text,
    }, to=room_code)


@socketio.on('disconnect')
def on_disconnect():
    from flask import request
    sid = request.sid
    for room_code, room in active_rooms.items():
        if room.get('human_sid') == sid:
            room['human_sid'] = None
            socketio.emit('bird_left', {}, to=room_code)
            break
