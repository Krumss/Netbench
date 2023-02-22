#!/usr/bin/python3

import socket
import os.path
import sys
from time import perf_counter

# set port number
# default is 41511 if no input argument
port = 41511

def server():
	# create socket and bind
	sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		sockfd.bind(('', port))
	except socket.error as emsg:
		print("Socket bind error: ", emsg)
		sys.exit(1)
	print("Start as server node")
	hostname=socket.gethostname()   
	IPAddr=socket.gethostbyname(hostname) 
	# listen and accept new connection
	sockfd.listen(5)
	print("Server is ready. Listening address: (\'" + str(IPAddr) +"\', " + str(port) + ")")
	try:
		conn, addr = sockfd.accept()
	except socket.error as emsg:
		print("Socket accept error: ", emsg)
		sys.exit(1)

	# print out peer socket address information
	print("Connection established. Here is the remote peer info:", addr)
	test1R(conn)
	
	# close connection
	print("[Completed]")
	sockfd.close()
	conn.close()

def client(argv):

	# create socket and connect to server
	print(argv[1])
	try:
		sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sockfd.connect((argv[1], port))
	except socket.error as emsg:
		print("Socket error: ", emsg)
		sys.exit(1)

	# once the connection is set up; print out 
	# the socket address of your local socket
	print("Connection established. My socket address is", sockfd.getsockname())

	test1(sockfd)
	sockfd.close()

def test1(sock):
	# send file name and file size as one string separate by ':'
	# e.g., socketprogramming.pdf:435678
	print("Start sending ...")
	t1_start = perf_counter()
	for i in range(200000):
		smsg = bytearray(os.urandom(1000))
		try:
			sock.sendall(smsg)
		except socket.error as emsg:
			print("Socket sendall error: ", emsg)
			sys.exit(1)

	rmsg = sock.recv(5)
	if rmsg != b"OK":
		print("Received a negative acknowledgment")
		sys.exit(1)
	t1_stop = perf_counter()
	print("Elapsed time:", t1_stop-t1_start)
	print("Throughput: "+str(200 / (t1_stop-t1_start))+"Mb/s")
	print("[Completed]")

	#receive data
	print("Start receiving . . .")
	remaining = 200000000
	while remaining > 0:
		rmsg = sock.recv(1000)
		if rmsg == b"":
			print("Connection is broken")
			sys.exit(1)
		remaining -= len(rmsg)
	# send acknowledge - e.g., "OK"
	sock.send(b"OK")

def test1R(conn):
	remaining = 200000000

	# receive the file contents
	print("Start receiving . . .")
	while remaining > 0:
		rmsg = conn.recv(1000)
		if rmsg == b"":
			print("Connection is broken")
			sys.exit(1)
		remaining -= len(rmsg)
	# send acknowledge - e.g., "OK"
	conn.send(b"OK")

	#send data
	print("Start sending ...")
	t1_start = perf_counter()
	for i in range(200000):
		smsg = bytearray(os.urandom(1000))
		try:
			conn.sendall(smsg)
		except socket.error as emsg:
			print("Socket sendall error: ", emsg)
			sys.exit(1)

	rmsg = conn.recv(5)
	if rmsg != b"OK":
		print("Received a negative acknowledgment")
		sys.exit(1)
	t1_stop = perf_counter()
	print("Elapsed time:", t1_stop-t1_start)
	print("Throughput: "+str(200 / (t1_stop-t1_start))+"Mb/s")
	print("[Completed]")

if __name__ == '__main__':
	if len(sys.argv) > 2:
		print("Usage: FTserver [<Server_port>]")
		sys.exit(1)
	elif len(sys.argv) == 2:
		client(sys.argv)
	else:
		server()