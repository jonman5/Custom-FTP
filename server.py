# COEN 366 Project Winter 2022
# By Jonathan Perlman 40094762

# server.py

from socket import *
import sys

#print(f"Arguments of the script : {sys.argv[1:]=}")

try:
    serverPort = sys.argv[1]
    debugMode = False
    if sys.argv[2] == 1:
        debugMode = True
except IndexError:
    raise SystemExit(f"Usage: {sys.argv[0]} <port> <Debug mode (0 or 1)>")

local_ip = gethostbyname(gethostname())
serverIP = local_ip
serverPort = int(serverPort)
print("Server IP: " + serverIP)
serverSocket = socket(AF_INET, SOCK_STREAM)  # SOCK_STREAM -> TCP
serverSocket.bind((serverIP, serverPort))
serverSocket.listen(1)

while 1:
    try:
        print("Server is listening for connections on port " + str(serverPort))
        conn, addr = serverSocket.accept()
        print("Client connection established")

        req = (conn.recv(2).decode())
        digitLimit = 1
        if not req[1].isdigit():
            digitLimit = 0
        opcode = int(req[:digitLimit+1]) >> 5
        filename = ""
        print(f"req = {req}")
        print(f"opcode = {opcode}")

        if opcode == 0b000:  # Put
            FL = int(req[:digitLimit+1])
            if digitLimit == 0:
                filename = req[digitLimit+1:]
            print(f"FL = {FL}")
            req = (conn.recv(5+FL).decode())
            filename += req[:FL+1]
            print("filename = " + filename)
            conn.send(str(0x00).encode())

        elif opcode == 0b001:  # Get
            FL = int(req) & 0b00011111
            print(f"FL = {FL}")
            req = (conn.recv(5+FL).decode())
            filename = req[:FL+1]
            print("filename = " + filename)
            conn.send(str(0x00).encode())

        elif opcode == 0b010:  # Change
            conn.send("Change?".encode())

        elif opcode == 0b011:  # Help
            resCode = 0b110 << 5
            helpMessage = "Commands: put get change bye"
            byte1 = resCode | (len(helpMessage)+1)
            print(f"byte1 = {byte1}")
            response = str(byte1) + helpMessage
            conn.send(response.encode())

    except IndexError:
        print("Server error")
        #break
conn.close()
