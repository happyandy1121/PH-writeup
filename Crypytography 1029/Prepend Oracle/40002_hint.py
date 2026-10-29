from pwn import remote

io = remote("10.99.70.3", 40002)

def oracle(payload):
    io.sendlineafter("message = ", payload.hex())
    return bytes.fromhex(io.recvline().strip().decode().split(" = ")[1])


cipher_length = ???
guess_range = ???


FLAG = b""
for i in range(cipher_length)[::-1]:
    prepend = b"A" * i
    target = oracle(prepend)[:cipher_length]
    for exhaustive in range(guess_range):
        message = ???
        if target == oracle(message)[:cipher_length]:
            FLAG += bytes([exhaustive])
            print(FLAG.decode())
            break