from time import sleep
from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, os
from RTP.VideoStream import VideoStream 


current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from RTP.RTPPacket import RTPPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class ClientWorker:
	# RTSP state
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	# Request
	SETUP = "SETUP"
	PLAY = "PLAY"
	PAUSE = "PAUSE"
	TEARDOWN = "TEARDOWN"
	
	# Initiation..
	def __init__(self, master, neighaddress, serverport, rtpport, filename, rankServers,isRP):
		self.neighAddress = neighaddress # Endereço do vizinho mais próximo
		self.isRP = isRP
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename   # "movie.Mjpeg"
		self.connectToServer(master,change=False)
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.frameNbr = 0
		self.rankServers = rankServers


	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)		
		self.master.destroy() # Close the gui window
		#self.rtpSocket.close()
		try:
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Delete the cache image from video
		except:
			pass
		
	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RTPPacket()
					rtpPacket.decode(data)
					
					currFrameNbr = rtpPacket.seqNum()
											
					if currFrameNbr > self.frameNbr: # Discard the late packet
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet(): 
					break
				
				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		
		return cachename
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288) 
		self.label.image = photo
		
	def nextServer(self):
		# Get the index of the current server ip address
		for ip,_,_,_,server_path in self.rankServers:
			if ip != self.neighAddress and server_path:
				self.neighAddress = ip
				break 

	def recvChangeStreamRequest(self):
		print("Client waiting for Change Stream Request\n")
		while True:
			reply = self.rtspSocket.recv(1024)
		
			if reply == b'Change Stream':
				self.nextServer()

				self.rtspSocket.close()
				print("Changing to server: ", self.neighAddress)
				sleep(10)
				self.connectToServer(self.master,change=True)
				break

	def connectToServer(self,master,change):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		try:
			self.rtspSocket.connect((self.neighAddress, self.serverPort))

			if not change:
				self.master = master
				self.master.protocol("WM_DELETE_WINDOW", self.handler)
				self.createWidgets()			

			if self.isRP:
				threading.Thread(target=self.recvChangeStreamRequest).start()

		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.neighAddress)
			print('Connection to \'%s\' failed.' %self.neighAddress)
			print("----------------------------------")

	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		

		"""
		Request Message Format:

		<type of request> <filename>
		<sequence number>
		<RTP port>
		"""

		# Setup request
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = f"{self.SETUP} {self.fileName}\n{self.rtspSeq}\n{self.rtpPort}" 
			
			# Keep track of the sent request.
			self.requestSent = self.SETUP
		
		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number.
			self.rtspSeq += 1

			print('\nPLAY event\n')
			
			# Write the RTSP request to be sent.
			request = f"{self.PLAY} {self.fileName}\n{self.rtspSeq}\n{self.rtpPort}" 
			
			# Keep track of the sent request.
			self.requestSent = self.PLAY
		
		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number.
			self.rtspSeq += 1

			print('\nPAUSE event\n')
			
			# Write the RTSP request to be sent.
			request = f"{self.PAUSE} {self.fileName}\n{self.rtspSeq}\n{self.rtpPort}" 
			
			# Keep track of the sent request.
			self.requestSent = self.PAUSE
			
		# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			print('\nTEARDOWN event\n')
			
			# Write the RTSP request to be sent.
			request = f"{self.TEARDOWN} {self.fileName}\n{self.rtspSeq}\n{self.rtpPort}" 
			
			# Keep track of the sent request.
			self.requestSent = self.TEARDOWN
		else:
			return
		
		# Send the RTSP request using rtspSocket.
		destAddr = (self.neighAddress, self.serverPort)
		self.rtspSocket.sendto(request.encode('utf-8'), destAddr)
		
		print('\nData sent:\n' + request)
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			reply = self.rtspSocket.recv(1024)
		
			if reply: 
					self.parseRtspReply(reply.decode("utf-8"))
			
			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break	

	def nextNode(self):		
		# Get the index of the current server ip address
		for i, ip_time in enumerate(self.rankServers):
			if ip_time[0] == self.neighAddress:
				index = i
				break
		
		# Get the server ip address at the index
		if index == len(self.rankServers) - 1:
			return None
		else:
			return self.rankServers[index+1][0]

	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""

		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])
		
		code = int(lines[0].split(' ')[1])

		# In case an error occurs, the client tries to get the video from the next server
		if code == 404 or code == 500:
			next = self.nextNode()

			if next != None:
				self.neighAddress = next
			else:
				print("Video not available in any server...")

		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session
			
			# Process only if the session ID is the same
			if self.sessionId == session:
				if code == 200: 
					if self.requestSent == self.SETUP:
						# Update RTSP state.
						self.state = self.READY
						
						# Open RTP port.
						self.openRtpPort() 

					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
						print('\nPLAY sent\n')
					
					elif self.requestSent == self.PAUSE:
						self.state = self.READY
						
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
					
					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""

		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		
		try:
			# Bind the socket to the address using the RTP port given by the client user
			self.rtpSocket.bind(("", self.rtpPort))

			print('\nBind \n')
		except TimeoutError:
			print("Closing RTP socket...")
		except:
			tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
		else: # When the user presses cancel, resume playing.
			self.playMovie()
