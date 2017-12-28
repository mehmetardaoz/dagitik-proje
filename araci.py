import queue
import threading
import socket
import time
import uuid

class loggerThread (threading.Thread):
    def __init__(self, name, lQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.logQueue = lQueue

    def run(self):
        print(self.name + " starting.")
        while True:
            msg = self.logQueue.get()
            if msg == 'QUIT':
                print(self.name + ": QUIT received.")
                break
            print(str(time.ctime()) + " - " + str(msg))
        print(self.name + " exiting." )


class serverThread(threading.Thread):
    def __init__(self, name, senderSoc, threadQueue, loggerQueue, userFihrist, blackList, msgFihrist, myId):
        threading.Thread.__init__(self)
        self.name = name                #thread adı
        self.s = senderSoc              #soket
        self.tQueue = threadQueue       #threadler arası mesaj iletişiminde kullanılacak
        self.lQueue = loggerQueue       #logger thread ile iletişim
        self.fihrist = userFihrist      #userları ve bilgilerini tutmak için
        self.black = blackList          #rej gönderip fihriste eklenmeyecek kullanıcı listesi
        self.id = myId                  #kendi kimliği
        self.mfihrist = msgFihrist      #kullanıcıların threadqueue'ları yerleştirmek için fihrist
        self.peerId = str()
        self.peerIp = str()
        self.peerPort = int()
        self.peerGenre = str()

    def run(self):
        self.lQueue.put(self.name + ": starting")
        while True:
            # receive from socket
            msg = self.s.recv(1024).decode().strip('\n')
            print(msg)
            #check if in list(login)
            if self.peerId == "" or self.peerId not in self.fihrist.keys():
                self.login(msg)
                continue
            else:
                self.incomingParse(msg)

    def login(self, msg):
        # USR uuid ip port genre
        if len(msg)>3 and msg[:3] == 'USR':
            # split message
            splited = msg.split(" ")
            self.peerId = splited[1]
            self.peerIp = splited[2]
            self.peerPort = int(splited[3])
            self.peerGenre = splited[4]
            if self.peerId not in self.black:
                # add or update peer
                self.fihrist[self.peerId] = [self.peerIp, self.peerPort, str(time.ctime()), "OK", self.peerGenre]
                self.mfihrist[self.peerId] = self.tQueue
                self.sendToPeer("HEL")
            else:
                self.fihrist[self.peerId] = [self.peerIp, self.peerPort, str(time.ctime()), "REJ", self.peerGenre]
                self.mfihrist[self.peerId] = self.tQueue
                self.sendToPeer("REJ")
                self.peerId = ""

    def incomingParse(self, msg):
        if len(msg) > 2:
            #LSQ
            if msg[:3] == "LSQ":
                self.sendToPeer("LSA " + str(self.fihrist))
            # LSA {'uuid': ['peerIp', peerPort, 'time', 'OK', 'P/S'], 'uuid2': ['peerIp2', peerPort2 ... }
            elif msg[:3] == "LSA":
                splited = msg[4:]
                splited = splited.strip('{')
                splited = splited.strip('}')
                uList = splited.split('], ')
                for user in uList:
                    uId = user.split(': ')[0]
                    uId = strip('\'')
                    attr = user.split(': ')[1]
                    attr = attr.strip('[')
                    attrList = attr.split(', ')
                    for at in attrList:
                        fValues = list()
                        ip = at[0]
                        port = at[1]
                        time = at[2]
                        statement = at[3]
                        genre = at[4]
                        fValues.append(ip)
                        fValues.append(port)
                        fValues.append(time)
                        fValues.append(statement)
                        fValues.append(genre)
                        self.fihrist[uId] = fValues
            #CHK
            elif msg[:3] == "CHK":
                self.sendToPeer("ACK " + str(self.id))
            #ACK uuid timestamp
            elif msg[:3] == "ACK":
                # update time
                splited = msg.split(" ")
                ackID = splited[1]
                self.fihrist[ackID][2] = str(time.ctime())
            else:
                self.sendToPeer("ERR")

    def sendToPeer(self, msg):
        self.mfihrist[self.peerId].put(msg)
        self.lQueue.put("cevap: " + msg)


class clientThread(threading.Thread):
    def __init__(self, name, clientSoc, threadQueue, loggerQueue, fihrist, msgFihrist, cmdQueue, myId, myIp, myPort):
        threading.Thread.__init__(self)
        self.name = name
        self.c = clientSoc
        self.tQueue = threadQueue
        self.lQueue = loggerQueue
        self.fihrist = fihrist
        self.mfihrist = msgFihrist
        self.id = myId
        self.ip = myIp
        self.port = myPort
        self.cqueue = cmdQueue

    def run(self):
        self.lQueue.put(self.name + ": starting")
        chkTread = checkMsg(self.tQueue)
        chkThread.start()
        while True:
            # get the message from thread queue to send
            msg = self.tQueue.get()
            self.c.send(msg.encode())
            # cmd from ui
            if not self.cqueue.empty():
                cmd = self.cqueue().get()
                # parse
                cmdMsg = self.cmdParser(cmd)
                #ui den alınan komuta göre mesajı tqueue'ye koy
                self.tQueue.put(cmdMsg)

    def cmdParser(self, msg):
        if len(msg) > 1:
            # USR uuid ip port genre='S'
            if msg[1] == "/n":
                return "USR " + str(self.id) + ' ' + str(self.ip) + ' ' + str(self.port) + " S"
            elif msg[1] == "/l":
                return "LSQ"
            # elif msg[1] == "/c":
            #     return "CHK"

class checkMsg(threading.Thread):
    def __init__(self, threadQueue):
        threading.Thread.__init(self)
        self.tQueue = threadQueue
    def run(self):
        while(True):
            #120 saniyede bir CHK yollaması için
            time.sleep(120)
            self.tQueue.put("CHK")



def main():
    lQueue = queue.Queue()
    lThread = loggerThread("Logger Thread", lQueue)
    lThread.start()

    #ui command queue
    cmdQueue = queue.Queue()
    #arayüzden gelen komutlar bu kuyruğa atılmalı ki client thread içinde erişilebilsin

    # user fihrist - blacklist - peerlar için mesaj fihristi
    fihrist = {}
    blacklist = list()
    msgFihrist = {}

    #stupid's uuid
    myId = str(uuid.NAMESPACE_DNS.hex)

    # create and listen
    s = socket.socket()
    host = "0.0.0.0"
    port = 1234
    s.bind((host,port))
    s.listen(5)

    wCounter = 0
    sCounter = 0

    while True:
        # fihristin içine konulacak thread kuyruğu
        threadQueue = queue.Queue()

        try:
            # lQueue.put('Waiting for a connection.')
            c, addr = s.accept()
        except:
            s.close()
            lQueue.put('QUIT')
            break

        # lQueue.put('Got new connection from' + str(addr))

        sThread = serverThread('serverThread-' + str(sCounter),
                               c,
                               threadQueue,
                               lQueue,
                               fihrist,
                               blacklist,
                               msgFihrist,
                               myId)
        sThread.start()
        sCounter += 1

        wThread = clientThread('clientThread-' + str(wCounter),
                               c,
                               threadQueue,
                               lQueue,
                               fihrist,
                               msgFihrist,
                               cmdQueue,
                               myId,
                               host,
                               port)
        wThread.start()
        wCounter += 1


if __name__ == '__main__':
    main()