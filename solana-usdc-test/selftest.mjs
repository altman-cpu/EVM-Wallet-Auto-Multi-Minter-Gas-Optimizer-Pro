// Offline checks: amount parsing, ATA derivation, and transfer instruction contents. No RPC needed.
import assert from "node:assert/strict";
import { Keypair, PublicKey } from "@solana/web3.js";
import {
  ASSOCIATED_TOKEN_PROGRAM_ID,
  TOKEN_PROGRAM_ID,
  decodeTransferCheckedInstruction,
} from "@solana/spl-token";
import { USDC_MINTS, usdcToBaseUnits, buildUsdcTransferTx } from "./send-usdc.mjs";

// 1. Amount parsing
assert.equal(usdcToBaseUnits("1"), 1_000_000n);
assert.equal(usdcToBaseUnits("0.25"), 250_000n);
assert.equal(usdcToBaseUnits("0.000001"), 1n);
for (const bad of ["0", "0.0", "-1", "1.0000001", "abc", "", "1e3"]) {
  assert.throws(() => usdcToBaseUnits(bad), `should reject ${JSON.stringify(bad)}`);
}
console.log("ok  amount parsing");

// 2. Mint addresses are valid
for (const [net, m] of Object.entries(USDC_MINTS)) {
  new PublicKey(m);
  console.log(`ok  ${net} mint ${m}`);
}

// 3. Transfer tx built for a recipient with no USDC account (expects ATA create + transferChecked)
const payer = Keypair.generate();
const recipient = Keypair.generate().publicKey;
const mint = new PublicKey(USDC_MINTS.devnet);
const blockhash = Keypair.generate().publicKey.toBase58(); // any valid 32-byte base58 value
const amountRaw = usdcToBaseUnits("2.5");

const [expectSource] = PublicKey.findProgramAddressSync(
  [payer.publicKey.toBuffer(), TOKEN_PROGRAM_ID.toBuffer(), mint.toBuffer()],
  ASSOCIATED_TOKEN_PROGRAM_ID,
);
const [expectRecipientAta] = PublicKey.findProgramAddressSync(
  [recipient.toBuffer(), TOKEN_PROGRAM_ID.toBuffer(), mint.toBuffer()],
  ASSOCIATED_TOKEN_PROGRAM_ID,
);

const { tx, sourceAta, recipientAta } = buildUsdcTransferTx({
  mint, payer: payer.publicKey, recipient, amountRaw, recipientAtaExists: false, blockhash,
});
assert.equal(sourceAta.toBase58(), expectSource.toBase58());
assert.equal(recipientAta.toBase58(), expectRecipientAta.toBase58());
assert.equal(tx.instructions.length, 2, "expected ATA create + transfer");
assert.equal(tx.instructions[0].programId.toBase58(), ASSOCIATED_TOKEN_PROGRAM_ID.toBase58());
const decoded = decodeTransferCheckedInstruction(tx.instructions[1]);
assert.equal(decoded.keys.source.pubkey.toBase58(), expectSource.toBase58());
assert.equal(decoded.keys.destination.pubkey.toBase58(), expectRecipientAta.toBase58());
assert.equal(decoded.keys.mint.pubkey.toBase58(), mint.toBase58());
assert.equal(decoded.keys.owner.pubkey.toBase58(), payer.publicKey.toBase58());
assert.equal(decoded.data.amount, 2_500_000n);
assert.equal(decoded.data.decimals, 6);
console.log("ok  transfer with ATA creation: accounts, amount 2.5 USDC, decimals 6");

// 4. Sign and serialize; signature must verify
tx.sign(payer);
assert.ok(tx.verifySignatures(), "signature should verify");
const wire = tx.serialize();
console.log(`ok  signed tx serializes to ${wire.length} bytes, signature verifies`);

// 5. Recipient account already exists: only the transfer instruction
const { tx: tx2 } = buildUsdcTransferTx({
  mint, payer: payer.publicKey, recipient, amountRaw: 1n, recipientAtaExists: true, blockhash,
});
assert.equal(tx2.instructions.length, 1);
console.log("ok  transfer without ATA creation when recipient account exists");

console.log("\nAll offline checks passed.");
