
# test run: python3 network.py 
# expected: see audio inputs being sent and recieved, should only be played after 3 packets are recieved
import struct
import socket
import threading
import time
# set address and port
LOCAL_IP = "127.0.0.1"
LOCAL_PORT = 5000
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5000

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
        # get the actual message body
        msg_body = data[4:].decode("utf-8")
        # print recieved msg
        print(f"Recieved from {address}: {seq_num} - {msg_body}")

        # check if the packet shoudl be skipped
        if(seq_num <= last_played_seq):
            continue
        else:
            jitter_buffer.append((seq_num, msg_body))
            jitter_buffer.sort(key=lambda x: x[0])

        # play audio if buffer is full
        if(len(jitter_buffer) >= JITTER_BUFFER_SIZE):
            popped_seq, popped_msg = jitter_buffer.pop(0)
            last_played_seq = popped_seq
            print(f"Playing packet #{popped_seq}: {popped_msg}")
    

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
    
        # create message
        message = f"Audio packet info".encode("utf-8")

        #combine 4 byte header and message body
        packet = header + message

        sock.sendto(packet, (TARGET_IP, TARGET_PORT))

        print(f"Sent packet {seq_num}")

        seq_num += 1
        
        # send 1 packet every 1sec
        time.sleep(1)

send_loop()
