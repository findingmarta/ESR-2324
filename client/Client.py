from time import sleep
from tkinter import *
import sys, os

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from client.ClientWorker import ClientWorker

# Set the DISPLAY environment variable to :0.0
os.environ['DISPLAY'] = ':0.0'

class Client:	
    def main(infoPort,rtpPort,isRP,isBigNode,rankServers,filename_request,lock):
        while not rankServers:
            sleep(1)       

        root = Tk()
        
        while isRP and len(rankServers) != 2:
            sleep(1)

        lock.acquire()

        #print("Client's Rank: " + str(rankServers))

        ip_neigh = rankServers[0][0]	

        print(f'\nRTSP Client connecting to the address {ip_neigh}:{infoPort}\n')
        #print(f'\nRTP Client connecting to the address {ip_neigh}:{rtpPort}')

        lock.release()

        # Create a new client
        app = ClientWorker(root,ip_neigh,infoPort,rtpPort,filename_request,rankServers,isRP)
        
        if not isRP and not isBigNode:
            app.master.title("RTPClient")	
            root.wait_visibility()
            root.mainloop()
        sleep(2)