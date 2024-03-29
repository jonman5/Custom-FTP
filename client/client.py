# COEN 366 Project Winter 2022
# By Jonathan Perlman 40094762

# client.py
# Requires python version >= 3.10 to run

from socket import *


def parse_get_response(response):
	try:
		# Extract FL (filename length) from first byte of response
		response_byte1 = response[0]
		FL = response_byte1 & 0b00011111
		# Extract filename based on FL
		filename = response[1:FL].decode()
		print(f"response filename = {filename}")
		FS = int.from_bytes(response[FL + 1:FL + 5], byteorder='big')
		print(f"FS = {FS}")
		success = 1
		return filename, FS, success
	except Exception:
		print("Error: cannot process server response")
		return "", 0, 0


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
				byte1 = (opcode | (len(filename) + 1)).to_bytes(1, byteorder='big')
				try:
					with open(filename, "r") as file:
						data = file.read()
						file_size = len(data)
						if file_size > (2**32 - 1):
							print("File too large")
							raise IOError
						FS = file_size.to_bytes(4, byteorder='big')
						request = byte1 + filename.encode() + FS
						clientSocket.send(request)
						clientSocket.send(data.encode())
				except IOError:  # Error in reading or writing data
					print("Error in reading or writing data")
			case "get":
				opcode = 0b001 << 5
				filename = separated_commands[1]
				byte1 = (opcode | (len(filename) + 1)).to_bytes(1, byteorder='big')
				request = byte1 + filename.encode()
				clientSocket.send(request)
			case "change":
				opcode = 0b010 << 5
				oldFilename = separated_commands[1]
				newFilename = separated_commands[2]
				byte1 = (opcode | (len(oldFilename) + 1)).to_bytes(1, byteorder='big')
				request = byte1 + oldFilename.encode() + (len(newFilename) + 1).to_bytes(1,
																						 byteorder='big') + newFilename.encode()
				clientSocket.send(request)
			case "help":
				opcode = 0b01100000
				request = opcode.to_bytes(1, byteorder='big')
				clientSocket.send(request)
			case "bye":
				print("BYE!")
				clientSocket.close()
				break
			case _:
				raise IndexError

		# print(f"command = {request}")

		# Receive response from server and parse it for the response
		response = clientSocket.recv(1024)
		# print(f"raw response = {response}")
		res_byte1 = response[0]
		res_code = res_byte1 >> 5
		# print(f"res code = {res_code}")
		match res_code:
			case 0b000:  # Correct put and change request response
				print("Successful put or change")
			case 0b001:  # Correct get request response
				filename, filesize, success = parse_get_response(response)
				if not success:
					continue
				try:
					data = clientSocket.recv(filesize).decode()
					with open(filename, "w") as newfile:
						newfile.write(data)
				except IOError:  # Error in reading or writing data
					print("Error in reading or writing data")
					continue
				else:
					print("Successful get. File " + filename + " saved.")
			case 0b010:  # Error file not found response
				print("Error: file not found")
			case 0b011:  # Error unknown request response
				print("Error: unknown request")
			case 0b101:  # Error unsuccessful change response
				print("Error: file change unsuccessful")
			case 0b110:  # Help response
				message_length = res_byte1 & 0b00011111
				print(response[1:message_length].decode())

	except (IndexError):
		print("Error: Invalid command. Input a command and filename(s). Type <help> for commands.")
