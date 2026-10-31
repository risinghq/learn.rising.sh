// A fresh VAPID key pair in the form the secrets hold it: the uncompressed
// public point and the private scalar, both as base64url.
export async function vapidKeys(): Promise<{
  VAPID_PUBLIC_KEY: string;
  VAPID_PRIVATE_KEY: string;
}> {
  const pair = (await crypto.subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["sign", "verify"],
  )) as CryptoKeyPair;
  const raw = await crypto.subtle.exportKey("raw", pair.publicKey);
  const jwk = (await crypto.subtle.exportKey(
    "jwk",
    pair.privateKey,
  )) as JsonWebKey;
  return {
    VAPID_PUBLIC_KEY: Buffer.from(raw).toString("base64url"),
    VAPID_PRIVATE_KEY: jwk.d ?? "",
  };
}
