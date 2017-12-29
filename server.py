import queue
import threading
import socket
import time
import uuid
import os, os.path
from difflib import SequenceMatcher
import hashlib
from PyQt4 import QtGui, QtCore
import sys

rCounter = 0
wCounter = 0
my_port = 12347
myId_ = 2

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
            #check if in list(login)
            if len(msg) > 2:
                self.incomingParse(msg)
                continue

    def similar(self,  a , b):
        a = a.lower()
        b = b.lower()
        sim = SequenceMatcher(None, a, b).ratio()
        return (sim)

    def get_md5(self, path_file):
        with open(path_file, 'rb') as fh:
            m = hashlib.md5()
            while True:
                data = fh.read(8192)
                if not data:
                    break
                m.update(data)
            return m.hexdigest()

    def incomingParse(self, msg):
        if len(msg) > 2:
            #LSQ
            if len(msg) > 3 and msg[:3] == 'USR':
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

            elif msg[:3] == "LSQ":
                self.sendToPeer("LSA " + str(self.fihrist))
                # pass
            #CHK
            elif msg[:3] == "CHK":
                self.sendToPeer("ACK " + str(self.id))
            #ACK uuid timestamp
            elif msg[:3] == "ACK":
                # update time
                splited = msg.split(" ")
                ackID = splited[1]
                self.fihrist[ackID][2] = str(time.ctime())

            elif msg[:3] == "FNS":
                file_name = msg[4:]
                path = "C:\\Users\\Arda\\PycharmProjects\\socket_deneme\\proje\\shared\\"
                dirs = os.listdir(path)
                files = []
                print(file_name)
                if os.path.isdir(path):
                    file_name = file_name.strip(" ")
                    for exist_file in dirs:
                        sim = self.similar(file_name, exist_file)
                        if sim >= 0.5:
                            md5 = self.get_md5(path + exist_file)
                            size_info = os.stat(path + exist_file)
                            size = size_info.st_size
                            file = exist_file + " " + str(md5) + " " + str(size)
                            files.append(file)

                msg = "FNO" + str(files)
                self.sendToPeer(msg)

            elif msg[:3] == "MDS":
                md5 = msg[4:]
                print(md5)
                md5 = md5.strip(" ")
                path = "C:\\Users\\Arda\\PycharmProjects\\socket_deneme\\proje\\shared\\"
                dirs = os.listdir(path)
                files = []
                if os.path.isdir(path):
                    for exist_file in dirs:
                        if self.get_md5(path + exist_file) == md5:
                            size_info = os.stat(path + exist_file)
                            size = size_info.st_size
                            file = exist_file + " " + str(md5) + " " + str(size)
                            files.append(file)

                msg = "MDO" + str(files)
                self.sendToPeer(msg)

            elif msg[:3] == "CNS":
                path = "C:\\Users\\Arda\\PycharmProjects\\socket_deneme\\proje\\shared\\"
                chunk_info = msg[4:]
                chunk_info = chunk_info.split(" ")
                chunk_size = chunk_info[0]
                chunk_no = chunk_info[1]
                md5 = chunk_info[2]
                dirs = os.listdir(path)
                files = []

                if os.path.isdir(path):
                    for exist_file in dirs:
                        if self.get_md5(path + exist_file) == md5:
                            files.append(exist_file)

                file_name = files[0]
                f = open(path + file_name, 'rb')
                data = f.read() # read the entire content of the file
                f.close()
                bytes = len(data)


                s = int(chunk_size)
                for i in range(0, bytes+1, s):
                    fnl = str(i)
                    f = open(fnl, 'wb')
                    f.write(data[i:i+ s])
                    f.close()

                msg = "CNO " + str(data[chunk_no:chunk_no +s])
                self.sendToPeer(msg)

            else:
                self.sendToPeer("ERR")

    def sendToPeer(self, msg):
        self.s.send(msg.encode())
        self.lQueue.put("cevap: " + msg)


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

class readerClientThread(threading.Thread):
    def __init__(self, name, clientSoc, sendQueue, loggerQueue, fihrist, msgFihrist, cmdQueue, myId, myIp, myPort, app, app2):
        threading.Thread.__init__(self)
        self.name = name
        self.c = clientSoc
        self.sQueue = sendQueue
        self.lQueue = loggerQueue
        self.fihrist = fihrist
        self.mfihrist = msgFihrist
        self.id = myId
        self.ip = myIp
        self.port = myPort
        self.app = app
        self.cqueue = cmdQueue
        self.app2 = app2

    def run(self):
        self.lQueue.put(self.name + ": starting")
        while True:
            # get the message from thread queue to send
            data = self.c.recv(1024)
            self.message = self.outgoing_parser(data.decode())
            # cmd from ui
            if not self.cqueue.empty():
                cmd = self.cqueue().get()
                # parse
                self.outgoing_parser(cmd)

    def outgoing_parser(self, msg):
        if len(msg) > 1:
            # USR uuid ip port genre='S'
            if (msg[0:3]) == "HEL":
                print("HEL")
            elif msg[1] == "/c":
                return "CHK"

            # LSA {'uuid': ['peerIp', peerPort, 'time', 'OK', 'P/S'], 'uuid2': ['peerIp2', peerPort2 ... }
            elif msg[:3] == "LSA":
            ################################## splitte sorun
                print(msg)
                splited = msg[4:]
                splited = splited.strip('{')
                splited = splited.strip('}')
                uList = splited.split('], ')
                for user in uList:
                    uId = user.split(': ')[0]
                    uId = uId.strip('\'')
                    print("uid = " + uId)
                    attr = user.split(': ')[1]
                    attr = attr.strip('[')
                    attr = attr.strip(']')
                    attrList = attr.split(', ')
                    print(attrList)
                    fValues = list()
                    ip = attrList[0]
                    port = attrList[1]
                    port = port.strip("'")
                    new_time = attrList[2]
                    statement = attrList[3]
                    genre = attrList[4]
                    print(ip + port + new_time + statement)
                    fValues.append(ip)
                    fValues.append(port)
                    fValues.append(new_time)
                    fValues.append(statement)
                    fValues.append(genre)
                    self.fihrist[uId] = fValues
                    self.app.addItem(uId + " " + ip + " " + port + " " + new_time + " " + genre + " ")
                    if uId == self.id:
                        continue
                    else:
                        ct = connectOther(ip, port, self.sQueue, self.lQueue, self.fihrist, self.mfihrist, self.cqueue, self.id, self.app)
                        ct.start()

            elif msg[:3] == "FNO":
                print(msg[4:])
                file_list = msg[4:].split(",")
                for file_info in file_list:
                    file_info.split(" ")
                    file_name = file_info[0]
                    md5 = file_info[1]
                    file_size = file_info[2]
                    self.app2.dosya_list.addItem(file_name + md5 + file_size)


            elif msg[:3] == "MDO":
                print(msg[4:])


class senderClientThread(threading.Thread):
    def __init__(self, name, clientSoc, sendQueue, loggerQueue, fihrist, msgFihrist, cmdQueue, myId, myIp, myPort,app, app2):
        threading.Thread.__init__(self)
        self.name = name
        self.c = clientSoc
        self.sQueue = sendQueue
        self.lQueue = loggerQueue
        self.fihrist = fihrist
        self.mfihrist = msgFihrist
        self.id = myId
        self.ip = myIp
        self.port = myPort
        self.cqueue = cmdQueue
        self.app = app
        self.app2 = app2

    def run(self):
        self.lQueue.put(self.name + ": starting")
        while True:
            # get the message from thread queue to send
            send_message = self.sQueue.get()

            if send_message[:3] == "FNS":
                message = send_message
                self.c.sendall(message.encode())


class connectOther(threading.Thread):
    def __init__(self,ip, port, sendQueue, lQueue, fihrist, msgFihrist, cmdQueue, myId, kullanici_list, app):
        threading.Thread.__init__(self)
        self.ip = ip
        self.app = app
        self.port = port
        self.sendQueue = sendQueue
        self.lQueue = lQueue
        self.fihrist = fihrist
        self. msgFihrist = msgFihrist
        self.cmdQueue = cmdQueue
        self.myId = myId
        self.kullanici_list = kullanici_list
        port_ = int(self.port)
        print(self.ip + self.port)
        cli = socket.socket()
        cli.connect(('127.0.0.1', port_))

        global rCounter
        global wCounter
        global my_port
        global myId_

        rThread = readerClientThread('readerClientThread-' + str(rCounter),
                                     cli,
                                     sendQueue,
                                     lQueue,
                                     fihrist,
                                     msgFihrist,
                                     cmdQueue,
                                     myId,
                                     ip,
                                     port,
                                     kullanici_list,
                                     self.app)
        rThread.start()
        rCounter += 1

        wThread = senderClientThread('writerClientThread-' + str(wCounter),
                                     cli,
                                     sendQueue,
                                     lQueue,
                                     fihrist,
                                     msgFihrist,
                                     cmdQueue,
                                     myId,
                                     ip,
                                     port,
                                     kullanici_list,
                                     self.app)
        wThread.start()
        wCounter += 1

        msg_usr = "USR " + str(myId_) + " " + "127.0.0.1" + " " + str(my_port) + " P"
        cli.send(msg_usr.encode())


        msg_lsq = "LSQ"
        cli.send(msg_lsq.encode())


class ChatApplication(QtGui.QDialog):
    def __init__(self,sendQueue, lQueue, fihrist, msgFihrist, cmdQueue, myId):
        self.app = QtGui.QApplication(sys.argv)
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("torrent")
        self.setMinimumSize(800,600)

        self.box = QtGui.QVBoxLayout()
        self.lineEdit_dosya_ismi = QtGui.QLineEdit("", self)
        self.lineEdit_ip = QtGui.QLineEdit("", self)
        self.lineEdit_port = QtGui.QLineEdit("", self)
        self.dosya_list = QtGui.QListWidget()
        self.kullanici_list = QtGui.QListWidget()
        self.pushButton_indir = QtGui.QPushButton("Indir")
        self.pushButton_dosya_ara = QtGui.QPushButton("Dosya Ara")
        self.pushButton_connect = QtGui.QPushButton("Baglan")
        self.connect(self.pushButton_connect, QtCore.SIGNAL("clicked()"), self.connect_user)
        self.connect(self.pushButton_dosya_ara, QtCore.SIGNAL("clicked()"), self.find_file)
        self.connect(self.pushButton_indir, QtCore.SIGNAL("clicked()"), self.outgoing_parser)

        #
        # self.box.addWidget(self.line_edit)
        # self.box.addWidget(self.text_browser)
        # self.box.addWidget(self.button)

        # self.setLayout(self.box)
        self.box.addWidget(self.lineEdit_ip)
        self.box.addWidget(self.lineEdit_port)
        self.box.addWidget(self.pushButton_connect)
        self.box.addWidget(self.kullanici_list)
        self.box.addWidget(self.lineEdit_dosya_ismi)
        self.box.addWidget(self.pushButton_dosya_ara)
        self.box.addWidget(self.dosya_list)
        self.box.addWidget(self.pushButton_indir)
        self.setLayout(self.box)

        self.sendQueue = sendQueue
        self.lQueue = lQueue
        self.fihrist = fihrist
        self.msgFihrist = msgFihrist
        self.cmdQueue = cmdQueue
        self.myid = myId

    def run(self):
        self.show()
        sys.exit(self.app.exec_())

    def connect_user(self):
        ip = str(self.lineEdit_ip.text())
        port = str(self.lineEdit_port.text())
        print(ip + port)
        connectOther(ip,port,self.sendQueue, self.lQueue, self.fihrist, self.msgFihrist, self.cmdQueue, self.myid, self.kullanici_list, self.app)

    def find_file(self):
        file_name = str(self.lineEdit_dosya_ismi.text())
        send_message = ("FNS " + file_name)
        self.sendQueue.put(send_message)



    def outgoing_parser(self):
        data = str(self.line_edit.text())
        if len(data) == 0:
            pass

        else:
            self.sendQueue.put(data)
            self.line_edit.clear()


def main():
    sendQueue = queue.Queue(20)

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
    sCounter = 0

    #stupid's uuid
    myId = str(uuid.NAMESPACE_DNS.hex)
    host = "127.0.0.1"

    s = socket.socket()
    s.bind((host, my_port))
    s.listen(5)

    app = ChatApplication(sendQueue, lQueue, fihrist, msgFihrist, cmdQueue, myId)
    app.run()

    # ip = "localhost"
    # port_c = 12346
    # connectOther(ip, port_c, sendQueue, lQueue, fihrist, msgFihrist, cmdQueue, myId)


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




if __name__ == '__main__':
    main()