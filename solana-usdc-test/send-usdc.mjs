// Send USDC (SPL token) from a wallet you control to a single recipient wallet.
//
// Safety defaults:
//   - Dry run unless SEND=1 is set. A dry run builds and simulates the transfer(s) and sends nothing.
//   - Devnet unless NETWORK=mainnet-beta is set. Mainnet also needs CONFIRM_MAINNET=yes.
//   - The sending keypair is read from a file you point to. Its secret key is never printed or stored.
//
// Required env:
//   KEYPAIR_PATH   path to the sender's Solana keypair JSON (solana-keygen format: a 64-number array)
//   RECIPIENT      recipient wallet public key (base58), e.g. your Moonshot Solana address
//   AMOUNT         USDC per transfer, e.g. 1 or 0.5 (up to 6 decimals)
// Optional env:
//   COUNT          number of transfers to send, one after another (default 1)
//   NETWORK        devnet (default) | mainnet-beta
//   RPC_URL        custom RPC endpoint (default: public endpoint for NETWORK)
//   SEND           set to 1 to actually broadcast (default: dry run)
//   CONFIRM_MAINNET set to yes to allow mainnet-beta

import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import {
  Connection,
  Keypair,
  PublicKey,
  Transaction,
  clusterApiUrl,
  sendAndConfirmTransaction,
} from "@solana/web3.js";
import {
  TOKEN_PROGRAM_ID,
  getAssociatedTokenAddressSync,
  createAssociatedTokenAccountInstruction,
  createTransferCheckedInstruction,
  getMint,
} from "@solana/spl-token";

export const USDC_MINTS = {
  devnet: "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU", // Circle USDC on devnet
  "mainnet-beta": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", // Circle USDC on mainnet
};
export const USDC_DECIMALS = 6;

// Convert a decimal USDC string ("1", "0.25") into base units (BigInt). Throws on bad input.
export function usdcToBaseUnits(amount) {
  const s = String(amount).trim();
  if (!/^\d+(\.\d{1,6})?$/.test(s)) {
    throw new Error(`AMOUNT must be a positive number with at most ${USDC_DECIMALS} decimals, got "${amount}"`);
  }
  const [whole, frac = ""] = s.split(".");
  const raw = BigInt(whole) * 10n ** BigInt(USDC_DECIMALS) + BigInt((frac + "000000").slice(0, USDC_DECIMALS));
  if (raw <= 0n) throw new Error("AMOUNT must be greater than 0");
  return raw;
}

// Build one unsigned transfer transaction. Creates the recipient's USDC token account if it does not exist.
// Pure function, so it can be tested without network access when the caller supplies the blockhash.
export function buildUsdcTransferTx({ mint, payer, recipient, amountRaw, recipientAtaExists, blockhash }) {
  const sourceAta = getAssociatedTokenAddressSync(mint, payer, false, TOKEN_PROGRAM_ID);
  const recipientAta = getAssociatedTokenAddressSync(mint, recipient, false, TOKEN_PROGRAM_ID);

  const tx = new Transaction();
  if (!recipientAtaExists) {
    tx.add(createAssociatedTokenAccountInstruction(payer, recipientAta, recipient, mint, TOKEN_PROGRAM_ID));
  }
  tx.add(
    createTransferCheckedInstruction(
      sourceAta,
      mint,
      recipientAta,
      payer,
      amountRaw,
      USDC_DECIMALS,
      [],
      TOKEN_PROGRAM_ID,
    ),
  );
  tx.feePayer = payer;
  tx.recentBlockhash = blockhash;
  return { tx, sourceAta, recipientAta };
}

function loadKeypair(path) {
  const secret = JSON.parse(readFileSync(path, "utf8"));
  if (!Array.isArray(secret) || secret.length !== 64) {
    throw new Error("KEYPAIR_PATH must point to a solana-keygen JSON file (64-number array)");
  }
  return Keypair.fromSecretKey(Uint8Array.from(secret));
}

async function main() {
  const network = process.env.NETWORK || "devnet";
  if (!USDC_MINTS[network]) throw new Error(`NETWORK must be one of: ${Object.keys(USDC_MINTS).join(", ")}`);
  if (network === "mainnet-beta" && process.env.CONFIRM_MAINNET !== "yes") {
    throw new Error("Mainnet is blocked. Set CONFIRM_MAINNET=yes to allow real-money transfers.");
  }
  if (!process.env.KEYPAIR_PATH) throw new Error("KEYPAIR_PATH is required");
  if (!process.env.RECIPIENT) throw new Error("RECIPIENT is required");
  if (!process.env.AMOUNT) throw new Error("AMOUNT is required");

  const count = Number(process.env.COUNT || 1);
  if (!Number.isInteger(count) || count < 1 || count > 100) throw new Error("COUNT must be an integer from 1 to 100");

  const amountRaw = usdcToBaseUnits(process.env.AMOUNT);
  const payer = loadKeypair(process.env.KEYPAIR_PATH);
  const recipient = new PublicKey(process.env.RECIPIENT);
  const mint = new PublicKey(USDC_MINTS[network]);
  const connection = new Connection(process.env.RPC_URL || clusterApiUrl(network), "confirmed");
  const send = process.env.SEND === "1";

  const mintInfo = await getMint(connection, mint, "confirmed", TOKEN_PROGRAM_ID);
  if (mintInfo.decimals !== USDC_DECIMALS) throw new Error(`Unexpected USDC decimals: ${mintInfo.decimals}`);

  const sourceAta = getAssociatedTokenAddressSync(mint, payer.publicKey, false, TOKEN_PROGRAM_ID);
  const recipientAta = getAssociatedTokenAddressSync(mint, recipient, false, TOKEN_PROGRAM_ID);

  const [sourceTokenBal, solBal, recipientAtaInfo] = await Promise.all([
    connection.getTokenAccountBalance(sourceAta).then((r) => BigInt(r.value.amount)).catch(() => 0n),
    connection.getBalance(payer.publicKey),
    connection.getAccountInfo(recipientAta),
  ]);

  const totalRaw = amountRaw * BigInt(count);
  const fmt = (raw) => (Number(raw) / 10 ** USDC_DECIMALS).toFixed(USDC_DECIMALS);

  console.log(`Network:          ${network}`);
  console.log(`Mode:             ${send ? "SEND (broadcasting)" : "DRY RUN (nothing will be sent)"}`);
  console.log(`Sender:           ${payer.publicKey.toBase58()}`);
  console.log(`Sender USDC ATA:  ${sourceAta.toBase58()}`);
  console.log(`Sender USDC bal:  ${fmt(sourceTokenBal)}`);
  console.log(`Sender SOL bal:   ${(solBal / 1e9).toFixed(4)} (needed for fees and rent)`);
  console.log(`Recipient:        ${recipient.toBase58()}`);
  console.log(`Recipient ATA:    ${recipientAta.toBase58()} (${recipientAtaInfo ? "exists" : "will be created"})`);
  console.log(`Transfers:        ${count} x ${fmt(amountRaw)} USDC = ${fmt(totalRaw)} USDC total`);

  if (sourceTokenBal < totalRaw) {
    throw new Error(`Insufficient USDC: have ${fmt(sourceTokenBal)}, need ${fmt(totalRaw)}`);
  }
  if (solBal < 0.01 * 1e9) {
    throw new Error("Sender has less than 0.01 SOL, which is too little for fees. Fund the sender with SOL first.");
  }

  for (let i = 1; i <= count; i++) {
    const { blockhash } = await connection.getLatestBlockhash("confirmed");
    // Only the first transfer creates the recipient ATA if it is missing.
    const { tx } = buildUsdcTransferTx({
      mint,
      payer: payer.publicKey,
      recipient,
      amountRaw,
      // The first real send creates the ATA, so later sends can skip creating it. A dry run sends nothing, so it must not assume that.
      recipientAtaExists: !!recipientAtaInfo || (send && i > 1),
      blockhash,
    });
    tx.sign(payer);

    if (!send) {
      const sim = await connection.simulateTransaction(tx);
      const status = sim.value.err ? `FAILED ${JSON.stringify(sim.value.err)}` : "OK";
      console.log(`[${i}/${count}] simulation ${status}`);
      if (sim.value.logs) sim.value.logs.slice(-3).forEach((l) => console.log("    " + l));
      continue;
    }

    const sig = await sendAndConfirmTransaction(connection, tx, [payer], { commitment: "confirmed" });
    const cluster = network === "devnet" ? "?cluster=devnet" : "";
    console.log(`[${i}/${count}] sent ${fmt(amountRaw)} USDC: ${sig}`);
    console.log(`        https://explorer.solana.com/tx/${sig}${cluster}`);
  }

  console.log(send ? "Done. Check the recipient wallet, which may take a few seconds to update." : "Dry run complete. Re-run with SEND=1 to broadcast.");
}

// Run only when executed directly, not when imported by selftest.mjs.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((err) => {
    console.error("ERROR:", err.message);
    process.exit(1);
  });
}
