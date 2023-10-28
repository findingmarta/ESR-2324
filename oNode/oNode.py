import socket, sys, os, json, threading

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from config.util import PORT

class oNode:

    def __init__(self, neighbours, mode):
        self.ip = ''
        self.neighbours = neighbours
        self.mode = mode

    def run_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.ip, PORT))
        s.listen()
        print(f"Servidor TCP à escuta no endereço: {self.ip}:{PORT}")

        try:
            while True:
                conn, addr = s.accept()
                print("Nova conexão de {}:{}".format(addr[0], addr[1]))
                threading.Thread(target=self.handle_connection, args=(conn,addr)).start()
        except KeyboardInterrupt:
            print("Servidor encerrado.")
            s.close()
    
    def run_client(self):
        for neigh in self.neighbours:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Conectar-se ao servidor
            s.connect((neigh, PORT))
            # Enviar uma mensagem para o servidor
            msg = "Olá, mundo!"
            s.send(msg.encode())
            # Receber uma mensagem do servidor
            message = s.recv(1024)
            # Manipular a mensagem recebida
            resposta = message.decode('utf-8')
            print(resposta)
            # Fechar a conexão com o servidor
            s.close()

    def handle_connection(self, conn, addr):
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Recebido de :{addr}")
                conn.sendall(data)
        except Exception as e:
            print("Erro na conexão:", e)
        finally:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: py oNode.py <config_file> [S|C]")
        sys.exit(1)


    f = open('./config/'+sys.argv[1])
    neighbours = json.load(f)

    mode = sys.argv[2]

    if mode == "S":
        print("Executando como servidor...")
        node = oNode(neighbours['neighbours'], mode)
        node.run_server()
    elif mode == "C":
        print("Executando como cliente...")
        node = oNode(neighbours['neighbours'], mode)
        node.run_client()
    else:
        print("Modo inválido. Use 'S' para servidor ou 'C' para cliente.")