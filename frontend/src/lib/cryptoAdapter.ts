import {
  base64ToBytes,
  bytesToBase64,
  utf8ToBytes,
  bytesToUtf8,
} from "./base64";
import { hkdfSha256 } from "./hkdf";
import { importAesGcmKey, aesGcmDecrypt, aesGcmEncrypt } from "./aes";

// ECDH/ECDSA-based placeholder for PQ KEM/signature to enable MVP interop.
// Keys are exported/imported as base64 (SPKI/PKCS8).

async function exportKey(
  format: "spki" | "pkcs8",
  key: CryptoKey
): Promise<string> {
  const buf = await crypto.subtle.exportKey(format, key);
  return bytesToBase64(new Uint8Array(buf));
}

async function importEcdhPublic(spkiB64: string): Promise<CryptoKey> {
  const spki = base64ToBytes(spkiB64);
  return crypto.subtle.importKey(
    "spki",
    spki,
    { name: "ECDH", namedCurve: "P-256" },
    true,
    []
  );
}

async function importEcdhPrivate(pkcs8B64: string): Promise<CryptoKey> {
  const pkcs8 = base64ToBytes(pkcs8B64);
  return crypto.subtle.importKey(
    "pkcs8",
    pkcs8,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    ["deriveBits"]
  );
}

async function importEcdsaPublic(spkiB64: string): Promise<CryptoKey> {
  const spki = base64ToBytes(spkiB64);
  return crypto.subtle.importKey(
    "spki",
    spki,
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["verify"]
  );
}

async function importEcdsaPrivate(pkcs8B64: string): Promise<CryptoKey> {
  const pkcs8 = base64ToBytes(pkcs8B64);
  return crypto.subtle.importKey(
    "pkcs8",
    pkcs8,
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["sign"]
  );
}

export type KemKeypair = { publicKeyB64: string; privateKeyB64: string };
export type SigKeypair = { publicKeyB64: string; privateKeyB64: string };

export async function generateKemKeypair(): Promise<KemKeypair> {
  const { publicKey, privateKey } = await crypto.subtle.generateKey(
    { name: "ECDH", namedCurve: "P-256" },
    true,
    ["deriveBits"]
  );
  return {
    publicKeyB64: await exportKey("spki", publicKey),
    privateKeyB64: await exportKey("pkcs8", privateKey),
  };
}

export async function generateSigKeypair(): Promise<SigKeypair> {
  const { publicKey, privateKey } = await crypto.subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["sign", "verify"]
  );
  return {
    publicKeyB64: await exportKey("spki", publicKey),
    privateKeyB64: await exportKey("pkcs8", privateKey),
  };
}

export async function encapsulate(recipientKemPkB64: string): Promise<{
  encapsulatedKeyB64: string; // ephemeral public key (SPKI, base64)
  sharedSecret: Uint8Array;
}> {
  // Generate ephemeral ECDH key
  const eph = await crypto.subtle.generateKey(
    { name: "ECDH", namedCurve: "P-256" },
    true,
    ["deriveBits"]
  );
  const recipientPub = await importEcdhPublic(recipientKemPkB64);
  const bits = await crypto.subtle.deriveBits(
    { name: "ECDH", public: recipientPub },
    eph.privateKey,
    256
  );
  const shared = new Uint8Array(bits);
  const encapsulatedKeyB64 = await exportKey("spki", eph.publicKey);
  return { encapsulatedKeyB64, sharedSecret: shared };
}

export async function decapsulate(
  encapsulatedKeyB64: string,
  kemSkB64: string
): Promise<Uint8Array> {
  const ephPub = await importEcdhPublic(encapsulatedKeyB64);
  const myPriv = await importEcdhPrivate(kemSkB64);
  const bits = await crypto.subtle.deriveBits(
    { name: "ECDH", public: ephPub },
    myPriv,
    256
  );
  return new Uint8Array(bits);
}

export async function deriveAesKey(
  sharedSecret: Uint8Array
): Promise<CryptoKey> {
  const info = utf8ToBytes("qchat-ecdh-aes-gcm");
  const salt = new Uint8Array(32); // zeros
  const keyBytes = await hkdfSha256(sharedSecret, salt, info, 32);
  return importAesGcmKey(keyBytes);
}

export async function sign(
  ciphertextB64: string,
  sigSkB64: string
): Promise<string> {
  const priv = await importEcdsaPrivate(sigSkB64);
  const data = base64ToBytes(ciphertextB64);
  const sig = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    priv,
    data
  );
  return bytesToBase64(new Uint8Array(sig));
}

export async function verify(
  ciphertextB64: string,
  signatureB64: string,
  sigPkB64: string
): Promise<boolean> {
  const pub = await importEcdsaPublic(sigPkB64);
  const data = base64ToBytes(ciphertextB64);
  const sig = base64ToBytes(signatureB64);
  return crypto.subtle.verify(
    { name: "ECDSA", hash: "SHA-256" },
    pub,
    sig,
    data
  );
}

export async function encryptTextToWire(
  plaintext: string,
  recipientKemPkB64: string,
  senderSigSkB64: string
): Promise<{
  ciphertext: string;
  nonce: string;
  encapsulated_key: string;
  signature: string;
}> {
  const { encapsulatedKeyB64, sharedSecret } = await encapsulate(
    recipientKemPkB64
  );
  const aesKey = await deriveAesKey(sharedSecret);
  const { nonceB64, ciphertextB64 } = await aesGcmEncrypt(
    aesKey,
    utf8ToBytes(plaintext)
  );
  const signature = await sign(ciphertextB64, senderSigSkB64);
  return {
    ciphertext: ciphertextB64,
    nonce: nonceB64,
    encapsulated_key: encapsulatedKeyB64,
    signature,
  };
}

export async function decryptWireToText(
  ciphertextB64: string,
  nonceB64: string,
  encapsulatedKeyB64: string,
  signatureB64: string,
  senderSigPkB64: string,
  myKemSkB64: string
): Promise<{ text?: string; trusted: boolean }> {
  const trusted = await verify(
    ciphertextB64,
    signatureB64,
    senderSigPkB64
  ).catch(() => false);
  try {
    const shared = await decapsulate(encapsulatedKeyB64, myKemSkB64);
    const aesKey = await deriveAesKey(shared);
    const pt = await aesGcmDecrypt(aesKey, nonceB64, ciphertextB64);
    return { text: bytesToUtf8(pt), trusted };
  } catch {
    return { text: undefined, trusted };
  }
}
