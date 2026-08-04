from Crypto.Random import get_random_bytes
import os

SBOX = [
    0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD,
    0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2
      ]

INV_SBOX = [0] * 16 #inverse SBOX
for i, v in enumerate(SBOX):
    INV_SBOX[v] = i

PBOX = [
    0, 16, 32, 48, 1, 17, 33, 49, 2, 18, 34, 50, 3, 19, 35, 51,
    4, 20, 36, 52, 5, 21, 37, 53, 6, 22, 38, 54, 7, 23, 39, 55,
    8, 24, 40, 56, 9, 25, 41, 57, 10, 26, 42, 58, 11, 27, 43, 59,
    12, 28, 44, 60, 13, 29, 45, 61, 14, 30, 46, 62, 15, 31, 47, 63
] #64 values for 64 bit block size

INV_PBOX=[0] * 64
for i,v in enumerate(PBOX):
    INV_PBOX[v] = i

# generate 32 round keys from the 80-bit key
def generate_round_keys(key: int) -> list:
    keys = []
    for i in range(1, 33):
        keys.append(key >> 16) # take the leftmost 64 bits as the round key
        key = ((key & 0x7FFFF) << 61) | (key >> 19) # rotate the key left by 61 bits
        sbox_in = key >> 76 # take the first 4 bits and apply the SBOX
        # Clear the first 4 bits, then insert their new values from the S-box.
        key = (key & 0x0FFFFFFFFFFFFFFFFFFF) | (SBOX[sbox_in] << 76) 
        # XOR the round number into the key to ensure 
        # each round uses a unique round key.
        key ^= (i << 15) 
    return keys

def present_encrypt(plaintext: int, key: int) -> int:
    state = plaintext
    round_keys = generate_round_keys(key)
    for i in range(31):
        state ^= round_keys[i]
        new_state = 0
        for j in range(16):
            nibble = (state >> (j * 4)) & 0xF
            new_state |= (SBOX[nibble] << (j * 4))
        state = new_state
        new_state = 0
        for j in range(64):
            bit = (state >> j) & 1
            new_state |= (bit << PBOX[j])
        state = new_state
    state ^= round_keys[31]
    return state

def present_decrypt(ciphertext: int, key: int) -> int:
    state = ciphertext
    round_keys = generate_round_keys(key)
    state ^= round_keys[31]
    for i in reversed(range(31)):
        new_state = 0
        for j in range(64):
            bit = (state >> j) & 1
            new_state |= (bit << INV_PBOX[j])
        state = new_state
        new_state = 0
        for j in range(16):
            nibble = (state >> (j * 4)) & 0xF
            new_state |= (INV_SBOX[nibble] << (j * 4))
        state = new_state
        state ^= round_keys[i]
    return state

def present_ctr(data: bytes, key: int, nonce: int = 0) -> bytes:
    out = bytearray()
    counter = nonce
    for offset in range(0, len(data), 8):
        keystream = present_encrypt(counter, key).to_bytes(8, "big")
        chunk = data[offset:offset + 8]
        out.extend(b1 ^ b2 for b1, b2 in zip(chunk, keystream))
        counter = (counter + 1) & ((1 << 64) - 1)
    return bytes(out)

def encrypt_file(input_file, output_file, key):
    nonce = int.from_bytes(os.urandom(8), "big")
    with open(input_file, "rb") as f:
        plaintext = f.read()
    ciphertext = present_ctr(plaintext, key, nonce)
    with open(output_file, "wb") as f:
        f.write(nonce.to_bytes(8, "big"))
        f.write(ciphertext)

def decrypt_file(input_file, output_file, key):
    with open(input_file, "rb") as f:
        nonce = int.from_bytes(f.read(8), "big")
        ciphertext = f.read()
    plaintext = present_ctr(ciphertext, key, nonce)
    with open(output_file, "wb") as f:
        f.write(plaintext)

def main(): #test the PRESENT implementation
    key = int.from_bytes(get_random_bytes(10), "big")  # 80-bit key
    nonce = 0 # just for test I need to change it later 

    encrypt_file("data/sample_1KB.txt", "data/sample_1KB.enc", key)
    decrypt_file("data/sample_1KB.enc", "data/sample_decrypted.txt", key)

    with open("data/sample_1KB.txt", "rb") as f:
        original = f.read()
    with open("data/sample_decrypted.txt", "rb") as f:
        decrypted = f.read()
    print("Match:", original == decrypted)

if __name__ == "__main__":
    main()