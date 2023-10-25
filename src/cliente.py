import socket

class cliente:
    def communication():
        # Inicializa o socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Converte a query para string para que possa ser enviada
        mensagem = "Ola"

        while True:
            # Codifica a mensagem se estiver em modo debug
            try:
                mensagem = mensagem.encode('utf-8')
            except UnicodeEncodeError:
                print(f"Erro na codificação da query")

            # A query é enviada para o servidor com o endereço e porta definidos
            s.sendto(mensagem, ('127.0.0.1', 1234))
            s.send
            # O cliente recebe uma resposta do servidor
            resp, add = s.recvfrom(1024)

            # A resposta é descodificada 
            print(f"Recebi uma resposta do servidor {add}")
            
            try:
                resposta = resp.decode('utf-8')
                print(resposta)
            except UnicodeDecodeError:
                print(f"Erro na descodificação da resposta")



def main():
    cliente.communication()

if __name__ == "__main__":
    main()