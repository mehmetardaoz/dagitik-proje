import sys
import socket
import threading
import queue
import time
from PyQt4 import QtGui, QtCore

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
    def __init__(self, name, csoc, sendQueue, logQueue, app):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.nickname = ""
        self.sendQueue = sendQueue
        self.message=""
        self.logQueue = logQueue
        self.app = app

    def incoming_parser(self, data):
        if len(data) < 2:
            self.sendQueue.put("ERR")

        else:
            if data[0:3] == "SOK":
                msg = "Toplu mesaj gonderildi."
                self.app.text_browser.append(msg)
                print("Toplu mesaj gonderildi.")
                self.logQueue.put("Toplu mesaj gonderildi.")
                return 0

            elif data[0:3] == "BYE":
                msg = "Hoscakal " + data[4:-1]
                self.app.text_browser.append(msg)
                print(msg)
                self.logQueue.put(msg)
                return -1

            elif data[0:3] == "SAY":
                self.app.text_browser.append(data[4:-1])
                return 0

            elif data[0:3] == "MSG":
                self.app.text_browser.append(data[4:-1])
                return 0

            elif data[0:3] == "SYS":
                self.app.text_browser.append(data[4:-1])
                return 0

            elif data[0:3] == "ERL":
                msg = "Oncelikle giris yapmalisiniz."
                self.app.text_browser.append(msg)
                print("Lutfen giris yapiniz.")
                self.logQueue.put("Lutfen giris yapiniz.")
                return 1

            elif data[0:3] == "ERR":
                msg = "Hatali komut girisi yapildi."
                self.app.text_browser.append(msg)
                print("Hatali komut girisi yapildi.")
                self.logQueue.put("Hatali komut girisi yapildi.")
                return 0

            elif data[0:3] == "HEL":
                rest = data [4:-1]
                msg = rest + " kullanici adiyla sisteme giris yapildi."
                self.app.text_browser.append(msg)
                self.logQueue.put(rest + " kullanici adiyla sisteme giris yapildi.")
                print(rest + " kullanici adiyla sisteme giris yapildi.")
                return 0

            elif data[0:3] == "REJ":
                rest = data[4:-1]
                msg = "Giris yapilamadi. " + rest + " adli kullanici zaten kayitli."
                self.app.text_browser.append(msg)
                print("Giris yapilamadi. " + rest + " adli kullanici zaten kayitli.")
                self.logQueue.put("Giris yapilamadi. '" + rest + "' adli kullanici zaten kayitli.")
                return 0

            elif data[0:3] == "MOK":
                msg = "Ozel mesaj gonderildi."
                self.app.text_browser.append(msg)
                self.logQueue.put("Ozel mesaj gonderildi.")
                return 0

            elif data[0:3] == "MNO":
                rest = data[4:-1]
                msg = "'" + rest + "'" + " adli kullanici bulunamadi."
                self.app.text_browser.append(msg)
                print(msg)
                self.logQueue.put("'" + rest + "'" + " adli kullanici bulunamadi.")
                return 0

            elif data[0:6] == "NO_MSG":
                msg = "Lütfen göndermek üzere bir mesaj yazınız!!!."
                self.app.text_browser.append(msg)
                print(msg)
                self.logQueue.put(msg)
                return 0

            elif data[0:3] == "TOC":
                msg = "TIC mesajı gönderildi. 'TOC' cevabı alındı."
                self.app.text_browser.append(msg)
                print(msg)
                self.logQueue.put(msg)
                return 0

            elif data[0:3] == "LSA":
                rest = data[4:-1]
                msg = "Kullanici listesi: " + rest
                self.app.text_browser.append(msg)
                print("Kullanici listesi: " + rest)
                self.logQueue.put("Kullanici listesi: " + rest)
                return 0

            else:
                pass
    def run(self):
        while True:
            data = self.csoc.recv(1024)
            self.message = self.incoming_parser(data.decode())
            if self.message==-1:
                break

            if self.message==1:
                pass

        self.sendQueue.put("FIN")
        print("Sistem başarıyla sonlandırıldı.")
        s.close()
        time.sleep(2)
        self.app.close()

# class InputThread(threading.Thread):
#     def __init__(self, name, sendQueue):
#         threading.Thread.__init__(self)
#         self.name = name
#         self.sendQueue = sendQueue
#
#     def run(self):
#         queue_message = input("Komut giriniz: ")
#         while True:
#             self.sendQueue.put(queue_message)
#             time.sleep(1)
#             queue_message = input("Komut giriniz: ")

class SenderThread (threading.Thread):
    def __init__(self, name, csoc, sendQueue, logQueue, app):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.sendQueue = sendQueue
        self.logQueue = logQueue
        self.app = app
        self.user = ""

    def run(self):
        while True:
            if self.sendQueue.qsize() > 0:
                msg = self.sendQueue.get()
                if msg == "FIN":
                    break
                self.outgoing_parser(msg)

    def outgoing_parser(self,data):
        if(data[0:2]) == "/n":
            self.user = data[3:]
            msg = "USR " + self.user
            self.csoc.send(msg.encode())

        elif (data[0:2]) == "/l":
            msg = "LSQ"
            self.csoc.send(msg.encode())

        elif (data[0:2]) == "/t":
            msg = "TIC"
            self.csoc.send(msg.encode())

        elif (data[0:2]) == "/q":
            msg = "QUI"
            self.csoc.send(msg.encode())

        elif (data[0:2]) == "/m":
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

        elif (data[0:2]) == "/s":
            msg = "SAY " + data[3:]
            self.csoc.send(msg.encode())

        else:
            self.csoc.send(data.encode())

class ChatApplication(QtGui.QDialog):
    def __init__(self,sendQueue):
        self.app = QtGui.QApplication(sys.argv)
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("Chat Programi")
        self.setMinimumSize(600,400)

        self.box = QtGui.QVBoxLayout()
        self.line_edit = QtGui.QLineEdit("", self)
        self.text_browser = QtGui.QTextBrowser()
        self.button = QtGui.QPushButton("SEND")
        self.connect(self.button, QtCore.SIGNAL("clicked()"), self.outgoing_parser)

        self.box.addWidget(self.line_edit)
        self.box.addWidget(self.text_browser)
        self.box.addWidget(self.button)

        self.setLayout(self.box)

        self.sendQueue = sendQueue

    def run(self):
        self.show()
        sys.exit(app.exec_())

    def outgoing_parser(self):
        data = str(self.line_edit.text())
        if len(data) == 0:
            pass

        else:
            self.sendQueue.put(data)
            self.line_edit.clear()


# log thread başlatılır
lQueue = queue.Queue()
lThread = loggerThread("Logger", lQueue, "log.txt")
lThread.start()


s = socket.socket()
host = "localhost"
# host = "localhost"
port = 12345
s.connect((host,port))

sendQueue = queue.Queue(20)
app = ChatApplication(sendQueue)

# start threads
# it = InputThread("InputThread", sendQueue)
# it.daemon=True
# it.start()
rt = ReadThread("ReadThread", s, sendQueue, lQueue, app)
rt.daemon=True
rt.start()
wt = SenderThread("SendThread", s, sendQueue, lQueue, app)
wt.daemon=True
wt.start()
app.run()
rt.join()
wt.join()
s.close()