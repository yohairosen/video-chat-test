import threading
from app import run_app  # Adjusted import based on the new function in app.py
import fay_connect  # Ensure fay_connect.py is adjusted to be importable

def start_flask_app():
    run_app()

if __name__ == "__main__":
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.start()

    # Wait a moment for Flask to fully start up (optional, adjust as necessary)
    import time
    time.sleep(10)  # Adjust based on actual startup time

    # Now, call the main function of fay_connect.py
    fay_connect.main()
