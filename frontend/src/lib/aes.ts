import { bytesToBase64, base64ToBytes } from "./base64";

export async function importAesGcmKey(rawKey: Uint8Array): Promise<CryptoKey> {
  return crypto.subtle.importKey("raw", rawKey, "AES-GCM", false, [
    "encrypt",
    "decrypt",
  ]);
}

export async function aesGcmEncrypt(
  key: CryptoKey,
  plaintext: Uint8Array
): Promise<{ nonceB64: string; ciphertextB64: string }> {
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce },
    key,
    plaintext
  );
  return {
    nonceB64: bytesToBase64(nonce),
    ciphertextB64: bytesToBase64(new Uint8Array(ct)),
  };
}

export async function aesGcmDecrypt(
  key: CryptoKey,
  nonceB64: string,
  ciphertextB64: string
): Promise<Uint8Array> {
  const nonce = base64ToBytes(nonceB64);
  const ct = base64ToBytes(ciphertextB64);
  const pt = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: nonce },
    key,
    ct
  );
  return new Uint8Array(pt);
}
