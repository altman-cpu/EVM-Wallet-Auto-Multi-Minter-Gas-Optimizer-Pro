# Solana USDC transfer test (to a Moonshot wallet)

Sends USDC (SPL token) from a Solana wallet **you control** to a recipient wallet, such as your Moonshot address.
It is a dry run by default. Nothing is broadcast until you set `SEND=1`.

## Important: how to know it works

- **Devnet** tests the script itself. Devnet tokens do **not** appear in Moonshot, which only shows mainnet.
- **Mainnet with a small amount (for example 1 USDC)** is the only way to see the transfer land in your Moonshot wallet. Use a real but small amount.
- This sandbox cannot reach Solana RPC, so the send has to run on your machine.

## Setup (on your machine)

Requires Node.js 18 or newer.

```bash
cd solana-usdc-test
npm install
npm run selftest          # offline checks, no network needed
```

## 1. Create a sender keypair

Use a wallet you control. For the mainnet test, it must hold real USDC and some SOL (about 0.01 SOL covers fees).

Using the Solana CLI:

```bash
solana-keygen new --outfile sender-keypair.json
```

Send the sender wallet some USDC. The sender's public key is printed by:

```bash
solana-keygen pubkey sender-keypair.json
```

The `.gitignore` already excludes `*keypair*.json`, so the key file will not be committed. Keep it private.

## 2. Get your Moonshot address

In Moonshot: **Settings > Export Keys**. Copy the address at the top of the page. It is a Solana address.

## 3a. Devnet check (script only)

```bash
# Dry run: builds and simulates, sends nothing. Needs devnet USDC in the sender wallet.
KEYPAIR_PATH=sender-keypair.json RECIPIENT=<MOONSHOT_ADDRESS> AMOUNT=1 npm run dry-run

# Real devnet send
KEYPAIR_PATH=sender-keypair.json RECIPIENT=<MOONSHOT_ADDRESS> AMOUNT=1 npm run send
```

Devnet USDC comes from https://faucet.circle.com (choose Solana Devnet). Devnet SOL comes from a Solana faucet.

## 3b. Mainnet test to Moonshot (real money)

```bash
# Always dry-run first
NETWORK=mainnet-beta CONFIRM_MAINNET=yes KEYPAIR_PATH=sender-keypair.json RECIPIENT=<MOONSHOT_ADDRESS> AMOUNT=1 npm run dry-run

# Then send
NETWORK=mainnet-beta CONFIRM_MAINNET=yes KEYPAIR_PATH=sender-keypair.json RECIPIENT=<MOONSHOT_ADDRESS> AMOUNT=1 npm run send
```

The script prints an explorer link for each transaction. Open it to see the status. Then check Moonshot's Holdings tab for USDC.

## Multiple transactions

Set `COUNT` to send several transfers one after another, each confirmed before the next:

```bash
COUNT=3 AMOUNT=1 ...   # 3 transfers of 1 USDC
```

Start with `COUNT=1` on mainnet.

## Environment variables

| Name | Required | Default | Meaning |
|---|---|---|---|
| `KEYPAIR_PATH` | yes | | Sender keypair JSON file |
| `RECIPIENT` | yes | | Recipient Solana address |
| `AMOUNT` | yes | | USDC per transfer (up to 6 decimals) |
| `COUNT` | no | 1 | Number of transfers (1 to 100) |
| `NETWORK` | no | devnet | `devnet` or `mainnet-beta` |
| `CONFIRM_MAINNET` | for mainnet | | Must be `yes` |
| `SEND` | no | unset | Set to `1` to broadcast. Unset means dry run |
| `RPC_URL` | no | public endpoint | Custom RPC, for example a paid provider |
