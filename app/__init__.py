from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

load_dotenv()

socketio = SocketIO()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')

    from .routes.game_routes import game_bp
    from .routes.api_routes import api_bp
    app.register_blueprint(game_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    socketio.init_app(app, cors_allowed_origins='*', async_mode='eventlet')

    from .db.store import init_db
    init_db()

    # register socket event handlers
    from . import sockets  # noqa: F401

    return app
