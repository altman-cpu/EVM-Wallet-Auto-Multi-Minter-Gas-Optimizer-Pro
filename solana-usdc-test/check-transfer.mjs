// Read-only Solana checker. Holds no keys and sends nothing.
// Shows the wallet's SOL and USDC balances, and optionally whether a transfer signature confirmed
// and how much USDC the recipient received in that transaction.
//
// Env:
//   ADDRESS     wallet public key to inspect (required)
//   SIGNATURE   transaction signature to check (optional)
//   NETWORK     devnet | mainnet-beta (default mainnet-beta)
//   RPC_URL     custom RPC endpoint (optional)

import { pathToFileURL } from "node:url";
import { Connection, PublicKey, clusterApiUrl, LAMPORTS_PER_SOL } from "@solana/web3.js";
import { TOKEN_PROGRAM_ID } from "@solana/spl-token";
import { USDC_MINTS, USDC_DECIMALS } from "./send-usdc.mjs";

// Pure helper: the USDC change for one owner, from a transaction's pre/post token balances.
export function usdcDelta(meta, owner, mint) {
  const sum = (balances = []) =>
    balances
      .filter((b) => b.mint === mint && b.owner === owner)
      .reduce((acc, b) => acc + BigInt(b.uiTokenAmount.amount), 0n);
  return sum(meta.postTokenBalances) - sum(meta.preTokenBalances); // base units
}

const fmtUsdc = (raw) => (Number(raw) / 10 ** USDC_DECIMALS).toFixed(USDC_DECIMALS);

async function main() {
  const network = process.env.NETWORK || "mainnet-beta";
  if (!USDC_MINTS[network]) throw new Error(`NETWORK must be one of: ${Object.keys(USDC_MINTS).join(", ")}`);
  if (!process.env.ADDRESS) throw new Error("ADDRESS is required");
  const owner = new PublicKey(process.env.ADDRESS);
  const mint = USDC_MINTS[network];
  const connection = new Connection(process.env.RPC_URL || clusterApiUrl(network), "confirmed");

  const [lamports, tokenAccounts] = await Promise.all([
    connection.getBalance(owner),
    connection.getParsedTokenAccountsByOwner(owner, { mint: new PublicKey(mint) }, "confirmed"),
  ]);
  const usdc = tokenAccounts.value.reduce(
    (acc, a) => acc + BigInt(a.account.data.parsed.info.tokenAmount.amount),
    0n,
  );

  console.log(`Network:     ${network}`);
  console.log(`Address:     ${owner.toBase58()}`);
  console.log(`SOL:         ${(lamports / LAMPORTS_PER_SOL).toFixed(6)}`);
  console.log(`USDC:        ${fmtUsdc(usdc)} (${tokenAccounts.value.length} token account(s))`);

  if (process.env.SIGNATURE) {
    const sig = process.env.SIGNATURE;
    const [status] = (await connection.getSignatureStatuses([sig], { searchTransactionHistory: true })).value;
    if (!status) {
      console.log(`Signature:   ${sig}\nStatus:      NOT FOUND (not yet seen by this RPC, or wrong network)`);
    } else {
      const state = status.err ? `FAILED ${JSON.stringify(status.err)}` : status.confirmationStatus;
      console.log(`Signature:   ${sig}\nStatus:      ${state}`);
      if (!status.err) {
        const tx = await connection.getParsedTransaction(sig, { maxSupportedTransactionVersion: 0, commitment: "confirmed" });
        if (tx?.meta) {
          const received = usdcDelta(tx.meta, owner.toBase58(), mint);
          console.log(`USDC received by ADDRESS in this tx: ${fmtUsdc(received)}`);
        }
      }
    }
    console.log(`Explorer:    https://explorer.solana.com/tx/${sig}${network === "devnet" ? "?cluster=devnet" : ""}`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((err) => {
    console.error("ERROR:", err.message);
    process.exit(1);
  });
}
