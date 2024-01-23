from flask import Flask, render_template
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

@app.route('/')
def index():
    # Serve the client-side application
    return render_template('index.html')

@sock.route('/echo')
def echo(ws):
    while True:
        # Wait for a message from the client
        data = ws.receive()
        if data is None:
            break  # Connection closed
        print(f"Received message: {data}")
        # Echo the received message back to the client
        ws.send(data)

if __name__ == '__main__':
    app.run(debug=True)
