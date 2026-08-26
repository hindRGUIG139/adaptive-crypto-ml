from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def encrypt_file(input_file, output_file, key):
    with open(input_file, "rb") as file:
        plaintext = file.read()

    cipher = AES.new(key, AES.MODE_CTR)
    ciphertext = cipher.encrypt(plaintext)

    with open(output_file, "wb") as file:
        file.write(cipher.nonce)
        file.write(ciphertext)

def decrypt_file(input_file, output_file, key):

    with open(input_file, "rb") as file:
        nonce = file.read(8)
        ciphertext = file.read()

    cipher = AES.new(
        key,
        AES.MODE_CTR,
        nonce=nonce
    )
    plaintext = cipher.decrypt(ciphertext)

    with open(output_file, "wb") as file:
        file.write(plaintext)

def main():
    key = get_random_bytes(32) # AES-256 key
    encrypt_file("data/csv1.csv", "data/sample.enc", key)
    decrypt_file("data/sample.enc", "data/sample_decrypted.csv", key)

    with open("data/csv1.csv", "rb") as file:
        original = file.read()
    with open("data/csv1.csv", "rb") as file:
        decrypted = file.read()
    print("Match:", original == decrypted)  # this is the real test
if __name__ == "__main__":
  main()