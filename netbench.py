#Name: Wong Yat Kiu Kevin
#UID: 3035687493
#Development Platform: VSCode
#Python version: Python 3.11.2

import socket
import os.path
import sys
from time import perf_counter, sleep

port = 41511
largeData = bytearray(os.urandom(200000000))
smallData = bytearray(os.urandom(10000))

def server():
	# create and bind TCP socket
	sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		sockfd.bind(('', port))
	except socket.error as emsg:
		print("Socket bind error: ", emsg)
		sys.exit(1)

	# listen
	sockfd.listen(5)
	hostname=socket.gethostname()   
	IPAddr=socket.gethostbyname(hostname) 
	print("Server is ready. Listening address: (\'" + str(IPAddr) +"\', " + str(port) + ")")
	
	# try accept new connection
	try:
		conn, addr = sockfd.accept()
	except socket.error as emsg:
		print("Socket accept error: ", emsg)
		sys.exit(1)

	# print out peer socket address information
	print("A client has connected and it is at:", addr)

	# do test 1, 2
	test1S(conn)
	
	# close TCP socket
	sockfd.close()
	conn.close()

	# create and bind UDP socket
	udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		udpSock.bind(('', port))
	except socket.error as emsg:
		print("Socket bind error: ", emsg)
		sys.exit(1)

	#receive handshake msg from client and return "OK" msg
	indata, addr = udpSock.recvfrom(5)
	udpSock.sendto("OK".encode(), addr)
	
	# do test 3
	UDPTestR(udpSock, addr)

	# close UDP socket
	udpSock.close()

def client(argv):
	# create TCP socket and try connect to server
	try:
		sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sockfd.connect((argv[1], port))
	except socket.error as emsg:
		print("Socket error: ", emsg)
		sys.exit(1)

	# print address of server and client
	pair = (argv[1], port)
	clientAddr = sockfd.getsockname()
	print("Client has connected to server at:", pair)
	print("Client's address:", clientAddr)

	# do test 1, 2
	test1C(sockfd)

	# close TCP socket
	sockfd.close()

	# create and bind UDP socket
	try:
		udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error as emsg:
		print("Socket error: ", emsg)
		sys.exit(1)
	try:
		udpSock.bind(clientAddr)
	except socket.error as emsg:
		print("Socket bind error: ", emsg)
		sys.exit(1)

	# sleep 1s to ensure server is ready
	sleep(1)

	# send handshake msg to ensure server is here
	udpSock.sendto("Test".encode(), pair)
	indata, addr = udpSock.recvfrom(5)
	if indata.decode() != "OK":
		print("Received a negative acknowledgment")
		sys.exit(1)

	# do test 3
	UDPTest(udpSock, pair)

	# close UDP socket
	udpSock.close()

def sendTCP(sock, msg, needProgressBar):
	# send length of msg to other side
	confirmMsg=str(len(msg))
	sock.send(confirmMsg.encode('ascii'))

	#receive "OK" msg
	rmsg = sock.recv(50)
	if rmsg != b"OK":
		print("Received a negative acknowledgment")
		sys.exit(1)

	# create a progress bar if needed
	if needProgressBar:
		bar = ProgressBar(max=len(msg)/10000)

	# start timer
	t1_start = perf_counter()

	# send msg
	for i in range(int(len(msg)/10000)):
		smsg = msg[i*10000:(i+1)*10000]
		try:
			sock.sendall(smsg)
		except socket.error as emsg:
			print("Socket sendall error: ", emsg)
			sys.exit(1)
		#if has progress bar, increment it
		if needProgressBar:
			bar.increment()

	# receive the small msg
	rmsg = sock.recv(5)
	if rmsg != b"OK":
		print("Received a negative acknowledgment")
		sys.exit(1)

	# stop timer
	t1_stop = perf_counter()

	# print info
	print("Sent total: ", len(msg), " bytes")
	print("Elapsed time: %.3f s" %(t1_stop-t1_start))
	print("Throughput(from server to client): %.3f Mb/s" %(len(msg)/125000/(t1_stop-t1_start)))

def receiveTCP(sock):
	# receive msg of length of msg
	try:
		rmsg = sock.recv(100)
	except socket.error as emsg:
		print("Socket recv error: ", emsg)
		sys.exit(1)
	if rmsg == b'':
		print("Connection is broken")
		sys.exit(1)
	length = int(rmsg.decode("ascii"))

	# send back "OK"
	sock.send(b"OK")

	# start receive msg
	remaining = length
	while remaining > 0:
		rmsg = sock.recv(10000)
		if rmsg == b"":
			print("Connection is broken")
			sys.exit(1)
		remaining -= len(rmsg)
	# send acknowledge "OK"
	sock.send(b"OK")

	#print info
	print("Received total: ", length, " bytes")

def test1S(sock):
	print("")
	print("Start test1 - large transfer")
	print("From server to client")
	sendTCP(sock, largeData, True)

	#receive data
	print("From client to server")
	receiveTCP(sock)

	print("")
	print("Start test2 - small transfer")
	print("From server to client")
	sendTCP(sock, smallData, False)

	print("From client to server")
	receiveTCP(sock)

def test1C(conn):
	print("")
	print("Start test1 - large transfer")
	print("From server to client")
	receiveTCP(conn)

	#send data
	print("From client to server")
	sendTCP(conn, largeData, True)

	print("")
	print("Start test2 - small transfer")
	print("From server to client")
	receiveTCP(conn)

	print("From client to server")
	sendTCP(conn, smallData, False)

def UDPTest(sock, pair):
	print("")
	print("Start test3 - UDP pingpong")
	print("From server to client")
	remaining = 5
	bar = ProgressBar(max=5)

	# receive msg
	while remaining > 0:
		indata, addrR = sock.recvfrom(5)
		sock.sendto(bytearray(os.urandom(5)), addrR)
		bar.increment()
		remaining-=1

	print("From client to server")

	# send msg
	sumTime = 0
	for i in range(5):
		# start timer
		t1_start = perf_counter()
		sock.sendto(bytearray(os.urandom(5)), pair)
		indata, addrR = sock.recvfrom(5)
		# stop timer
		t1_stop = perf_counter()
		sumTime += (t1_stop-t1_start)
		print("Reply from "+pair[0]+": time = %.4f s" %(t1_stop-t1_start))
	print("Average RTT: %.5f s" %(sumTime/5))
	print("End of all benchmarks")

def UDPTestR(sock, addr):
	print("")
	print("Start test3 - UDP pingpong")
	print("From server to client")
	# send msg
	sumTime = 0
	for i in range(5):
		# start timer
		t1_start = perf_counter()
		sock.sendto(bytearray(os.urandom(5)), addr)
		indata, addrR = sock.recvfrom(5)
		# stop timer
		t1_stop = perf_counter()
		sumTime += (t1_stop-t1_start)
		print("Reply from "+addr[0]+": time = %.4f s" %(t1_stop-t1_start))

	print("Average RTT: %.5f s" %(sumTime/5))

	print("From client to server")
	remaining = 5
	bar = ProgressBar(max=5)

	# receive msg
	while remaining > 0:
		indata, addrR = sock.recvfrom(5)
		sock.sendto(bytearray(os.urandom(5)), addrR)
		bar.increment()
		remaining-=1

	print("End of all benchmarks")

class ProgressBar: #display 20 space on screen
	def __init__(self, max=100) -> None:
		self.min = 0
		self.max = max
		self.step = 1
		self.curr = 0 #range: 0 to max
		print("[", " " * 20, "]", end="\r", sep="")

	def increment(self):
		oldNum = int(self.curr / self.max * 20)
		self.curr += self.step
		if oldNum != int(self.curr / self.max * 20):
			newNum = int(self.curr / self.max * 20)
			end = "\r"
			if self.curr == self.max:
				end = "\n"
			elif self.curr > self.max:
				return
			print("[", "=" * newNum, " " * (20 - newNum), "]", end=end, sep="") #19 - oldNum = 20 - (oldNum + 1)

if __name__ == '__main__':
	if len(sys.argv) > 2:
		print("Usage: FTserver [<Server_port>]")
		sys.exit(1)
	elif len(sys.argv) == 2:
		client(sys.argv)
	else:
		server()