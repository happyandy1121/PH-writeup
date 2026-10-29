from pwn import remote

io = remote("10.99.70.3", 40004)

def oracle(cipher):
    io.sendlineafter("cipher = ", cipher.hex())
    if b"CORRECT" in io.recvline():
        return True
    return False


def xor(a, b):
    return bytes([x ^ y for x, y in zip(a, b)])


encrypt_flag = bytes.fromhex(io.recvline().decode().strip().split(" = ")[1])
blocks = [encrypt_flag[i : i + 16] for i in range(0, len(encrypt_flag), 16)]

IV = blocks.pop(0)
FLAG = b""

for block in blocks:
    find = b""
    for index in range(16)[::-1]:
        padding = 16 - index
        for exhaustive in range(256):
            if index == 15 and exhaustive == IV[15]:
                continue
            if oracle(
                ???
                + ???
                + xor(xor(bytes([padding] * (padding - 1)), ???), ???)
                + block
            ):
                find = ???
                break
        else:
            find = bytes([1]) + find
        print(find)
    IV = block
    FLAG += find

print(FLAG.decode().strip())
