import threading
import queue
import socket
import time

class LoggerThread(threading.Thread):
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


class ReaderThread(threading.Thread):
    def __init__(self, name, csoc, fihrist, sendQueue, logQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.fihrist = fihrist
        self.sendQueue = sendQueue
        self.logQueue = logQueue
        self.user = ""

    def run(self):
        self.logQueue.put(self.name + ": starting.")
        while True:
            data = self.csoc.recv(1024)
            msg = self.parser(data.decode()) + "\n"

            if msg == "QUI\n":
                self.sendQueue.put("QUI")
                break

        self.logQueue.put(self.name + ": exiting.")

    def parser(self, data):
        if len(data) != 0:
            # giriş yapılmazsa ERL dondur
            if not data[:3] == "USR" and not self.user:
                self.sender("ERL")
                return "ERL"

            #kullanici olusturmak icin
            elif data[0:3] == "USR":
                self.user = data[4:]
                if self.user in self.fihrist.keys():
                    self.logQueue.put("There is already exist user: " + self.user)
                    self.sender("REJ " + self.user)
                    return "REJ"
                else:
                    self.fihrist[self.user] = self.sendQueue
                    msg = self.user + " has joined."
                    self.logQueue.put(msg)
                    send_message = ("SYS", self.user, msg)
                    for q in self.fihrist.values():
                        q.put(send_message)

                    self.sender('HEL ' + self.user)
                    return 'HEL'

            # bütün kayıtlı kullanıcıları göstermek için LSQ mesajı
            elif data[:3] == "LSQ":
                liste = ''
                for i in self.fihrist.keys():
                    liste += ':'
                    liste += i
                user_list = str(liste)
                self.logQueue.put(self.user + " has requested for user list." + " User List: " + user_list[1:])
                self.sender("LSA " + user_list[1:])
                return 'LSA'

            # kontrol için TIC mesajı
            elif data[0:3] == "TIC":
                self.logQueue.put(self.user + " send 'TIC' message.")
                self.sender('TOC')
                return 'TOC'

            # bütün kullanıcılara mesaj göndermek için SAY komutu
            elif data[0:3] == "SAY":
                send_message = ("SAY", self.user, data[4:])
                del self.fihrist[self.user]
                for q in self.fihrist.values():
                    q.put(send_message)
                self.logQueue.put(self.user + " send a message to all users. The message is '" + data[4:] + "'")
                self.fihrist[self.user] = self.sendQueue
                self.sender('SOK')
                return 'SOK'

            # private message göndermek için MSG komutu
            elif data[0:3] == "MSG":
                target_user, msg = data[4:].split(":")
                if len(msg) > 0:
                    if target_user in self.fihrist.keys():
                        send_message = ("MSG", self.user, msg)
                        self.fihrist[target_user].put(send_message)
                        self.logQueue.put(self.user + " sent a private message to " + target_user)
                        self.sender('MOK')
                        return "MOK"

                    else:
                        self.logQueue.put("There is no user as " + "'" + target_user + "'")
                        self.sender('MNO ' + target_user)
                        return "MNO"

                else:
                    self.logQueue.put("There is no message! Please write something to send.")
                    self.sender('NO_MSG')
                    return "EMPTY_MESSAGE"

            # kullanıcının çıkış yapması için QUI mesajı.
            # kullanıcı çıkış yapınca aktifliğini kaybeder ve listeden çıkarılır.
            elif data[0:3] == "QUI":
                msg = "BYE " + self.user
                self.sender(msg)
                self.fihrist.pop(self.user)
                message = self.user + " has left."
                self.logQueue.put(message)
                self.sender(message)
                send_message = ("SYS", self.user, message)
                for q in self.fihrist.values():
                    q.put(send_message)

                return "QUI"

            else:
                self.sender('ERR')
                return "ERR"
        else:
            pass

    def sender(self,send_message):
        send_message += '\n'
        self.csoc.send(send_message.encode())


class WriterThread(threading.Thread):
    def __init__(self, name, csoc, sendQueue, logQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.sendQueue = sendQueue
        self.logQueue = logQueue

    def run(self):
        self.logQueue.put(self.name + ": starting.")
        while True:
            if self.sendQueue.qsize() > 0:
                send_message = self.sendQueue.get()

                if send_message[0] == "SAY":
                    send_msg = "SAY " + send_message[1] + ":" + send_message[2]
                    print(send_msg)

                elif send_message[0] == "MSG":
                    send_msg = "MSG " + send_message[1] + ":" + send_message[2]

                elif send_message[0] == "SYS":
                    time.sleep(0.5)
                    send_msg = "SYS " + send_message[2]

                else:
                    break

                message = send_msg + "\n"
                self.csoc.sendall(message.encode())

        self.logQueue.put(self.name + ": exiting.")

fihrist = dict()
threads = []

# thread sayıları belirlenir.her yeni thread için 1 arttırılır
readerCounter = 1
writerCounter = 1

# log thread başlatılır
lQueue = queue.Queue(30)
lThread = LoggerThread("Logger Thread", lQueue, "log.txt")
lThread.daemon = True
lThread.start()
threads.append(lThread)

# dinlemeye başlanır
s = socket.socket()
host = "localhost"
port = 12345
s.bind((host,port))
s.listen(5)

print("Waiting for connection...")

while True:
    c, addr = s.accept()
    lQueue.put('Got new connection from' + str(addr))

    sendQueue = queue.Queue(10)

    readerThread = ReaderThread("Reader Thread - "+ str(readerCounter), c, fihrist, sendQueue, lQueue)
    readerThread.daemon = True
    readerThread.start()
    threads.append(readerThread)
    readerCounter += 1

    writerThread = WriterThread("Writer Thread - "+ str(writerCounter), c, sendQueue, lQueue)
    writerThread.daemon = True
    writerThread.start()
    threads.append(writerThread )
    writerCounter += 1


