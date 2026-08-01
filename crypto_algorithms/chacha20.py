from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes

key = get_random_bytes(32)  # ChaCha20 uses a 256-bit key

def encrypt_file(input_file, output_file, key):
    with open(input_file, "rb") as file:
        plaintext = file.read()
    cipher = ChaCha20.new(key=key)
    ciphertext = cipher.encrypt(plaintext)

    with open(output_file, "wb") as file:
        file.write(cipher.nonce)
        file.write(ciphertext)

def decrypt_file(input_file, output_file, key):
    with open(input_file, "rb") as file:
        nonce = file.read(8)
        ciphertext = file.read()
    cipher = ChaCha20.new(key=key, nonce=nonce)
    plaintext = cipher.decrypt(ciphertext)

    with open(output_file, "wb") as file:
        file.write(plaintext)

def main():
    key = get_random_bytes(32)  # ChaCha20 uses a 256-bit key
    encrypt_file(
        "data/sample.txt",
        "data/sample.enc",
        key
    )
    decrypt_file(
        "data/sample.enc",
        "data/sample_decrypted.txt",
        key
    )
    with open("data/sample.txt", "rb") as file:
        original = file.read()
    with open("data/sample_decrypted.txt", "rb") as file:
        decrypted = file.read()
    print("Match:", original == decrypted)
if __name__ == "__main__":
    main()