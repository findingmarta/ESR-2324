from random import randint
import sys, threading, socket, os
from time import sleep

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from RTP.VideoStream import VideoStream
from RTP.RTPPacket import RTPPacket

class ServerWorker:
	# Requests
	SETUP = "SETUP"
	PLAY = "PLAY"
	PAUSE = "PAUSE"
	TEARDOWN = "TEARDOWN"
	
	# RTSP State
	INIT = 0
	READY = 1
	PLAYING = 2
	#state = INIT

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2
		
	def __init__(self, isRP,rankServers,nodesInterested,videostream,ipAddress):
		self.isRP = isRP
		self.rankServers = rankServers
		self.nodesInterested = nodesInterested
		self.videostream = videostream
		self.ipAddress = ipAddress
		self.ip_neigh = None

		
	def changeStream(self,streamSocket):
		print(f"\nChanging stream connection to {self.ip_neigh}:6000\n")

		message = 'Change Stream'
		streamSocket.send(message.encode('utf-8'))
		self.videostream = None


	def receiveStream(self):
		self.ip_neigh = self.rankServers[0][0]
		streamSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		streamSocket.connect((self.ip_neigh, 6000))
		print(f"\nStream socket connecting to {self.ip_neigh}:6000\n")

		while len(self.nodesInterested) != 0:
			print("\nServer's Rank: " + str(self.rankServers))

			# Change the streaming provider of the RP if necessary
			if self.isRP:
				# Get the first server with a valid path
				time1,index1 = next(((time, index) for index, (_, time, _, _, server_path) in enumerate(self.rankServers) if server_path), 0)
				# Get the actual server
				time2 = next((time for (ip, time, _, _, _) in self.rankServers if ip == self.ip_neigh), 0)
				
				# If the ranking changed...
				if time2 > time1:
						self.ip_neigh = self.rankServers[index1][0]
						
						self.changeStream(streamSocket)
					
						sleep(30)

						# Receive the new stream
						streamSocket.close()
						streamSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
						streamSocket.connect((self.ip_neigh, 6000))

			try:
				# Envia uma mensagem ao servidor
				message = 'Stream request'
				streamSocket.send(message.encode('utf-8'))
				print(f"\nMessage: {message}")

				reply = streamSocket.recv(1024)
				
				if reply: 
					# Deserialize the VideoStream object
					self.videostream = VideoStream.deserialize(reply)

					print(f"VideoStream received from {self.videostream.ipAddress}")
					print(f"File: {self.videostream.filename}")
					sleep(15)
				
				else:
					print("No reply received! Retrying...")
					sleep(15)
			except Exception as e:
				print(f"[{e}]")
				break
			
		print("No more clients interested in the stream. Closing...")
		message = 'Close streaming'
		streamSocket.send(message.encode('utf-8'))
		self.videostream = None
		streamSocket.close()

	# Server server opens a socket to send a stream
	def listeningStreamRequest(self):	
		streamSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		streamSocket.bind((self.ipAddress, 6000))

		print(f"\nStream socket listening at {self.ipAddress}:6000\n")
		
		while True:
			try:
				req, adr = streamSocket.recvfrom(256)
				
				# Send the stream
				if req == b'Stream request':
					print(f"\nStream request from server {adr}")

					if self.videostream is None:
						print("No video stream available")
						continue
					
					else:
						# Serialize the VideoStream object
						stream_serialized = self.videostream.serialize()

						print(f"Sending stream to {adr}")

						# Send the serialized object over the socket
						streamSocket.sendto(stream_serialized, adr)
				
				elif req == b'Close streaming': 
					for clientInfo in self.nodesInterested:
						if clientInfo['rtspSocket'][1][0] == adr[0]:
							self.nodesInterested.remove(clientInfo)
							print(f"Client {adr[0]} left the streaming service")
				
				elif req == b'Change Stream':
					for clientInfo in self.nodesInterested:
						if clientInfo['rtspSocket'][1][0] == adr[0]:
							sockRTSP = clientInfo['rtspSocket'][0]
							
							self.nodesInterested.remove(clientInfo)

							message = 'Change Stream'
							sockRTSP.send(message.encode('utf-8'))
			except Exception as e:
				print(f"[{e}]")
				break						
				
		streamSocket.close()

	def handleClient(self,clientInfo):
			print(f"New client: {clientInfo['rtspSocket'][1]}")

			threading.Thread(target=self.recvRtspRequest, args=(clientInfo,)).start()

	def run(self):
		threading.Thread(target=self.listeningStreamRequest).start()

		if self.videostream is None:
			threading.Thread(target=self.receiveStream).start()
		
		while self.videostream is None:
			sleep(1)

		if self.videostream is not None:			
			for clientInfo in self.nodesInterested:
				clientInfo['state'] = self.INIT
				threading.Thread(target=self.handleClient, args=(clientInfo,)).start()

	
	def recvRtspRequest(self,clientInfo):
		"""Receive RTSP request from the client."""
		connSocket = clientInfo['rtspSocket'][0]
		while True:            
			data = connSocket.recv(1024)

			if data:
				print("Data received:\n" + data.decode("utf-8"))
				self.processRtspRequest(data.decode("utf-8"),clientInfo)
			else:
				#print('-'*60)
				#traceback.print_exc(file=sys.stdout)
				#print('-'*60)
				break
		
		connSocket.close()

	def processRtspRequest(self, data, clientInfo):
		"""Process RTSP request sent from the client."""
		# Get the request type
		request = data.split('\n')
		line1 = request[0].split(' ')
		requestType = line1[0]

		# Get the RTSP sequence number 
		seq = request[1].split(' ')[0]

		# Process SETUP request
		if requestType == self.SETUP:
			if clientInfo['state'] == self.INIT:			
				# Update state
				print("processing SETUP\n")   

				try:
					clientInfo['videostream'] = self.videostream 
					clientInfo['state']= self.READY
				except IOError:
					self.replyRTSP(self.FILE_NOT_FOUND_404, seq, clientInfo)
				
				# Generate a randomized RTSP session ID
				clientInfo['session'] = randint(100000, 999999)
				
				# Send RTSP reply
				self.replyRTSP(self.OK_200, seq, clientInfo)
				
				# Get the RTP/UDP port from the last line
				clientInfo['rtpPort'] = request[2].split(' ')[0]
		
		# Process PLAY request 		
		elif requestType == self.PLAY:
			if clientInfo['state'] == self.READY:
				print("processing PLAY\n")
				clientInfo['state'] = self.PLAYING
				
				# Create a new socket for RTP/UDP
				clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				
				self.replyRTSP(self.OK_200, seq, clientInfo)
				
				# Create a new thread and start sending RTP packets
				clientInfo['event'] = threading.Event()
				clientInfo['worker']= threading.Thread(target=self.sendRTP, args=(clientInfo,))
				clientInfo['worker'].start()
		
		# Process PAUSE request
		elif requestType == self.PAUSE:
			if clientInfo['state'] == self.PLAYING:
				print("processing PAUSE\n")
				clientInfo['state'] = self.READY
				
				clientInfo['event'].set()
			
				self.replyRTSP(self.OK_200, seq, clientInfo)
		
		# Process TEARDOWN request
		elif requestType == self.TEARDOWN:
			print("processing TEARDOWN\n")

			if 'event' in clientInfo.keys():
				clientInfo['event'].set()
			
			self.replyRTSP(self.OK_200, seq, clientInfo)

			# Remove client		
			self.nodesInterested.remove(clientInfo)

			print(f"\nClient {clientInfo['rtspSocket'][1]} left the streaming service")

			# Close the RTP socket
			clientInfo['rtpSocket'].close()

			
	def sendRTP(self,clientInfo):
		"""Send RTP packets over UDP."""
		while True:
			clientInfo['event'].wait(0.05) 
			
			# Stop sending if request is PAUSE or TEARDOWN
			if clientInfo['event'].isSet(): 
				break 
				
			data = clientInfo['videostream'].nextFrame()
			if data: 
				frameNumber = clientInfo['videostream'].frameNbr()
				try:
					address = clientInfo['rtspSocket'][1][0]
					port = int(clientInfo['rtpPort'])

					clientInfo['rtpSocket'].sendto(self.makeRTP(data, frameNumber),(address,port))
				except:
					print("Connection Error")
					#print('-'*60)
					#traceback.print_exc(file=sys.stdout)
					#print('-'*60)

	def makeRTP(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0 
		
		rtpPacket = RTPPacket()
		
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return rtpPacket.getPacket()
		
	def replyRTSP(self, code, seq, clientInfo):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(clientInfo['session'])
			connSocket = clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			print(f"404 NOT FOUND.\n{clientInfo}\n")
			reply = 'RTSP/1.0 404 NOT_FOUND\nCSeq: ' + '\nSession: ' + str(clientInfo['session'])
			conn_socket = (clientInfo['rtspSocket'])[0]
			conn_socket.send(reply.encode())
		elif code == self.CON_ERR_500:
			print(f"500 CONNECTION ERROR.\n{clientInfo}\n")
			reply = 'RTSP/1.0 500 CONNECTION_ERROR\nCSeq: ' + '\nSession: ' + str(clientInfo['session'])
			conn_socket = (clientInfo['rtspSocket'])[0]
			conn_socket.send(reply.encode())
