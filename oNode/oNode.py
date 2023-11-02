import socket, sys, os, json, threading

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from config.util import PORT
from server.Server import Server
from client.Client import Client

class oNode:

    def __init__(self, port, neighbours):
        self.ip = ''
        self.port = port
        self.neighbours = neighbours

    def createConnections(self):
        for neigh in self.neighbours:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Conectar-se ao servidor
            s.connect((neigh, PORT))

            msg = "Olá, mundo!"
            s.send(msg.encode())

            # Receber uma mensagem do servidor
            message = s.recv(1024)

            # Manipular a mensagem recebida
            resposta = message.decode('utf-8')
            print(resposta)

            # Fechar a conexão com o servidor
            s.close()

    
    def acceptConnections(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.ip, PORT))
            s.listen()

            while True:
                try:
                    conn, addr = s.accept()
                    msg = conn.recv(1024)
                    mensagem = msg.decode('utf-8')
                    print(f"Recebi uma mensagem do cliente {addr}")
                    print(mensagem)
                except UnicodeDecodeError:
                    #pass
                    s.close()
                    conn.close()            

                resp = "Adeus" 
                
                # O servidor tenta codificar a resposta para o cliente
                try:
                    resposta=resp.encode('utf-8')
                except UnicodeEncodeError:
                    print(f"Erro na codificação da resposta")
                    s.close()
                    conn.close()

                # O servidor envia a resposta para o cliente
                conn.sendto(resposta, addr)

        except:
            pass

    def start(self):
        self.createConnections()
        threading.Thread(target=self.acceptConnections)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: py oNode.py <config_file>")
        sys.exit(1)


    f = open('./config/'+sys.argv[1])
    data = json.load(f)

    isServer = data['isServer']
    port = data['port']
    neighbours = data['neighbours']

    if isServer:
        Server().main(port)
    else:
        Client().main()