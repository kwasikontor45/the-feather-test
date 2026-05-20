from flask import Blueprint, request, jsonify
import eventlet
from ..ai_bird import get_bird_response

api_bp = Blueprint('api', __name__)


@api_bp.route('/bird-response', methods=['POST'])
def bird_response():
    data = request.get_json()
    species = data.get('species')
    question = data.get('question')
    history = data.get('history', [])

    if not species or not question:
        return jsonify({'error': 'species and question are required'}), 400

    try:
        # run in a greenlet so the httpx call yields to the eventlet loop
        gt = eventlet.spawn(get_bird_response, species, question, history)
        reply = gt.wait()
        return jsonify({'reply': reply})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'bird did not respond', 'detail': str(e)}), 500
