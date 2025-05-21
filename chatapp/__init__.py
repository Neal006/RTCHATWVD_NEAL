
import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS

sio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
db = SQLAlchemy()
login_manager = LoginManager()

login_manager.login_view = 'main.login' 

def create_app():
    app = Flask(__name__)
    CORS(app) 
    app.config['SECRET_KEY'] = 'ndvvrvrfknwi3j3098765rfvkjytgvbfjytgbnmjhyefgju765rfbnmki8765rfbnmki876tgnmkiuy6trdcvbhytfvz$$%^RRFGFRTYZA4rfr%$r%$%^%$BNHGVNJHFVBBNFCVBNHGFCVNHFVNJHvwedqwndhwvwefnwf'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    db.init_app(app)
    login_manager.init_app(app)

    from chatapp.routes import main
    app.register_blueprint(main)

    sio.init_app(app)

    return app

from chatapp import socket_handler