import socket
import time


socket_path = "/home/nicorossi/csprojects/ELEC327-Webserver/ipc.sock"

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(socket_path)

ip = "192.168.1.1"
tst = bytearray(len(ip) + 1)

# for idx, c in ip:
#     tst[idx] = 

tst = bytes(ip, 'utf-8')


# sock.send(tst)

ba = bytearray(5)
ba[0] = 1
ip = [192, 168, 1, 1]
for i in range(1, 5):
    ba[i] = ip[i - 1]

print(ba)

sock.send(ba)

time.sleep(1)

sock.send(ba)