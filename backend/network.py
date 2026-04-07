
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

# core logic
while True:

    # recieve data
    data, address = sock.recvfrom(4096)

    # unpack the first 4 bytes as sequence number
    header = data[:4]

    # get the actual message body
    msg_body = data[4:].decode("utf-8")
    
    # print recieved msg
    print(f"Recieved from {address}: {header} {msg_body}")


