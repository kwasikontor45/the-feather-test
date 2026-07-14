import random
import string
from flask import Blueprint, render_template, redirect, url_for, session, request
from ..db.store import create_session, get_session, get_leaderboard
from ..ai_bird import list_species

game_bp = Blueprint('game', __name__)

# in-memory room registry: {room_code: {species, human_is_bird_a, human_sid, judge_sid}}
# this is reset on server restart; SQLite holds the persistent record
active_rooms = {}


def _generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


@game_bp.route('/')
def index():
    return render_template('index.html')


@game_bp.route('/create', methods=['GET', 'POST'])
def create_game():
    if request.method == 'POST':
        species_list = list_species()
        chosen = random.choice(species_list)
        species_id = chosen['id']

        room_code = _generate_room_code()
        while room_code in active_rooms:
            room_code = _generate_room_code()

        # randomly assign: is the human Bird A or Bird B?
        human_is_bird_a = random.choice([True, False])

        active_rooms[room_code] = {
            'species': species_id,
            'species_name': chosen['name'],
            'human_is_bird_a': human_is_bird_a,
            'human_sid': None,
            'judge_sid': None,
            'round': 0,
            'history': [],
        }

        create_session(room_code, species_id, human_is_bird_a)

        return redirect(url_for('game.judge_lobby', room_code=room_code))

    return render_template('create-game.html')


@game_bp.route('/game/<room_code>')
def judge_lobby(room_code):
    room = active_rooms.get(room_code) or get_session(room_code)
    if not room:
        return render_template('error.html', message='Room not found.'), 404
    return render_template('game-view.html', room_code=room_code)


@game_bp.route('/join', methods=['GET', 'POST'])
def join_game():
    if request.method == 'POST':
        room_code = request.form.get('room_code', '').strip().upper()
        room = active_rooms.get(room_code)
        if not room:
            return render_template('join-game.html', error='Room not found. Check the code and try again.')
        return redirect(url_for('game.bird_view', room_code=room_code))

    return render_template('join-game.html')


@game_bp.route('/bird/<room_code>')
def bird_view(room_code):
    room = active_rooms.get(room_code)
    if not room:
        return render_template('error.html', message='Room not found.'), 404

    # The human needs the same character brief the AI's system prompt gets —
    # otherwise they're improvising "generic bird" against an AI playing one
    # very specific, richly-detailed species, which isn't a fair test of
    # human-vs-AI and can make the two respondents describe different animals
    # entirely. Same brief, different means of performing it.
    from ..ai_bird import load_species
    species = load_species(room['species'])

    return render_template('bird-view.html', room_code=room_code, species=species)


@game_bp.route('/reveal/<room_code>')
def reveal(room_code):
    room = active_rooms.get(room_code)
    session_data = get_session(room_code)
    if not room and not session_data:
        return render_template('error.html', message='Room not found.'), 404

    species_id = (room or session_data)['species']
    human_is_bird_a = bool((room or session_data).get('human_is_bird_a', session_data and session_data.get('human_is_bird_a')))
    # judge guessed which slot held the AI
    guess = request.args.get('guess', '')          # 'A' or 'B'
    ai_is_a = not bool((room or session_data).get('human_is_bird_a', True))
    actual_ai_slot = 'A' if ai_is_a else 'B'
    judge_correct = guess.upper() == actual_ai_slot

    from ..db.store import complete_session
    complete_session(room_code, judge_correct)

    leaderboard = get_leaderboard()

    from ..ai_bird import load_species
    species = load_species(species_id)

    return render_template(
        'reveal.html',
        room_code=room_code,
        species=species,
        species_id=species_id,
        human_is_bird_a=human_is_bird_a,
        judge_correct=judge_correct,
        leaderboard=leaderboard,
    )


@game_bp.route('/leaderboard')
def leaderboard():
    data = get_leaderboard()
    return render_template('leaderboard.html', leaderboard=data)
