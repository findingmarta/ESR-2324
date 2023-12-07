from datetime import datetime, time, timedelta
import socket, sys, os, json, threading
import logging
import time

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

import server.Server as Server
from client.Client import Client
from RTP.VideoStream import VideoStream

INFO_PORT = 3000
RTP_PORT = 4000
FLOODING_PORT = 5000

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
isBigNode = data['isBigNode']
neighbours = data['neighbours']
filename_request = "movie.Mjpeg"

# Estrutura da mensagem de prova
date_format = '%Y-%m-%d %H:%M:%S.%f'


# ----------------------------------------------------------------------------------------------------------------------------

log_filename = './logs/log'+str(logging.DEBUG)+'.log'
logging.basicConfig(filename=log_filename, level=logging.DEBUG)

# ----------------------------------------------------------------------------------------------------------------------------


# Create the message to send to active nodes
message = {
    "ipAddress": ipAddress,
    "isServer": isServer,
    "isRP": isRP,
    "isBigNode": isBigNode,
    "neighbours": neighbours,
    "sentTo": {},
    "receivedFrom": {},
    "time": [datetime.now(), timedelta(days=0, hours=0, seconds=0)],
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
    m['time'][0] = datetime.strptime(time_str.replace('T', ' '), date_format)
    return m


# ----------------------------------------------------------------------------------------------------------------------------


def convert_to_timedelta(data):
    parts = data.split(':')
    hours, minutes, rest = map(float, parts)
    seconds, microseconds = divmod(rest, 1)
    return timedelta(hours=hours, minutes=minutes, seconds=seconds, microseconds=int(microseconds * 1e6))

def updateRank(messageReceived):
    # Os servidores não atualizam o ranking
    if isServer:
        return
    
    # O RP não atualiza o ranking com os cliente, apenas com os servidores e outros RPs
    if isRP or isBigNode:
        if not messageReceived['isServer'] and not messageReceived['isRP'] and not messageReceived['isBigNode']:
            return

    #-------------------------------------------------------------------------------------------------
    # Update Loss %
    loss = 0
    if ipAddress in messageReceived["sentTo"].keys():
        n_sent = messageReceived["sentTo"][ipAddress]
        n_received = message["receivedFrom"][messageReceived["ipAddress"]]
        loss = round(1-(n_received/n_sent), 2)
        #print(n_received/n_sent)
    #-------------------------------------------------------------------------------------------------

    server_path = False


    # Verificar se o nodo a ser inserido já existe na lista
    ip_exists = any(messageReceived["ipAddress"] in sublist for sublist in message["rankServers"]) 

    # Se não existir inserimos
    neighbour_time = timedelta(days=0, hours=0, seconds=0)
    if not ip_exists:
        # Se o RP não tiver como vizinho o servidor que enviou a mensagem, então adiciona o tempo do vizinho do vizinho ao tempo do vizinho                    
        if isRP or isBigNode:
            if not messageReceived["isServer"]:
                # Procura o servidor na lista de vizinhos(ranking) do vizinho
                for index, (_,_,_,isserver,_) in enumerate(messageReceived["rankServers"]):
                    if isserver:
                        neighbour_time = convert_to_timedelta(messageReceived["rankServers"][index][1])
                        server_path = True
        
        message["rankServers"].insert(0,[messageReceived["ipAddress"],messageReceived["time"][1]+neighbour_time,loss,messageReceived["isServer"],server_path])
    
    # Se exitir atualizamos o valor do response time
    else:
        for index, (ip,time,_,_,_) in enumerate(message["rankServers"]):
            if ip == messageReceived["ipAddress"]:
                time = messageReceived["time"][1]
                message["rankServers"][index][1] = time
                message["rankServers"][index][2] = loss

                # Se o RP não tiver como vizinho o servidor que enviou a mensagem, então adiciona o tempo do vizinho do vizinho ao tempo do vizinho                    
                if isRP or isBigNode:
                    if not messageReceived["isServer"]:
                        for i, (_,_,_,isserver,_) in enumerate(messageReceived["rankServers"]):
                            if isserver:
                                neighbour_time = convert_to_timedelta(messageReceived["rankServers"][i][1])
                                neighbour_loss = messageReceived["rankServers"][i][2]
                                message["rankServers"][index][1] = time + neighbour_time
                                message["rankServers"][index][2] = loss + neighbour_loss
                                message["rankServers"][index][4] = True     
                        
    # Ordenar a lista
    message["rankServers"].sort(key=lambda x: (x[1], x[2])) # Sort by latency and loss

    #print(f"[{message['ipAddress']}] Server's Ranking:\n {message['rankServers']}\n\n")

    logging.info(f"[{message['ipAddress']}] Server's Ranking:\n{json.dumps(message['rankServers'], default=serialize, indent=4)}\n\n")


#    
def listenMessage(sock):
    logging.info(f"[{ipAddress}:{FLOODING_PORT} LISTENING]\n")

    #sock.settimeout(1)

    while True:
        data, adr = sock.recvfrom(1024)
        m = json.loads(data)

        messageReceived = deserialize(m)

        logging.info(f"[{ipAddress}] RECEIVED FROM [{adr[0]}]")
        logging.info(f"the message:{json.dumps(messageReceived, default=serialize)}\n\n\n")

        if adr[0] not in message["receivedFrom"].keys():
            message["receivedFrom"][adr[0]] = 1
        else:
            message["receivedFrom"][adr[0]] += 1

        response_time = datetime.now() - messageReceived["time"][0]
        messageReceived["time"][1] = response_time

        # Update ranking
        updateRank(messageReceived)

    sock.close()








# ----------------------------------------------------------------------------------------------------------------------------

# Sends a message to a server
def send_message(sock,neighAddress):
    # Converts the message to a json format
    m = json.dumps(message, default=serialize)

    if neighAddress not in message["sentTo"].keys():
        message["sentTo"][neighAddress] = 1
    else:
        message["sentTo"][neighAddress] += 1

    sock.sendto(m.encode(), (neighAddress, FLOODING_PORT))
    logging.info(f"[{ipAddress} SENT TO {neighAddress}]")
    logging.info(f"the message:{json.dumps(message, default=serialize)}\n\n")


# Flooding
def flood(sock):
    for neighAddress in message["neighbours"]:
            send_message(sock,neighAddress)


# Every 15 seconds a new flooding process starts with updated message 
def refreshMessage(sock):
    # First flooding process
    flood(sock)

    while True:        
        time.sleep(15)
        
        logging.info(f"[{ipAddress} is REFRESHING the flooding process.]\n")
        message["time"][0] = datetime.now()
        flood(sock)

#
def handler():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ipAddress, FLOODING_PORT))

    send = threading.Thread(target=refreshMessage, args=(sock,))
    receive = threading.Thread(target=listenMessage, args=(sock,))

    receive.start()
    send.start()

    receive.join()
    send.join()



# Starts the flooding process
startProcess =  threading.Thread(target=handler, args=())
startProcess.start()

lock = threading.Lock()

# Create a Server if the node is a server or a RP to receive requests and send files
if isServer:
    videostream = VideoStream(filename_request,ipAddress)
    streamingServer = threading.Thread(target=lambda: Server.main(ipAddress,INFO_PORT,isServer,isRP,message['rankServers'],videostream))
    streamingServer.start()

elif isRP or isBigNode:
    streamingServer = threading.Thread(target=lambda: Server.main(ipAddress,INFO_PORT,isServer,isRP,message['rankServers'],videostream=None))
    streamingServer.start()

# Create a Client if the node is a client ou a RP to send requests
if not isServer:
    streamingClient = threading.Thread(target=Client.main, args=(INFO_PORT,RTP_PORT,isRP,isBigNode,message['rankServers'],filename_request,lock))
    streamingClient.start()

startProcess.join()

if isServer or isRP or isBigNode:
    streamingServer.join()
else:
    streamingClient.join()