from datetime import datetime, time, timedelta
import socket, sys, os, json, threading
import struct
import time

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

import server.Server as Server
from client.Client import Client

INFO_PORT = 3000
RTP_PORT = 4000
FLOODING_PORT = 5000


""""
Estrutura da mensagem a ser enviada por flooding:

<ip do nodo>
<isServer>
<isRP>
<vizinhos>
<tempo>
<saltos>
<servidores mais próximos>
"""

MAX_HOPS = 10

# Estrutura da mensagem de prova
class Message:
    date_format = '%d-%m-%Y %H:%M:%S.%f'

    def __init__(self,ipAddress,isServer,isRP,neighbours,hops,time,lastRefresh,rankServers):
        self.ipAddress = ipAddress
        self.isServer = isServer
        self.isRP = isRP
        self.neighbours = neighbours
        self.hops = hops
        self.time = time
        self.lastRefresh
        self.rankServers = rankServers

    def to_json(message):
        # Converte os atributos do objeto em um dicionário
        message_dict = {
            "ipAddress": message.ipAddress,
            "isServer": message.isServer,
            "isRP": message.isRP,
            "neighbours": message.neighbours,
            "hops": message.hops,
            "time": [message.time[0].strftime(message.date_format), message.time[1].total_seconds()],
            "rankServers": message.rankServers
        }
        return json.dumps(message_dict)

    @classmethod
    def from_dict(cls,message):
        time = [datetime.strptime(message["time"][0], cls.date_format), timedelta(seconds=message["time"][1])]
        lastRefresh = datetime.strptime(message["lastRefresh"][0], cls.date_format)
        return cls(message["ipAddress"], message["isServer"], message["isRP"], message["neighbours"], message["hops"], time, lastRefresh, message["rankServers"])

    def listenMessage(self,sock):
        print(f"\n[Flooding socket listening at the address {self.ipAddress}:{FLOODING_PORT}]\n")

        while True:
            data = sock.recv(1024)
            m = json.loads(data)
            message = self.from_dict(m)

            print(f"[{self.ipAddress}:{FLOODING_PORT}] recieved: \n{m}.\n")

            if message.hops >= MAX_HOPS:
                print("\nReached the max number of hops!")
                break
            
            #tempo_str = message.time[0]
            #refresh_str = message['last_refresh']
            #message.time[0] = datetime.strptime(tempo_str.replace('T', ' '), self.date_format)
            #message['last_refresh'] = datetime.strptime(refresh_str.replace('T', ' '), self.date_format)

            response_time = datetime.now() - message.time[0]
            message.time[1] = response_time

                       

            #
            self.flood(sock,message)

        sock.close()

    # Sends a message to a server
    def send_message(self,sock,server_ip,message):
        # Converts the message to a json format
        m = message.to_json()      

        # Sends the message
        sock.sendto(m.encode(), (server_ip, FLOODING_PORT))

    # Flooding
    def flood(self,sock,message):
        for server_ip in message.neighbours:
            print(f"\n[{message.ipAddress} sent a message to {server_ip}:{FLOODING_PORT}]\n")
            self.send_message(sock,server_ip,message)
        #m = self.to_json
        #print(f"AA {self.to_json(message)}")
        print(f"Message:\n{message.to_json()}\n\n")
        print("----------------------------------------------------------------------------")

    # 
    def refresh(self,sock,message):
        # First flooding process
        self.flood(sock,message)

        # Every 30 seconds a new flooding process starts with updated message
        while True:
            #print(f"local info:\n{json.dumps(message['rankServers'], indent=4)}\n\n")
            time.sleep(30)
            #self.refreshMessage()
            message.flood(sock,message)

    def refreshMessage():
        print("A")

    def handler(message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((message.ipAddress, FLOODING_PORT))

        send = threading.Thread(target=message.refresh, args=(sock,message))
        receive = threading.Thread(target=message.listenMessage, args=(sock,))

        receive.start()
        send.start()

        receive.join()
        send.join()



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: py oNode/oNode.py <config_file>")
        sys.exit(1)

    # Open the node's configuration file
    f = open('./config/'+sys.argv[1])
    data = json.load(f)

    # Variables
    ipAddress = data['ipAddress'] 
    isServer = data['isServer']
    isRP = data['isRP']
    neighbours = data['neighbours']
    filename = "movie.Mjpeg" 

    # Create the message to send to active nodes
    message = Message(ipAddress, isServer, isRP, neighbours, hops=0, time=[datetime.now(), timedelta(days=0, hours=0, seconds=0)], lastRefresh=datetime.now(),rankServers=[])

    # Starts the flooding process
    Message.handler(message)


    #lock = threading.Lock()

    # Create a Server if the node is a server or a RP to receive requests and send files
    #if isServer or isRP:
    #    streamingServer = threading.Thread(target=lambda: Server.main(ipAddress,INFO_PORT,isServer))
    #    streamingServer.start()

    # Create a Client if the node is a client ou a RP to send requests
    #if not isServer:
    #    for ip_neigh in neighbours:
    #        streamingClient = threading.Thread(target=Client.main, args=(ip_neigh, INFO_PORT, RTP_PORT, filename))
    #        streamingClient.start()

    #if isServer or isRP:
    #    streamingServer.join()
    #else:
    #    streamingClient.join()