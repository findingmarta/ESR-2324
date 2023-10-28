import socket

class Cliente:
    def __init__(self, socket=None):
        self.socket = socket

    def communication(self):

        try:
            if self.socket is None:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect(("", ""))
                print("connect")

            with self.socket:
                #while True:
                    msg = "HI"
                    self.socket.sendall(msg.encode())                    

                    try:
                        msg = self.socket.recv(256)
                        infp = msg.decode('utf-8')
                        print(("", ""), infp)
                    
                    except:
                        pass

        except:
            print('Connection Failed', 'Connection to 127.0.0.1 failed.')


    def start(self):
        self.communication()

if __name__ == "__main__":
    Cliente().start()
