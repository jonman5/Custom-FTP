# COEN 366 Project Winter 2022
# server.py
# By Jonathan Perlman 40094762
# I, Jonathan Perlman, am the sole author and contributor of this file "server.py"
import os
import time
from math import ceil
from socket import *
import sys


# Function parse_request takes the raw request that was received by the server parses it for
# opcode, filename, FS (filesize), new_filename (if applicable)
# The function returns opcode, filename, FS, new_filename, success based on request
# success is 1 if function succeeded in extracting all applicable information from the request, 0 otherwise

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
		if FL > 0 and (opcode != 0b010):
			filename = request[1:FL].decode()
			FS = int.from_bytes(request[FL:FL + 5], byteorder='big')
			if debugMode:
				print(f"message received from client: opcode = {opcode}, FL = {FL}, filename = {filename}, FS = {FS}")
				print(f"raw message received from client: {request.decode()}")
		# Extract new filename if change request
		elif opcode == 0b010:
			filename = request[1:FL].decode()
			NFL = request[FL]
			new_filename = request[FL + 1:NFL + FL + 2].decode()
			if debugMode:
				print(
					f"message received from client: opcode = {opcode}, FL = {FL}, filename = {filename}, new filename = {new_filename}")
				print(f"raw message received from client: {request.decode()}")
		success = 1
		return opcode, filename, FS, new_filename, success
	except Exception:
		print("Error: cannot process client request")
		conn.send(0b01100000.to_bytes(1, byteorder='big'))
		return 0, "", 0, "", 0


try:
	serverPort = sys.argv[1]
	debugMode = False
	if int(sys.argv[2]) > 0:
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

			opcode, filename, filesize, new_fileName, success = parse_request(req)
			if not success:
				conn.send(0b01100000.to_bytes(1, byteorder='big'))

			if opcode == 0b000:  # Put
				try:
					number_of_chunks = ceil(filesize / 4096)
					with open(filename, "wb") as newfile:
						for i in range(0, number_of_chunks):
							data = conn.recv(4096)
							newfile.write(data)
					conn.send(0x00.to_bytes(1, byteorder='big'))
				except IOError:  # Error in reading or writing data
					print("Error in reading or writing data")
					conn.send(0b01100000.to_bytes(1, byteorder='big'))

			elif opcode == 0b001:  # Get
				byte1 = (0b00100000 | (len(filename) + 1)).to_bytes(1, byteorder='big')
				try:
					# check if file exists
					if not os.path.exists(filename):
						conn.send(0b01100000.to_bytes(1, byteorder='big'))

					file_size = os.stat(filename).st_size
					if file_size > (2 ** 32 - 1):
						print("File requested is too large!")
						raise IOError

					FS = file_size.to_bytes(4, byteorder='big')
					response = byte1 + filename.encode() + FS
					conn.send(response)
					time.sleep(0.2)
					number_of_chunks = ceil(file_size / 4096)

					with open(filename, "rb") as file:
						for i in range(0, number_of_chunks):
							data = file.read(4096)
							if data:
								conn.send(data)
							else:
								raise IOError

				except IOError:  # Error in reading or writing data
					print("Error in reading or writing data")
					conn.send(0b01100000.to_bytes(1, byteorder='big'))

			elif opcode == 0b010:  # Change
				try:
					os.replace(filename, new_fileName)
				except (Exception):
					conn.send(0b10100000.to_bytes(1, byteorder='big'))
				finally:
					conn.send(0b0.to_bytes(1, byteorder='big'))

			elif opcode == 0b011:  # Help
				resCode = 0b110 << 5
				helpMessage = "Commands: put get change bye"
				byte1 = (resCode | (len(helpMessage) + 1)).to_bytes(1, byteorder='big')

				print(f"byte1 = {byte1}")
				response = byte1 + helpMessage.encode()
				conn.send(response)

	except (IndexError, Exception):
		print("Server error.")
		continue  # Restart listening for connections
	except (ConnectionResetError, ConnectionAbortedError):
		print("Client disconnected.")
		continue  # Restart listening for connections

conn.close()
