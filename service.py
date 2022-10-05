import pickle
from time import sleep
import socket
from plyer import tts

def connect_server(dev_name,ip,port,hsh):
    print("connect server")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("created client obj")
    client.connect((ip,int(port)))
    client.settimeout(10)
    print("connect to obj")
    print(ip,port)
    message = client.recv(1024).decode('ascii')

    if message == 'NICKNAME':
        msg=dev_name+"~"+hsh
        client.send(msg.encode('ascii'))
        
    message = client.recv(1024).decode('ascii')
    print(message)
    if message=="CONNECTIONACCEPTED":
        hsh = client.recv(1024).decode('ascii')
        print("HASH : {}".format(hsh))
        return client

    elif message=="!NAME":
        print("NAME ALREADY CHOSEN")


    else:
        print("MESSAGE : "+message)

    return None


sleep(5)
file = open("./data.pickle","rb")
data = pickle.load(file)
file.close()
dev_name,ip,port = data
print(data)
dev_name="LISTENER*"+dev_name
f = open('hash.pickle','rb')
hsh = pickle.load(f)
f.close()
client = connect_server(dev_name,ip,port,hsh)

while True:
    try:
        message = client.recv(1024).decode('ascii')
        print(message)
        if message == "!DISCONNECT":
            client.send("DISCONNECTED".encode("ascii"))
            client.close()
            exit()
            
        elif message == '!ALIVE':
            client.send("alive".encode("ascii"))
        
        task,msg = message.split("~")
        client.send("RECIEVED".encode("ascii"))
        if task == "speak":
            tts.speak(msg)

        elif task =="WEBBROWSER":
            with open('cmd.txt','w') as f:
                f.write(message)
            f.close()

        
    except Exception as e:
        print("RECIEVE EXC: {}".format(e))



