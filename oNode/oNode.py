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
FLOODING_CONTROL_PORT = 6000

SET_TIMEOUT = 3

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


#if len(sys.argv) != 2:
    #print("Usage: py oNode/oNode.py <config_file>")
    #sys.exit(1)

# Open the node's configuration file
f = open('./config/'+sys.argv[1]+".json")
data = json.load(f)


# Variables
ipAddress = data['ipAddress'] 
isServer = data['isServer']
isRP = data['isRP']
neighbours = data['neighbours']
filename = "movie.Mjpeg"

# Estrutura da mensagem de prova
date_format = '%Y-%m-%d %H:%M:%S.%f'


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

def serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        return str(obj)
    return json.JSONEncoder().default(obj)

def deserialize(m):
    time_str = m['time'][0]
    refresh_str = m['lastRefresh']
    m['time'][0] = datetime.strptime(time_str.replace('T', ' '), date_format)
    m['lastRefresh'] = datetime.strptime(refresh_str.replace('T', ' '), date_format)
    return m


# ----------------------------------------------------------------------------------------------------------------------------


#
#def updateNeighbours(messageReceived, tag):
#    for neigh_info in message["neighbours"]:
#        if neigh_info[0] == messageReceived["ipAddress"]:
#            neigh_info[1] = tag

#
def updateRank(messageReceived):
    # Verificar se o nodo a ser inserido já existe na lista
    ip_exists = any(messageReceived["ipAddress"] in sublist for sublist in message["rankServers"]) 

    # Se não existir inserimos
    if not ip_exists:
        message["rankServers"].insert(0,[messageReceived["ipAddress"],messageReceived["time"][1]])
    # Se exitir atualizamos o valor do response time
    else:
        for ip_time in message["rankServers"]:
            if ip_time[0] == messageReceived["ipAddress"]:
                ip_time[1] = messageReceived["time"][1]
                
                #message["rankServers"].insert(0,[messageReceived["ipAddress"],messageReceived["time"][1]])

    # Ordenar a lista
    message["rankServers"].sort(key=lambda x: x[1])

    print(f"Servers Ranking:\n{json.dumps(message['rankServers'], default=serialize, indent=4)}\n\n")
    print("----------------------------------------------------------------------------")



#    
def listenMessage(sock):
    print(f"\n[Flooding socket LISTENING at the address {ipAddress}:{FLOODING_PORT}]\n")

    #sock.settimeout(1)

    while True:
        data, adr = sock.recvfrom(1024)
        m = json.loads(data)

        messageReceived = deserialize(m)

        # Se o nodo atual for um servidor não interessa atualizar a lista de servidores mais próximos porque ele vai comunicar apenas com o RP
        #if isServer or messageReceived["ipAddress"] == ipAddress:
            #return 

        print(f"[{ipAddress}:{FLOODING_PORT}] RECEIVED FROM {adr}: \n{messageReceived}\n")

        response_time = datetime.now() - messageReceived["time"][0]
        messageReceived["time"][1] = response_time

        # Update ranking
        updateRank(messageReceived)

        # Floods the updated message
        #flood(sock,messageReceived)

    sock.close()








# ----------------------------------------------------------------------------------------------------------------------------

# Sends a message to a server
def send_message(sock,neighAddress,message):
    # Converts the message to a json format
    m = json.dumps(message, default=serialize)

    sock.sendto(m.encode(), (neighAddress, FLOODING_PORT))
    print(f"\n[{ipAddress} SENT a message TO {neighAddress}:{FLOODING_PORT}]\n")


# Flooding
def flood(sock,m):
    for neighAddress in m["neighbours"]:
            send_message(sock,neighAddress,m)

    print(f"Message:\n{json.dumps(m, default=serialize)}\n\n")
    print("----------------------------------------------------------------------------")

# Every 60 seconds a new flooding process starts with updated message 
def refreshMessage(sock):
    # First flooding process
    flood(sock,message)

    while True:        
        time.sleep(15)
        
        print(f"[{ipAddress} is REFRESHING the flooding process.]\n")
        message["time"][0] = datetime.now()
        message["lastRefresh"] = datetime.now()
        flood(sock,message)


#
def handler():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ipAddress, FLOODING_PORT))

    #if isServer or isRP:
    #    if ipAddress not in message['rankServers']:
    #        message['rankServers'].insert(0, [ipAddress,timedelta(days=0, hours=0, seconds=0)])

    send = threading.Thread(target=refreshMessage, args=(sock,))
    receive = threading.Thread(target=listenMessage, args=(sock,))

    receive.start()
    send.start()

    receive.join()
    send.join()




# ----------------------------------------------------------------------------------------------------------------------------


# Starts the flooding process
startProcess =  threading.Thread(target=handler, args=())
startProcess.start()

lock = threading.Lock()

# Create a Server if the node is a server or a RP to receive requests and send files
if isServer or isRP:
    streamingServer = threading.Thread(target=lambda: Server.main(ipAddress,INFO_PORT,isServer))
    streamingServer.start()

# Create a Client if the node is a client ou a RP to send requests
if not isServer:
    streamingClient = threading.Thread(target=Client.main, args=(message, INFO_PORT, RTP_PORT, filename))
    streamingClient.start()

startProcess.join()


if isServer or isRP:
    streamingServer.join()
else:
    streamingClient.join()