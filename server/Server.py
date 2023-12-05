import socket
from time import sleep

from server.ServerWorker import ServerWorker

MAX_CONN = 5

def main(ipAddress,infoPort,isServer,isRP,rankServers,videostream):
	rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	rtspSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	rtspSocket.bind((ipAddress, infoPort))

	if isServer:
		print(f"\nRTSP Server listening at the address {ipAddress}:{infoPort}\n")
	else: 
		print(f"\nRTSP RP listening at the address {ipAddress}:{infoPort}\n")

	rtspSocket.listen(MAX_CONN)        

	nodesInterested = []

	if not isServer:
		while not rankServers:
			sleep(1)

	# Receive client info (address,port) through RTSP/TCP session
	while True:
		clientInfo = {}
		
		try:
			clientInfo['rtspSocket'] = rtspSocket.accept()
			
			nodesInterested.append(clientInfo)
			
			#while isRP and len(nodesInterested) != 2:
				#sleep(1)
			
			ServerWorker(isRP,rankServers,nodesInterested,videostream,ipAddress).run()	
		
		except Exception as e:
			print(f"[{e}]")
			break
	rtspSocket.close()