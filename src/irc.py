import select
import irccolors
import socket
import threading

class IrcConnection:
    def __init__(self, server, channel, nick, port):
        self.channel = channel

        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((server, port))
        self.connection.recv(4096)

        self.post_string('NICK ' + nick + '\n')
        self.post_string('USER mynewbot completely real :GH notifications\n')
        self.post_string('JOIN ' + channel + '\n')
        self.send_message(irccolors.colorize('IRC bot initialized successfully', 'green'))

        self.queue = []
        self.lock = threading.Lock()
        self.quit_loop = False

    def schedule_message(self, message):
        self.lock.acquire()
        try:
            self.queue.append(message)
        finally:
            self.lock.release()

    def process_input(self):
        data = self.connection.recv(4096).decode('utf-8')
        if data.find('PING') != -1:
            self.post_string('PONG ' + data.split()[1] + '\n')

        if len(data) > 0:
            print(data)

    def post_string(self, message):
        self.connection.send(bytes(message, 'utf-8'))

    def send_message(self, message):
        self.post_string('NOTICE ' + self.channel + ' :' + message + '\n')

    def stop_loop(self):
        self.quit_loop = True

    def loop(self):
        while not self.quit_loop:
            ready = select.select([self.connection], [], [], 1)
            if ready[0]:
                self.process_input()

            self.lock.acquire()
            try:
                while len(self.queue) > 0:
                    self.send_message(self.queue[0])
                    self.queue = self.queue[1:]
            finally:
                self.lock.release()

    def __del__(self):
        self.connection.close()
