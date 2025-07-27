import oqs

# Use Kyber512 (or another algorithm like Kyber768, Classic-McEliece, NTRU, etc.)
algorithm = "Kyber512"

with oqs.KeyEncapsulation(algorithm) as kem:
    public_key = kem.generate_keypair()
    ciphertext, shared_secret_enc = kem.encap_secret(public_key)
    shared_secret_dec = kem.decap_secret(ciphertext)

    print("Ciphertext:", ciphertext.hex())
    print("Shared secret (encapsulated):", shared_secret_enc.hex())
    print("Shared secret (decapsulated):", shared_secret_dec.hex())
    print("Match:", shared_secret_enc == shared_secret_dec)
