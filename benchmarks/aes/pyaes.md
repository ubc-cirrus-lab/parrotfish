THIS WIKI PAGE IS TAKEN FROM https://github.com/kmu-bigdata/serverless-faas-workbench/wiki/pyaes
Originally Written by: Jeongchul Kim and Kyungyong Lee
## Pyaes

Pyaes benchmark that performs private key-based encryption and decryption. It is a pure-Python implementation of the AES block-cipher algorithm in CTR mode.

**Library** : pyaes, time, json

[aws-build-deployment-package](https://github.com/kmu-bigdata/serverless-faas-workbench/wiki/aws-build-deployment-package) -> pyaes

```text
(message example)
58pjx102ajfdil3cphd1wlt9b1i5wo5c5ys0f82td2j68y7k5g2c5f5n06ez6brwltrfdq8shuy7rcnzk7qym3eqsmfzuz5k7mjo
(encrypt message ciphertext) 
���������単}�����6�����     va��m��Puf/wf1��    2�A��O;R�טi�et�,=xƴ�oe���xa%0b
```
<img src='https://user-images.githubusercontent.com/10591350/65368805-9d084400-dc80-11e9-8937-d014a3352f5a.png' width=800px>

**Input**(test-event) example:
```json
{
    "length_of_message": [LENGTH OF MESSAGE],
    "num_of_iterations": [NUMBER OF ENCRYPT, DECRYPT ITERARTIONS]
}
```
**Output** : latency and cipertext
