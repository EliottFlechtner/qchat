import {bytesToBase64} from './base64';
import type {InboxMessageWire} from './types';

export function computeMessageId(wire: InboxMessageWire): string {
  // Deterministic id from fields
  const concat = `${wire.sender}|${wire.nonce}|${wire.ciphertext}|${
      wire.signature}|${wire.encapsulated_key}|${wire.sent_at}`;
  // Simple hash
  let h = 0;
  for (let i = 0; i < concat.length; i++) {
    h = (h * 31 + concat.charCodeAt(i)) >>> 0;
  }
  return bytesToBase64(new TextEncoder().encode(String(h)));
}
