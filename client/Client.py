import socket, sys, os, time

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from config.util import PORT
from tkinter import Tk

class Client:
    def __init__(self, ip):
        self.ip = ip

    def communication(self):

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.ip, PORT))
            print("connect")               


            while True:
                msg = "HI"
                s.sendall(msg.encode())  
                
                try:
                    msg = s.recv(1024)
                    resposta = msg.decode('utf-8')
                    print(f"Recebi uma resposta do servidor: {resposta}")
                
                except:
                    #pass
                    s.close()
            
                time.sleep(5)
            
            s.close()
        except:
            print('Connection Failed')
            s.close()



    def start(self):
        self.communication()


from Client import Client


if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpPort = sys.argv[3]
		fileName = sys.argv[4]	
	except:
		print("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")	
	
	root = Tk()
	
	# Create a new client
	app = Client(root, serverAddr, serverPort, rtpPort, fileName)
	app.master.title("RTPClient")	
	root.mainloop()


    #Client(sys.argv[1]).start()
