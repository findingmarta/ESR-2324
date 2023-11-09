from tkinter import *
import sys, os, threading

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from client.ClientWorker import ClientWorker

# Set the DISPLAY environment variable to :0.0
os.environ['DISPLAY'] = ':0.0'

class Client:	
    def main(ip_neigh,infoPort,rtpPort,filename):
        print(f'\nRTSP Client connecting to the address {ip_neigh}:{infoPort}')
        print(f'\nRTP Client connecting to the address {ip_neigh}:{rtpPort}')
        print("----------------------------------")
        root = Tk()

        # Create a new client
        try:
            app = ClientWorker(root,ip_neigh,infoPort,rtpPort,filename)
            app.master.title("RTPClient")	
            root.wait_visibility()
            root.mainloop()        
        except:
            pass