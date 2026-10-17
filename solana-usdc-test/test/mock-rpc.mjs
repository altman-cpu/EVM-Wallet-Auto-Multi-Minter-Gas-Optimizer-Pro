// Local fake Solana JSON-RPC server for offline integration tests. NOT a live network. Port 8899.
import http from "node:http";

const MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
const TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
const ME = "43XYBNz43sjw8Y9UPfJka317vSddrPuoDG9vNkkNTeLu";
const SENDER = "11111111111111111111111111111111";
const SIG = "4fwgX16WDwYj5hZ2t5xEHz6UUnuaTovJpMeoWWEBvuA7z1baf1qX1BW2EGZVR9ChSyJZ8akeLX6EDTadFcEcSTdy";
const ctx = { slot: 100 };

function mintData() {
  const b = Buffer.alloc(82);
  b.writeUInt8(1, 45); // isInitialized
  b.writeUInt8(6, 44); // decimals
  return b.toString("base64");
}

const handlers = {
  getVersion: () => ({ "solana-core": "2.0.0", "feature-set": 1 }),
  getHealth: () => "ok",
  getSlot: () => 100,
  getBalance: ([pk]) => ({ context: ctx, value: 2_500_000_000 }),
  getLatestBlockhash: () => ({ context: ctx, value: { blockhash: "11111111111111111111111111111111", lastValidBlockHeight: 999 } }),
  getAccountInfo: ([pk]) => {
    if (pk === MINT) return { context: ctx, value: { data: [mintData(), "base64"], executable: false, lamports: 1461600, owner: TOKEN_PROGRAM, rentEpoch: 0, space: 82 } };
    return { context: ctx, value: null }; // recipient USDC account does not exist yet
  },
  getParsedTokenAccountsByOwner: ([owner]) => {
    if (owner !== ME) return { context: ctx, value: [] };
    return { context: ctx, value: [{
      pubkey: TOKEN_PROGRAM,
      account: { data: { program: "spl-token", space: 165, parsed: { type: "account", info: {
        mint: MINT, owner: ME, tokenAmount: { amount: "3000000", decimals: 6, uiAmount: 3, uiAmountString: "3" } } } },
        executable: false, lamports: 2039280, owner: TOKEN_PROGRAM, rentEpoch: 0, space: 165 },
    }] };
  },
  getTokenAccountsByOwner: (params) => handlers.getParsedTokenAccountsByOwner(params),
  getTokenAccountBalance: () => ({ context: ctx, value: { amount: "3000000", decimals: 6, uiAmount: 3, uiAmountString: "3" } }),
  getTransaction: (params) => handlers.getParsedTransaction(params),
  getSignatureStatuses: ([sigs]) => ({ context: ctx, value: sigs.map(() => ({ slot: 100, confirmations: null, err: null, confirmationStatus: "finalized" })) }),
  getParsedTransaction: () => ({
    slot: 100, blockTime: 1, version: "legacy",
    transaction: { signatures: [SIG], message: { accountKeys: [
      { pubkey: SENDER, signer: true, writable: true, source: "transaction" },
      { pubkey: ME, signer: false, writable: false, source: "transaction" }], instructions: [], recentBlockhash: "11111111111111111111111111111111" } },
    meta: { err: null, fee: 5000, innerInstructions: [], logMessages: [], preBalances: [1, 1], postBalances: [1, 1], rewards: [],
      preTokenBalances: [{ accountIndex: 2, mint: MINT, owner: ME, programId: TOKEN_PROGRAM, uiTokenAmount: { amount: "2000000", decimals: 6, uiAmount: 2, uiAmountString: "2" } }],
      postTokenBalances: [{ accountIndex: 2, mint: MINT, owner: ME, programId: TOKEN_PROGRAM, uiTokenAmount: { amount: "3000000", decimals: 6, uiAmount: 3, uiAmountString: "3" } }] },
  }),
  simulateTransaction: () => ({ context: ctx, value: { err: null, logs: ["Program log: mock simulate ok"], accounts: null, unitsConsumed: 1000 } }),
  sendTransaction: () => SIG,
  getFeeForMessage: () => ({ context: ctx, value: 5000 }),
};

http.createServer((req, res) => {
  let body = "";
  req.on("data", (c) => (body += c));
  req.on("end", () => {
    const reqs = JSON.parse(body || "{}");
    const answer = (r) => {
      const fn = handlers[r.method];
      console.log("rpc", r.method);
      if (!fn) return { jsonrpc: "2.0", id: r.id, error: { code: -32601, message: `mock: unsupported ${r.method}` } };
      return { jsonrpc: "2.0", id: r.id, result: fn(r.params || []) };
    };
    res.setHeader("content-type", "application/json");
    res.end(JSON.stringify(Array.isArray(reqs) ? reqs.map(answer) : answer(reqs)));
  });
}).listen(8899, "127.0.0.1", () => console.log("mock rpc on 8899"));
