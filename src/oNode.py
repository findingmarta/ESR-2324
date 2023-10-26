import socket
import threading
import sys

class oNode:

    def __init__(self, port, mode):
        self.port = port
        self.mode = mode

    def run_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("localhost", self.port))
        self.sock.listen()
        try:
            while True:
                conn, addr = self.sock.accept()
                print("Nova conexão de {}:{}".format(addr[0], addr[1]))
                threading.Thread(target=self.handle_connection, args=(conn,)).start()
        except KeyboardInterrupt:
            print("Servidor encerrado.")
            self.sock.close()
    
    def run_client(self):
        # Conectar-se ao servidor
        self.sock.connect("localhost", 8080)
        # Enviar uma mensagem para o servidor
        self.sock.send("Olá, mundo!")
        # Receber uma mensagem do servidor
        message = self.receive()
        # Manipular a mensagem recebida
        print(message)
        # Fechar a conexão com o servidor
        self.sock.close()

    def handle_connection(self, conn):
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print("Recebido de {}:{}".format(conn.getpeername()[0], conn.getpeername()[1]))
                conn.sendall(data)
        except Exception as e:
            print("Erro na conexão:", e)
        finally:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: py oNode.py [S|C] <porta>")
        sys.exit(1)

    mode = sys.argv[1]
    port = int(sys.argv[2])

    if mode == "S":
        print("Executando como servidor...")
        node = oNode(port, mode)
        node.run_server()
    elif mode == "C":
        print("Executando como cliente...")
        node = oNode(port, mode)
        node.run_client()
    else:
        print("Modo inválido. Use 'S' para servidor ou 'C' para cliente.")