import socket, sys, os, time

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from config.util import PORT

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

if __name__ == "__main__":
    Client(sys.argv[1]).start()
