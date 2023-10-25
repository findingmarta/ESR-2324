import socket

class servidor:
    # Inicializa o servidor
    def __init__(self, porta):
        self.porta = porta


    # Inicializa a comunicação UDP???????????????????????????????????????????????
    def communication(self):
        # Inicializa o socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        endereco = '127.0.0.1'
        s.bind((endereco, self.porta))
        print(f"Servidor UDP à escuta no endereço {endereco}:{self.porta}")

        while True:
            msg, address = s.recvfrom(1024)
            print(f"Recebi uma mensagem do cliente {address}")


            try:
                mensagem = msg.decode('utf-8')
                print(mensagem)
            except UnicodeDecodeError:
                print(f"Erro 3: erro na descodificação da mensagem")


            # Transforma a query query em query string
            resp = "Adeus" 

            # O servidor tenta codificar a resposta para o cliente
            try:
                resposta =resp.encode('utf-8')
            except UnicodeEncodeError:
                print(f"Erro na codificação da resposta")

            # O servidor envia a resposta para o cliente
            s.sendto(resposta, address)

def main():
    server = servidor(1234)
    servidor.communication(server)

if __name__ == "__main__":
    main()