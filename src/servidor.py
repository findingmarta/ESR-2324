import socket

class Servidor:
    # Inicializa o servidor
    def __init__(self, porta):
        self.porta = porta


    # Inicializa a comunicação TCP
    def communication(self):     
        # Inicializa o socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        endereco = '127.0.0.1'
        s.bind((endereco, self.porta))
        #s.bind(("", self.porta))
        s.listen()
        print(f"Servidor TCP à escuta no endereço {endereco}:{self.porta}")

        connection, address = s.accept()


        while True:
            try:
                msg = connection.recv(256)
                mensagem = msg.decode('utf-8')
                print(f"Recebi uma mensagem do cliente {address}")
                print(mensagem)
            except UnicodeDecodeError:
                pass

            # Transforma a query query em query string
            resp = "Adeus" 

            # O servidor tenta codificar a resposta para o cliente
            try:
                resposta=resp.encode('utf-8')
            except UnicodeEncodeError:
                print(f"Erro na codificação da resposta")

            # O servidor envia a resposta para o cliente
            connection.sendto(resposta, address)

    def start(self):
        self.communication()


Servidor(1234).start()