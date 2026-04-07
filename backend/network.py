import socket
# set address and port
LOCAL_IP = "127.0.0.1"
LOCAL_PORT = 5000

# create UDP socket, and use IPv4

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# bind socket

sock.bind((LOCAL_IP, LOCAL_PORT))

