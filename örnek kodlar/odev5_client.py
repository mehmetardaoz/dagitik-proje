import sys
import socket
import threading
import queue
import time

class loggerThread(threading.Thread):
    def __init__(self, name, logQueue, logFileName):
        threading.Thread.__init__(self)
        self.name = name
        self.lQueue = logQueue
        # dosyayi appendable olarak ac
        self.fid = open(logFileName, "a+")

    def log(self, message):
        # gelen mesaji zamanla beraber bastir
        t = time.ctime()
        print (t + ":" + message)
        self.fid.write(t + ":" + message + "\n")
        self.fid.flush()

    def run(self):
        self.log("Starting " + self.name)
        while True:
            if not self.lQueue.empty():
                to_be_logged = self.lQueue.get()
                self.log(to_be_logged)

class ReadThread (threading.Thread):
    def __init__(self, name, csoc, sendQueue, logQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.nickname = ""
        self.sendQueue = sendQueue
        self.message=""
        self.logQueue = logQueue

    def incoming_parser(self, data):
        liste = data.split("\n")
        if len(data) < 2:
            self.sendQueue.put("ERR")


        else:
            if data[0:3] == "SOK":
                print("Toplu mesaj gonderildi.")
                self.logQueue.put("Toplu mesaj gonderildi.")
                return 0

            elif data[0:3] == "SAY":
                print("Toplu mesaj gonderildi.")
                self.logQueue.put("Toplu mesaj gonderildi.")
                return 0

            elif data[0:3] == "ERL":
                print("Lutfen giris yapiniz.")
                self.logQueue.put("Lutfen giris yapiniz.")
                return 0

            elif data[0:3] == "ERR":
                print("Hatali komut girisi yapildi.")
                self.logQueue.put("Hatali komut girisi yapildi.")
                return 0

            elif data[0:3] == "HEL":
                rest = data[4:-1]
                self.logQueue.put(rest + " kullanici adiyla sisteme giris yapildi.")
                print(rest + " kullanici adiyla sisteme giris yapildi.")
                return 0

            elif data[0:3] == "REJ":
                rest = data[4:-1]
                print("Giris yapilamadi. " + rest + " adli kullanici zaten kayitli.")
                self.logQueue.put("Giris yapilamadi. '" + rest + "' adli kullanici zaten kayitli.")
                return 0

            elif data[0:3] == "MOK":
                self.logQueue.put("Ozel mesaj gonderildi.")
                return 0

            elif data[0:3] == "MNO":
                rest = data[4:-1]
                print(rest + " adli kullanici bulunamadi.")
                self.logQueue.put(rest + " adli kullanici bulunamadi.")
                return 0

            elif data[0:3] == "LSA":
                rest = data[4:-1]
                print("Kullanici listesi: " + rest)
                self.logQueue.put("Kullanici listesi: " + rest)
                return 0

            elif data[0:3] == "BYE":
                return -1

            elif "LSA" in liste:
                rest = data.split("\n")[0]
                print("Kullanici listesi: " + rest)
                self.logQueue.put("Kullanici listesi: " + rest)

                return 0


    def run(self):
        while True:

            data = self.csoc.recv(1024)
            self.message = self.incoming_parser(data.decode())
            if self.message==-1:
                break

        print("Sistemden başariyla cikildi.")
        s.close()

class InputThread(threading.Thread):
    def __init__(self, name, sendQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.sendQueue = sendQueue

    def run(self):
        queue_message = input("Komut giriniz: ")
        while True:
            self.sendQueue.put(queue_message)
            time.sleep(1)
            queue_message = input("Komut giriniz: ")

class SenderThread (threading.Thread):
    def __init__(self, name, csoc, sendQueue, logQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.sendQueue = sendQueue
        self.logQueue = logQueue

    def run(self):
        while True:
            msg = self.sendQueue.get()
            self.message = self.outgoing_parser(msg)

    def outgoing_parser(self,data):
        if(data[0:2]) == "/n":
            msg = "USR " + data[3:]
            self.csoc.send(msg.encode())

        if (data[0:2]) == "/l":
            msg = "LSQ"
            self.csoc.send(msg.encode())

        if (data[0:2]) == "/q":
            msg = "QUI"
            self.csoc.send(msg.encode())

        if (data[0:2]) == "/m":
            rest = data[3:]
            rest1 = rest.split(" ")
            user = rest1[0]
            rest1.pop(0)
            mesaj = ''
            for p in rest1:
                mesaj += p
                mesaj += ' '

            msg = "MSG " + user + ":" + mesaj
            self.csoc.send(msg.encode())

        if (data[0:2]) == "/s":
            msg = "SAY " + data[3:]
            self.csoc.send(msg.encode())

        pass


# log thread başlatılır
lQueue = queue.Queue()
lThread = loggerThread("Logger", lQueue, "log.txt")
lThread.start()


s = socket.socket()
host = "localhost"
port = 12345
s.connect((host,port))
sendQueue = queue.Queue(20)
# start threads
it = InputThread("InputThread", sendQueue)
it.daemon=True
it.start()
rt = ReadThread("ReadThread", s, sendQueue, lQueue)
rt.daemon=True
rt.start()
wt = SenderThread("SendThread", s, sendQueue, lQueue)
wt.daemon=True
wt.start()
rt.join()
wt.join()
s.close()