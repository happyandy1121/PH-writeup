from pwn import remote
from base64 import b64decode, b64encode

io = remote("10.99.70.3", 40003)

cipher_text = bytearray(b64decode(io.recvline().decode()))

plain_text = ???
goal = ???

for i in range(9):
    cipher_text[i] = ???

io.sendline(b64encode(cipher_text))
print(io.recv().decode().strip())