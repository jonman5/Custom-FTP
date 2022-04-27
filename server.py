# COEN 366 Project Winter 2022
# By Jonathan Perlman 40094762

# server.py

from socket import *
import sys
from pathlib import Path

# print(f"Arguments of the script : {sys.argv[1:]=}")


def parse_request(request):
	try:
		# Extract opcode and FL (filename length) from first byte of request
		request_byte1 = request[0]
		opcode = request_byte1 >> 5
		FL = request_byte1 & 0b00011111
		filename = ""
		new_filename = ""
		FS = 0
		# Extract filename based on FL
		if FL > 0 & (opcode != 0b010):
			filename = request[1:FL].decode()
			print(f"filename = {filename}")
			FS = int.from_bytes(request[FL+1:FL+5], byteorder='big')
			print(f"FS = {FS}")
		# Extract new filename if change request
		if opcode == 0b010:
			filename = request[1:FL].decode()
			print(f"filename = {filename}")
			NFL = [FL+1]
			new_filename = request[FL+2:NFL+FL+2].decode()
			print(f"new filename = {new_filename}")
		success = 1
		return opcode, filename, FS, new_filename, success
	except Exception:
		print("Error: cannot process client request")
		return 0, "", 0, "", 0

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
		while conn:
			req = conn.recv(1024)
			# If empty message received from client, client has disconnected
			if req == b'':
				print("Client disconnected.")
				break  # Restart listening for connections

			print(f"req = {req}")
			opcode, filename, filesize, new_fileName, success = parse_request(req)
			if not success:
				conn.send(0b01100000.to_bytes(1, byteorder='big'))
			print(f"opcode = {opcode}")

			if opcode == 0b000:  # Put
				try:
					# Path("jFTP").mkdir(exist_ok=True)
					data = conn.recv(filesize+100).decode()
					with open(filename, "w") as newfile:
						newfile.write(data)
					conn.send(0x00.to_bytes(1, byteorder='big'))
				except IOError:  # Error in reading or writing data
					print("Error in reading or writing data")
					conn.send(0b01100000.to_bytes(1, byteorder='big'))

			elif opcode == 0b001:  # Get
				byte1 = (0b00100000 | (len(filename) + 1)).to_bytes(1, byteorder='big')
				try:
					with open(filename, "r") as file:
						data = file.read()
						file_size = len(data)
						if file_size > (2**32 - 1):
							print("File too large")
							raise IOError
						FS = file_size.to_bytes(4, byteorder='big')
						response = byte1 + filename.encode() + FS
						conn.send(response)
						conn.send(data.encode())
				except IOError:  # Error in reading or writing data
					print("Error in reading or writing data")

			elif opcode == 0b010:  # Change
				# try:

				conn.send(0b10100000.to_bytes(1, byteorder='big'))

			elif opcode == 0b011:  # Help
				resCode = 0b110 << 5
				helpMessage = "Commands: put get change bye"
				byte1 = (resCode | (len(helpMessage) + 1)).to_bytes(1, byteorder='big')

				print(f"byte1 = {byte1}")
				response = byte1 + helpMessage.encode()
				conn.send(response)

	except IndexError:
		print("Server error.")
		continue # Restart listening for connections
	except (ConnectionResetError, ConnectionAbortedError):
		print("Client disconnected.")
		continue  # Restart listening for connections
# break
conn.close()




