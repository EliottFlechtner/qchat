import oqs

import base64

with oqs.KeyEncapsulation("Kyber512") as kem:
    public_key = kem.generate_keypair()
    b64_pubkey = base64.b64encode(public_key).decode()

    print("Base64 Public Key:")
    print(b64_pubkey)
