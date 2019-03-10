import select
import time
import sys
import irccolors
import socket
import threading

PING_INTERVAL = 30
PING_TIMEOUT = PING_INTERVAL + 30 # Must be PING_INTERVAL + actual ping timeout
RETRY_INTERVAL = 60

ansi_colors = {
        'green' : '1;32m',
        'blue'  : '1;34m',
        'red'   : '1;31m',
        'brown' : '0;33m',
        };

def colorize(line, color):
    if not sys.stdout.isatty():
        return line

    return '\033[' + ansi_colors[color] + line + '\033[0m'

class IrcConnection:
    def __init__(self, server, channel, nick, passw, port):
        self.server = server
        self.channel = channel
        self.nick = nick
        self.passw = passw
        self.port = port

        self.connection = None
        self.buffer = ""
        self.last_pong = 0
        self.await_pong = False

        self.queue = []
        self.lock = threading.Lock()
        self.quit_loop = False

    def connect_server(self):
        print(colorize("Connecting to {}:{}".format(self.server, self.port), 'brown'))

        while not self.connection:
            try:
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((self.server, self.port))
            except socket.gaierror:
                print(colorize("Couldn't resolve server, check your internet connection." \
                       " Re-attempting in 60 seconds.", 'red'))
                self.connection = None
                time.sleep(RETRY_INTERVAL)

        self.last_pong = time.time()
        self.await_pong = False
        self.process_input()

        if len(self.passw) > 0:
            self.post_string('PASS {}\n'.format(self.passw));

        self.post_string('NICK {}\n'.format(self.nick))
        self.post_string('USER {} {} {} :GH notifications\n'.format(self.nick, self.nick, self.nick))

        self.post_string('JOIN {}\n'.format(self.channel))
        self.send_message(irccolors.colorize('IRC bot initialized successfully', 'green'))

    def reconnect(self):
        self.connection.shutdown(2)
        self.connection.close()
        self.connection = None
        self.connect_server()

    def try_ping(self):
        self.post_string('PING {}\n'.format(self.server))
        self.await_pong = True

    def schedule_message(self, message):
        self.lock.acquire()
        try:
            self.queue.append(message)
        finally:
            self.lock.release()

    def process_line(self, line):
        if line.find('PING') != -1:
            self.post_string('PONG ' + line.split()[1] + '\n')

        if line.find('PONG') != -1:
            self.last_pong = time.time()
            self.await_pong = False

        if len(line) > 0:
            print('{}: {}'.format(colorize(self.server, 'green'), line))

    # Receive bytes from input, and process each new line which was received
    def process_input(self):
        data = self.connection.recv(4096)
        if not data or data == b'':
            return

        self.buffer += data.decode('utf-8')

        last_line_complete = (self.buffer[-1] == '\n')
        lines = self.buffer.split('\n')
        if last_line_complete: # The next buffer should be empty
            lines += ['']

        # Process all complete lines
        for line in lines[:-1]:
            self.process_line(line)

        # Next time append to the last line which is still incomplete
        self.buffer = lines[-1]

    def post_string(self, message):
        print(colorize(self.nick + '> ' + message[:-1], 'blue'))
        self.connection.send(bytes(message, 'utf-8'))

    def send_message(self, message):
        self.post_string('NOTICE ' + self.channel + ' :' + message + '\n')

    def stop_loop(self):
        self.quit_loop = True

    def loop(self):
        self.connect_server() # Initial connection attempt
        k = 0
        while not self.quit_loop:
            try:
                to_read, _, _ = select.select([self.connection], [], [], 1)
            except select.error:
                self.reconnect()
                continue

            # make sure connection doesn't get dropped
            if self.last_pong + PING_INTERVAL < time.time() and not self.await_pong:
                self.try_ping()

            # it was too much time since last pong, assume a broken connection
            if self.last_pong + PING_TIMEOUT < time.time() and self.await_pong:
                self.reconnect()
                continue

            if to_read:
                r = self.process_input()

            self.lock.acquire()
            try:
                while len(self.queue) > 0:
                    self.send_message(self.queue[0])
                    self.queue = self.queue[1:]
            finally:
                self.lock.release()

    def __del__(self):
        self.connection.close()
