# Taken from https://github.com/ddps-lab/serverless-faas-workbench by Jeongchul Kim and Kyungyong Lee
from time import time
import random
import string

import functions_framework
import pyaes


def generate(length):
    letters = string.ascii_lowercase + string.digits
    return "".join(random.choice(letters) for i in range(length))


@functions_framework.http
def lambda_handler(request):
    print(request.get_json())
    request_json = request.get_json(silent=True)
    print(request_json)
    length_of_message = None
    num_of_iterations = None

    if request_json and "length_of_message" in request_json:
        length_of_message = request_json["length_of_message"]

    if request_json and "num_of_iterations" in request_json:
        num_of_iterations = request_json["num_of_iterations"]

    message = generate(length_of_message)

    # 128-bit key (16 bytes)
    KEY = b"\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,"

    start = time()
    for loops in range(num_of_iterations):
        aes = pyaes.AESModeOfOperationCTR(KEY)
        ciphertext = aes.encrypt(message)
        print(ciphertext)

        aes = pyaes.AESModeOfOperationCTR(KEY)
        plaintext = aes.decrypt(ciphertext)
        print(plaintext)
        aes = None

    latency = time() - start
    return {"response": latency}