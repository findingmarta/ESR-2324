import sys, socket

from server.ServerWorker import ServerWorker

MAX_CONN = 5

def main(ipAddress,infoPort,isServer):
	rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	rtspSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	rtspSocket.bind((ipAddress, infoPort))

	if isServer:
		print(f"\nRTSP Server listening at the address {ipAddress}:{infoPort}\n")
	else:
		print(f"\nRTSP RP listening at the address {ipAddress}:{infoPort}\n")

	rtspSocket.listen(MAX_CONN)        

	# Receive client info (address,port) through RTSP/TCP session
	while True:
		clientInfo = {}

		try:
			clientInfo['rtspSocket'] = rtspSocket.accept()
			ServerWorker(clientInfo).run()		
		except Exception as e:
			print(f"Exception: [{e}]\n")
			break

	rtspSocket.close()