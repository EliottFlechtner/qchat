from pqc.kem import mceliece6960119 as kemalg


# 1. Keypair generation
pk, sk = kemalg.keypair()


# 2. Key encapsulation
ss, kem_ct = kemalg.encap(pk)


# 3. Key de-encapsulation
ss_result = kemalg.decap(kem_ct, sk)
assert ss_result == ss
