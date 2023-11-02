from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import sys, os

current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(root_dir)

from client.ClientWorker import ClientWorker


class Client:	
    #def main(self):

    if __name__ == "__main__":
        try:
            serverAddr = sys.argv[1]
            serverPort = sys.argv[2]
            rtpPort = sys.argv[3]
            fileName = sys.argv[4]	
        except:
            print("[Usage: Client.py Server_name Server_port RTP_port Video_file]\n")	

        root = Tk()

        # Create a new client
        app = ClientWorker(root, serverAddr, serverPort, rtpPort, fileName)
        app.master.title("RTPClient")	
        root.mainloop()