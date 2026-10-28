/** 128-bit random id, base64url without padding (22 chars). */
function randomId(bytes = 16): string {
  return Buffer.from(crypto.getRandomValues(new Uint8Array(bytes))).toString("base64url");
}

export const newRoomId = () => randomId(16);
/** 12 random bytes → 16 base64url chars. */
export const newIdentity = () => `u_${randomId(12)}`;
/** 24 random bytes → 32 base64url chars. */
export const newSeatKey = () => randomId(24);
/** Seat keys are stored hashed, so a database leak cannot be used to take seats. */
export const hashSeatKey = (key: string) =>
  new Bun.CryptoHasher("sha256").update(key).digest("hex");
