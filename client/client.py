# COEN 366 Project Winter 2022
# By Jonathan Perlman 40094762
# client.py
# I, Jonathan Perlman, am the sole author and contributor of this file "client.py"
# Requires python version >= 3.10 to run
import os
import sys
import time
from math import ceil
from socket import *


def parse_get_response(response):
	try:
		# Extract FL (filename length) from first byte of response
		response_byte1 = response[0]
		resp_code = response_byte1 >> 5
		FL = response_byte1 & 0b00011111
		# Extract filename based on FL
		filename = response[1:FL].decode()
		FS = int.from_bytes(response[FL:FL + 5], byteorder='big')
		success = 1
		if debugMode:
			print(
				f"message received from server: response code = {resp_code}, FL = {FL}, filename = {filename}, FS = {FS}")
			print(f"raw message received from server: {response.decode()}")
		return filename, FS, success
	except Exception:
		print("Error: cannot process server response")
		return "", 0, 0


try:
	serverIP = sys.argv[1]
	serverPort = int(sys.argv[2])
	debugMode = False
	if int(sys.argv[3]) > 0:
		debugMode = True
except IndexError:
	raise SystemExit(f"Usage: {sys.argv[0]} <server IP> <port> <Debug mode (0 or 1)>")

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverIP, serverPort))

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
					file_size = os.stat(filename).st_size
					# print(f"file size = {file_size}")
					if file_size > (2 ** 32 - 1):
						print("File too large!")
						raise IOError
					FS = file_size.to_bytes(4, byteorder='big')
					request = byte1 + filename.encode() + FS
					clientSocket.send(request)
					time.sleep(0.2)
					number_of_chunks = ceil(file_size / 4096)
					with open(filename, "rb") as file:
						for i in range(0, number_of_chunks):
							data = file.read(4096)
							if data:
								clientSocket.send(data)
							else:
								raise IOError
				except (IOError, FileNotFoundError):  # Error in reading or writing data
					print("Error in reading or writing data")
					raise Exception

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
				if debugMode:
					print(f"message received from server: response code = {res_code}")
					print(f"raw message received from server: {response.decode()}")
				print("Successful put or change")
			case 0b001:  # Correct get request response
				filename, filesize, success = parse_get_response(response)
				if not success:
					continue
				try:
					number_of_chunks = ceil(filesize / 4096)
					with open(filename, "wb") as newfile:
						for i in range(0, number_of_chunks):
							data = clientSocket.recv(4096)
							newfile.write(data)
				except IOError:  # Error in reading or writing data
					print("Error in reading or writing data")
					continue
				else:
					print("Successful get. File " + filename + " saved.")
			case 0b010:  # Error file not found response
				if debugMode:
					print(f"message received from server: response code = {res_code}")
					print(f"raw message received from server: {response.decode()}")
				print("Error: file not found")
			case 0b011:  # Error unknown request response
				if debugMode:
					print(f"message received from server: response code = {res_code}")
					print(f"raw message received from server: {response.decode()}")
				print("Error: unknown request")
			case 0b101:  # Error unsuccessful change response
				if debugMode:
					print(f"message received from server: response code = {res_code}")
					print(f"raw message received from server: {response.decode()}")
				print("Error: file change unsuccessful")
			case 0b110:  # Help response
				message_length = res_byte1 & 0b00011111
				if debugMode:
					print(
						f"message received from server: response code = {res_code}, message length = {message_length}")
					print(f"raw message received from server: {response.decode()}")
				print(response[1:message_length].decode())

	except (IndexError, Exception):
		print(
			"Error: Invalid command or server response. Input a valid command and filename(s). Type <help> for commands.")
