
# test run: python3 network.py in one terminal and python3 CLIENT_B.py in another
# might have to use arch -x86_64 python3 ... depending on architecture
import struct
import socket
import threading
import queue
import pyaudio

# set address and port
LOCAL_IP = "127.0.0.1"
LOCAL_PORT = 5000
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5001

# === Audio config ===
# 1024 frames of sound at a time
CHUNK = 1024
# audio data is formatted in 16 bit integers
FORMAT = pyaudio.paInt16
# 1 for one mic, set to 2 if we are using two mics (Stereo)
CHANNELS = 1
# number of times per second the mic is listened to
RATE = 44100

# === Jitter buffer config ===
# how many packets we wait for before starting to play audio 
JITTER_BUFFER_SIZE = 3
DEFAULT_PORT = 5000


# Auto-detect the user's LAN IP by opening a dummy UDP socket
def detect_local_ip():
    try:
        dummy = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dummy.connect(("8.8.8.8", 80))
        ip = dummy.getsockname()[0]
        dummy.close()
        return ip
    # otherwise default to 127.0.0.1
    except Exception:
        return "127.0.0.1"

# Define all logic regarding network and audio in a class so it can be called by the GUI
class NetworkLogic:
    def __init__(self, local_ip, local_port, target_ip, target_port):
        # initialize variables
        self.target_ip = target_ip
        self.target_port = target_port
        self.running = False # only set to true once call is joined

        # === PyAudio config ====

        self.p = pyaudio.PyAudio()
        # audio input stream (from mic)
        self.mic_stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        # audio output stream (to speakers)
        self.speaker_stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

        # === UDP socket setup ===

        # create UDP socket using IPv4
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bind socket to given IP and port
        self.sock.bind((local_ip, local_port))

        # === Shared variables ===
        
        # waiting list for incoming data
        self.jitter_buffer = []
        # mutex lock to prevent race conditions from recv_thread
        self.jitter_lock = threading.Lock()
        # track the ID of the last played packet
        self.last_played_seq = -1
        # intermediary queue used by 
        self.audio_queue = queue.Queue()

    # when the call is joined, call start() to begin all audio sending and recieving
    def start(self):
        self.running = True
        # start the audio threads
        threading.Thread(target=self.recieve_loop, daemon=True).start()
        threading.Thread(target=self.send_loop, daemon=True).start()

    def recieve_loop(self):
        # core logic
        while self.running:

            # recieve data
            data, _ = sock.recvfrom(4096)

            # unpack the first 4 bytes as sequence number
            header = data[:4]
            seq_num = struct.unpack("!I", header)[0]
            # get the actual message body in raw audio bytes
            msg_body = data[4:]
            
            # optional debug statement
            # print(f"Received packet {seq_num}")

            # check if the packet should be skipped
            if(seq_num <= last_played_seq):
                continue
            else:
                jitter_buffer.append((seq_num, msg_body))
                jitter_buffer.sort(key=lambda x: x[0])

            # play audio if buffer is full
            if(len(jitter_buffer) >= JITTER_BUFFER_SIZE):
                popped_seq, popped_msg = jitter_buffer.pop(0)
                last_played_seq = popped_seq
                
                # write audio chunk to speaker
                speaker_stream.write(popped_msg)

    # thread that sends audio from user to server
    def send_loop():
        # sequence number counter for packets
        seq_num = 0

        while self.running:
            # create header
            header = struct.pack("!I", seq_num)
        
            # grab chunk of raw audio from mic
            audio = self.mic_stream.read(CHUNK, exception_on_overflow=False)

            # concatenate header and audio data into 1 packet and send it
            packet = header + audio
            self.sock.sendto(packet, (TARGET_IP, TARGET_PORT))

            # print(f"Sent packet {seq_num}")
            seq_num += 1

