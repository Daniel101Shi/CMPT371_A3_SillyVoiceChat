import socket 
import struct
import time
# set target address and port
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5000

# set socket, IPv4 and UDP

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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

    