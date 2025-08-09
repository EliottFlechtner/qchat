// HKDF-SHA-256 extract-and-expand to derive 32-byte key
// Using subtle.importKey and deriveBits via PBKDF-like workaround is not available; implement HKDF per RFC5869 with subtle HMAC

async function hmacSha256(
  key: CryptoKey,
  data: Uint8Array
): Promise<Uint8Array> {
  const sig = await crypto.subtle.sign("HMAC", key, data);
  return new Uint8Array(sig);
}

async function importHmacKey(keyBytes: Uint8Array): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    keyBytes,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
}

export async function hkdfSha256(
  ikm: Uint8Array,
  salt: Uint8Array,
  info: Uint8Array,
  outputLength = 32
): Promise<Uint8Array> {
  // Extract
  const prkKey = await importHmacKey(salt.length ? salt : new Uint8Array(32));
  const prk = await hmacSha256(prkKey, ikm);
  const prkCryptoKey = await importHmacKey(prk);

  // Expand
  const n = Math.ceil(outputLength / 32);
  const okm = new Uint8Array(outputLength);
  let previous = new Uint8Array();
  let offset = 0;
  for (let i = 1; i <= n; i++) {
    const input = new Uint8Array(previous.length + info.length + 1);
    input.set(previous, 0);
    input.set(info, previous.length);
    input[input.length - 1] = i;
    const t = await hmacSha256(prkCryptoKey, input);
    const toCopy = i < n ? 32 : outputLength - offset;
    okm.set(t.subarray(0, toCopy), offset);
    offset += toCopy;
    previous = t;
  }
  return okm;
}
