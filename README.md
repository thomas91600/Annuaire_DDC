# Malicious Camera Project :rocket:

This project is an educational demonstration of a tool using Python to capture images through a camera. It consists of two Python scripts: one for the main execution and a listener for monitoring actions.

⚠️ **Disclaimer**: This project is strictly for educational purposes and cybersecurity awareness. Any malicious use is illegal and unethical.

## Technologies Used :computer:

-   Python :snake:
-   PyInstaller :package:
-   OpenCV :camera:
-   Pyaudio 🎧
-   FFmpeg 📽️


## Installation and executable creation :wrench:

1. Clone the repository: `git clone https://github.com/thomas91600/Annuaire_DDC.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Generate .exe : `pyinstaller --onefile --noconsole listener.py`
4. Strat the listener : `py listener.py`

## Usage :bulb:

### On the Server:

-   **Start the server script**: `py listener.py`. 
-   The server will listen for connections and save the captured video and audio in the Camera directory.

### On the Client:

-   **Lauch the executable**: Double click on the .exe. 
-   The client captures video from the webcam, records audio, and sends the data to the server.

## Contributing :handshake:

If you find a bug or have a suggestion for improvement, feel free to open an issue or submit a pull request.
