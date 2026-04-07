
# test run: python3 network.py in one terminal and python3 CLIENT_B.py in another
# might have to use arch -x86_64 python3 ... depending on architecture
import struct
import socket
import threading
import time
import pyaudio
# set address and port
LOCAL_IP = "127.0.0.1"
LOCAL_PORT = 5000
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5001

# audio configs
# 1024 size of sound at a time
CHUNK = 1024
# 16 bit integer 
FORMAT = pyaudio.paInt16
# 1 for one mic, set to 2 if we are using two mics (Stereo)
CHANNELS = 1
# mic is listened to RATE times a second
RATE = 44100

# initialize PyAudio
p = pyaudio.PyAudio()

# creating mic stream
mic_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

# Create the Speaker Stream
speaker_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# create UDP socket, and use IPv4
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# bind socket
sock.bind((LOCAL_IP, LOCAL_PORT))

# waiting list for incoming data
jitter_buffer = []
# how many packets we wait for before starting to play audio 
JITTER_BUFFER_SIZE = 3
#the last ID we played
last_played_seq = -1

def recieve_loop():
    global last_played_seq
    # core logic
    while True:

        # recieve data
        data, address = sock.recvfrom(4096)

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
    

# background thread for recieving

recv_thread = threading.Thread(target=recieve_loop, daemon=True)
recv_thread.start()

def send_loop():
    # sequence number counter for packets
    seq_num = 0

    # core logic
    while True:
        # create header
        header = struct.pack("!I", seq_num)
    
        # grab chunk of raw audio from mic
        message = mic_stream.read(CHUNK, exception_on_overflow=False)

        #combine 4 byte header and message body
        packet = header + message

        sock.sendto(packet, (TARGET_IP, TARGET_PORT))

        print(f"Sent packet {seq_num}")

        seq_num += 1
        

send_loop()
