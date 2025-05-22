from chatapp import create_app, db, sio
import eventlet
import eventlet.wsgi

app = create_app()

if __name__ == "__main__":
    sio.run(app, host="0.0.0.0", port=8001, debug=False)
