from Crypto.Cipher import AES #Import the AES module from the PyCryptodome library
from Crypto.Random import get_random_bytes 
key = get_random_bytes(16) #AES-128 requires a 16-byte key
with open("data/sample.txt", "rb") as file:
    plaintext = file.read()