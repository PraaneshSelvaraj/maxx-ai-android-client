import os
import socket
from time import sleep

def recieve(host,path,port=5001):
    BUFFER_SIZE = 4096
    SEPARATOR = "<SEPARATOR>"
    s = socket.socket()
    print(f"[+] Connecting to {host}:{port}")
    s.connect((host, port))
    print("[+] Connected.")
    received = s.recv(BUFFER_SIZE).decode('ascii')
    s.send("RECIEVED".encode('ascii'))
    filename, filesize = received.split(SEPARATOR)
    filename = os.path.basename(filename)
    filesize = int(filesize)
    with open(path, "wb") as f:
        while True:
            bytes_read = s.recv(BUFFER_SIZE)
            if not bytes_read:    
                break

            f.write(bytes_read)
    s.close()
