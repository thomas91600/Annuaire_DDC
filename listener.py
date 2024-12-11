import socket
import struct
import pickle
import cv2
import os
import time
import threading
import subprocess
import numpy as np

# Configuration
HOSTNAME = 'A0008471'
PORT = 9999
SAVE_DIR = 'Camera'
VIDEO_DURATION = 20
AUDIO_TEMP_FILE = "temp_audio.wav"

# Créer les répertoires si nécessaire
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)


# Résoudre le nom d'hôte en adresse IP
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
    
# Fonction pour enregistrer l'audio
def record_audio(stop_event):
    import pyaudio
    import wave
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

    print("Enregistrement audio...")
    frames = []
    while not stop_event.is_set():
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(AUDIO_TEMP_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print("Enregistrement audio terminé.")


# Fusionner vidéo et audio
def merge_video_audio(video_file, audio_file, output_file):
    command = ['ffmpeg', '-i', video_file, '-i', audio_file,
               '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
               '-shortest', output_file]
    subprocess.run(command, check=True)
    print(f"Fusion réussie : {output_file}")


# Recevoir et traiter les frames
def receive_video(conn, video_filename_raw, video_duration):
    data = b""
    payload_size = struct.calcsize("L")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_filename_raw, fourcc, 30.0, (640, 480))

    start_time = time.time()
    while time.time() - start_time < video_duration:
        while len(data) < payload_size:
            data += conn.recv(4096)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += conn.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        try:
            frame = pickle.loads(frame_data)

            # Vérification de la frame
            if isinstance(frame, np.ndarray) and frame.size > 0:
                frame = cv2.resize(frame, (640, 480))
                out.write(frame)
            else:
                print("Frame invalide reçue.")
        except Exception as e:
            print(f"Erreur lors de la réception ou de la désérialisation de la frame : {e}")

    out.release()


# Fonction principale
def main():

    resolved_ip = resolve_hostname(HOSTNAME)
    if not resolved_ip:
        print(f"Impossible de résoudre l'adresse IP pour '{HOSTNAME}'.")
        return
    print(f"Adresse IP résolue pour '{HOSTNAME}': {resolved_ip}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOSTNAME, PORT))
    server_socket.listen(1)
    print(f"En écoute sur {HOSTNAME}:{PORT}...")

    conn, addr = server_socket.accept()
    print(f"Connexion de {addr}")

    video_counter = 1
    video_filename_raw = os.path.join(SAVE_DIR, f"video_raw_{video_counter}.mp4")
    video_filename_final = os.path.join(SAVE_DIR, f"video_{video_counter}.mp4")

    stop_event = threading.Event()

    # Démarrer l'enregistrement audio dans un thread séparé
    audio_thread = threading.Thread(target=record_audio, args=(stop_event,))
    audio_thread.start()

    # Démarrer la réception vidéo
    video_thread = threading.Thread(target=receive_video, args=(conn, video_filename_raw, VIDEO_DURATION))
    video_thread.start()

    # Attendre que les threads finissent
    video_thread.join()
    stop_event.set()
    audio_thread.join

    print("Fusion vidéo/audio...")
    merge_video_audio(video_filename_raw, AUDIO_TEMP_FILE, video_filename_final)

    print(f"Vidéo finale avec audio sauvegardée sous {video_filename_final}")

    # Nettoyage
    os.remove(video_filename_raw)
    os.remove(AUDIO_TEMP_FILE)

    conn.close()
    server_socket.close()


if __name__ == "__main__":
    main()