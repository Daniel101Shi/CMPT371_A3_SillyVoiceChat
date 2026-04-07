
# test: run python3 network.py in one terminal
# run: echo "Hello from terminal 2" | nc -u 127.0.0.1 5000 ,in another terminal
import struct
import socket
# set address and port
LOCAL_IP = "127.0.0.1"
LOCAL_PORT = 5000

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
    

    


