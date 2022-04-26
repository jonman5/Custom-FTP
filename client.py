# COEN 366 Project Winter 2022
# By Jonathan Perlman 40094762

# client.py
# Requires python version >= 3.10 to run
from socket import *
local_ip = gethostbyname(gethostname())
clientIP = "169.254.217.77"
clientPort = 65432
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((clientIP, clientPort))

while True:
    command_str = input("jFTP> ")
    separated_commands = command_str.split()
    try:
        match separated_commands[0]:
            case "put":
                opcode = 0b000 << 5
                filename = separated_commands[1]
                byte1 = opcode | (len(filename)+1)
                request = str(byte1) + filename
            case "get":
                opcode = 0b001 << 5
                filename = separated_commands[1]
                byte1 = opcode | (len(filename)+1)
                request = str(byte1) + filename
            case "change":
                opcode = 0b010 << 5
                oldFilename = separated_commands[1]
                newFilename = separated_commands[2]
                byte1 = opcode | (len(oldFilename)+1)
                request = str(byte1) + oldFilename + str(len(newFilename)+1) + newFilename
            case "help":
                opcode = bytes(0b011 << 5)
                request = (opcode)
                print(f"request = {request}")
            case "bye":
                print("BYE!")
                clientSocket.close()
                break
            case _:
                raise Exception

        print(f"command = {request}")

        clientSocket.send(request)
        response = clientSocket.recv(1024).decode()
        print(f"response = {response}")
        res_code = int(response[:3]) >> 5
        print(f"res code = {res_code}")
        match res_code:
            case 0b000:  # Correct put and change request response
                print("Successful put or get")
            case 0b001:  # Correct get request response
                print("successful put or get")
            case 0b010:  # Error file not found response
                print("Error: file not found")
            case 0b011:  # Error unknown request response
                print("Error: unknown request")
            case 0b101:  # Error unsuccessful change response
                print("Error: file change unsuccessful")
            case 0b110:  # Correct help response
                print(response[3:])

    except (IndexError):
        print("Error: Invalid command. Input a command and filename(s). Type <help> for commands.")
