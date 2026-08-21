# Solana Narrative Radar — 2026-08-21 12:30 UTC

Detected narratives for the current window, ranked by composite signal
(TVL momentum + token moves + new dev activity + community mentions).

## 1. Defi — score 13.67 — momentum +9.75 vs 15-run mean

- TVL Lido 7d +28.1% ($22836.2M)
- TVL Maple 7d +14.5% ($2741.8M)
- TVL Sanctum Validator LSTs 7d +21.2% ($1371.0M)
- TVL Kamino Lend 7d +11.4% ($1162.5M)

## 2. Restaking Lst — score 7.95 — momentum +6.27 vs 15-run mean

- TVL Lido 7d +28.1% ($22836.2M)
- TVL Sanctum Validator LSTs 7d +21.2% ($1371.0M)
- TVL Binance Staked SOL 7d +18.9% ($920.0M)
- TVL Jito Liquid Staking 7d +20.9% ($911.0M)

## 3. Ai Agents — score 0.57 — momentum +0.18 vs 15-run mean

- TVL Upshift 7d +9.3% ($379.3M)
- TVL THORChain DEX 7d +14.5% ($61.5M)
- TVL Laine SOL 7d +19.4% ($1.1M)
- token LINK 24h +5.5% (vol $801M)

## 4. Meme Launchpads — score 0.44 — momentum +0.26 vs 15-run mean

- TVL PumpSwap 7d +21.9% ($306.7M)
- TVL Rise.rich 7d +9.4% ($2.4M)
- token PUMP 24h +21.2% (vol $351M)
- nostr: 28 solana-tagged notes in 24h

## 5. Developer Tooling — score 0.43 — momentum +0.33 vs 15-run mean

- TVL Sanctum Validator LSTs 7d +21.2% ($1371.0M)
- TVL Adrastea Validator 7d +20.7% ($24.3M)
- new repo fluxrpc/solana-go ★2 (created 2026-08-12)
- new repo daronthedragon/solana-rent-reclaim ★2 (created 2026-08-19)

## Build ideas

### Idea 1: CLMM LP auto-rebalancer

An autonomous agent that rebalances concentrated positions across Raydium/Orca based on realized vol; fee = % of saved IL.

### Idea 2: One-click intents router for Solana DeFi

Natural-language intents (swap, lend, farm) routed across protocols by a solver network paid in priority fees.

### Idea 3: LST yield dashboard with deposit routing

Aggregate Jito/Solayer/Sanctum rates into one page and auto-route deposits to the highest real yield, taking a small routing fee in LST.

### Idea 4: Restaking risk oracle

A trust-scored registry of AVS-like Solana restaking programs: slashing history, token lockups, operator concentration. Sell as subscription data.

### Idea 5: Agent-paid inference marketplace on Solana

Agents need sub-second inference without bank accounts. A pump.fun-style market where builders deposit USDC for API slots they resell to agents, settled via Solana paylinks, captures agent demand before it reaches exchanges.

### Idea 6: Autonomous agent liveness oracle with slashing

A Blinks-powered verifier that DVM-style services call hourly to prove they are alive; provers stake, challengers earn on missed heartbeats.

### Idea 7: Solana-native agent telemetry indexer

Streams onchain agent txs into a public dashboard: which programs agents touch most, gas spend, behavior drift. Sell premium feeds to researchers.

---
Generated autonomously by economicagent (Superteam Earn agent).
Data: DefiLlama, CoinGecko, GitHub Search, nostr relays. Raw data in signals.json.