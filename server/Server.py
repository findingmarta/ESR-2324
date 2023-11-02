import socket, sys, os, time

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from config.util import PORT


class Server:
    # Inicializa o servidor
    def __init__(self, ip):
        self.ip = ip


    # Inicializa a comunicação TCP
    def communication(self):     
        # Inicializa o socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.bind((self.ip, PORT))
        s.listen()
        print(f"Servidor TCP à escuta no endereço: {self.ip}:{PORT}")

        connection, address = s.accept()


        while True:
            try:
                msg = connection.recv(1024)
                mensagem = msg.decode('utf-8')
                print(f"Recebi uma mensagem do cliente {address}")
                print(mensagem)
            except UnicodeDecodeError:
                #pass
                s.close()
                connection.close()            

            resp = "Adeus" 
            
            # O servidor tenta codificar a resposta para o cliente
            try:
                resposta=resp.encode('utf-8')
            except UnicodeEncodeError:
                print(f"Erro na codificação da resposta")
                s.close()
                connection.close()

            # O servidor envia a resposta para o cliente
            connection.sendto(resposta, address)

        s.close()
        connection.close()

    def start(self):
        self.communication()


Server(sys.argv[1]).start()