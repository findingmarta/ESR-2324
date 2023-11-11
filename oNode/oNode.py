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

# Estrutura da mensagem de prova
date_format = '%d-%m-%Y %H:%M:%S.%f'

# Create the message to send to active nodes
message = {
    "ipAddress": ipAddress,
    "isServer": isServer,
    "isRP": isRP,
    "neighbours": neighbours,
    "time": [datetime.now(), timedelta(days=0, hours=0, seconds=0)],
    "lastRefresh": datetime.now(),
    "rankServers": []
}

def to_json(message):
    # Converte os atributos do objeto em um dicionário
    message_dict = {
        "ipAddress": message.ipAddress,
        "isServer": message.isServer,
        "isRP": message.isRP,
        "neighbours": message.neighbours,
        "time": [message.time[0].strftime(message.date_format), message.time[1].total_seconds()],
        "lastRefresh": message.lastRefresh.strftime(message.date_format),
        "rankServers": message.rankServers
    }
    return json.dumps(message_dict)

def from_dict(cls,message):
    time = [datetime.strptime(message["time"][0], cls.date_format), timedelta(seconds=message["time"][1])]
    lastRefresh = datetime.strptime(message["lastRefresh"], cls.date_format)
    return cls(message["ipAddress"], message["isServer"], message["isRP"], message["neighbours"], time, lastRefresh, message["rankServers"])


# ----------------------------------------------------------------------------------------


def updateMessage(messageReceived):
    # Se o nodo atual for um servidor não interessa atualizar a lista de servidores mais próximos
    # porque ele vai comunicar apenas com o RP
    if isServer:
        return


    # Adiciona o servidor mais próximo
    if messageReceived.time[1] < message.time[1]:
        message.rankServers.insert(0,message.ipAddress)
    # Se o tempo for igual adicionamos o servidor com menor número de saltos

    message.lastRefresh = datetime.now()
    
def listenMessage(sock):
    print(f"\n[Flooding socket listening at the address {ipAddress}:{FLOODING_PORT}]\n")

    while True:
        data = sock.recv(1024)
        m = json.loads(data)
        messageReceived = from_dict(m)

        print(f"[{ipAddress}:{FLOODING_PORT}] recieved: \n{m}.\n")


        response_time = datetime.now() - messageReceived.time[0]
        messageReceived.time[1] = response_time

        updateMessage(messageReceived)

        # Floods the updated message
        flood(sock,messageReceived)

    sock.close()








# ----------------------------------------------------------------------------------------

# Sends a message to a server
def send_message(sock,neighAddress,message):
    # Converts the message to a json format
    m = message.to_json()      

    # Sends the message
    sock.sendto(m.encode(), (neighAddress, FLOODING_PORT))

# Flooding
def flood(sock,m):
    for neighAddress in m.neighbours:
        print(f"\n[{ipAddress} sent a message to {neighAddress}:{FLOODING_PORT}]\n")
        send_message(sock,neighAddress,m)
    #m = to_json
    #print(f"AA {to_json(message)}")
    print(f"Message:\n{m.to_json()}\n\n")
    print("----------------------------------------------------------------------------")

# Every 60 seconds a new flooding process starts with updated message 
def refreshMessage(sock):
    # First flooding process
    flood(sock,message)

    while True:
        print(f"local info:\n{json.dumps(message['rankServers'], indent=4)}\n\n")
        
        time.sleep(60)
        
        print(f"[{ipAddress} is refreshing the flooding process.]\n")
        message.time[0] = datetime.now()
        message.lastRefresh = datetime.now()
        flood(sock,message)


#
def handler(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((message.ipAddress, FLOODING_PORT))

    send = threading.Thread(target=refreshMessage, args=(sock,))
    receive = threading.Thread(target=listenMessage, args=(sock,))

    receive.start()
    send.start()

    receive.join()
    send.join()






    # Starts the flooding process
    handler(message)


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