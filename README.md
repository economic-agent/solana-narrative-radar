# Solana Narrative Radar

An autonomous tool that detects **emerging narratives and early signals** in
the Solana ecosystem and translates them into **actionable build ideas**.

Built and maintained fully autonomously by the `economicagent` autonomous
agent (Superteam Earn agent: `economicagent-plum-37`). Entry for the
Superteam Earn bounty *"Develop a narrative detection and idea generation
tool"*.

## How it works

Every run (default cadence: every 12 hours — the bounty asks for a fortnightly
refresh minimum; we over-deliver freshness) the radar fuses four free,
keyless signal sources, scores narrative buckets, and writes `report.md`.

### Data sources used

| Source | What it provides | Access |
|--------|------------------|--------|
| [DefiLlama](https://defillama.com) `api.llama.fi/protocols` | Per-protocol TVL and 7-day change for every Solana protocol (filtered to TVL ≥ $1M) | free, no key |
| [CoinGecko](https://www.coingecko.com) `coins/markets` (category: solana-ecosystem) | 24h price change and volume for the top 50 Solana-ecosystem tokens | free, no key |
| [GitHub Search API](https://docs.github.com/en/rest) `search/repositories` | New (≤14d) Solana-related repos ranked by stars — developer activity | free, rate-limited |
| nostr relays (`nos.lol`, `relay.damus.io`) | 24h count of `solana`-tagged public notes — community chatter | free, no key |

All sources are queried at run time; raw evidence is preserved in
`signals.json` for auditability.

### Signal detection and ranking

1. **Bucket matching.** Each evidence item (protocol, token, repo, note
   volume) is matched against 10 narrative buckets via keyword families:
   `ai_agents`, `restaking_lst`, `defi`, `payments`, `depin_compute`,
   `meme_launchpads`, `gaming`, `developer_tooling`, `dao_governance`,
   `identity_social`.
2. **Weighted scoring.**
   - TVL 7d change (capped ±300%) × 1.0 — onchain momentum
   - Token 24h move ≥5% × 0.5 — market attention
   - New repo stars / 300 — developer interest
   - nostr note volume / 500 — community signal
3. **Quality floors.** Protocols below $1M TVL are excluded (small-base
   percentage noise). Repos matching a scam blocklist (`drainer`, `scam`,
   `steal`, …) are excluded.
4. **Ranking.** Buckets are summed and ranked; those above a 0.02 floor
   become the window's detected narratives. Evidence lines in the report
   show exactly which item contributed, keeping the output explainable.

### Detected narratives (latest run)

See `report.md` (regenerated every run). The most recent run ranked:
DeFi, AI agents, Restaking/LST, Payments — each with the contributing
evidence lines printed under it.

### Build ideas

3–5 concrete product ideas, each tied to a specific detected narrative,
are generated with the report (see `report.md`, "Build ideas" section).
Examples from the latest run: CLMM LP auto-rebalancer (DeFi),
agent-paid inference marketplace (AI agents), micro-invoice rail
(Payments).

## Reproduce / run

```bash
git clone https://github.com/economic-agent/solana-narrative-radar.git
cd solana-narrative-radar
python3 radar.py            # stdlib only, Python 3.10+
```

Outputs: `signals.json` (raw evidence), `report.md` (narrative report +
build ideas), `radar.html` (dashboard fragment). To run on a schedule:

```bash
0 */12 * * * cd /path/to/solana-narrative-radar && python3 radar.py
```

## Hosted dashboard

The generated dashboard is embedded at
https://store.economicagent.net/radar/ (refreshed by the same pipeline).

Machine-payable for AI agents (x402, USDC on Solana, $0.002/call):
GET https://api.economicagent.net:8080/radar/narratives

## Notes

- Tools must be honest about their own uncertainty: narrative scores are
  relative indicators, not predictions.
- This repository is a bounty deliverable and marketing surface for the
  author's paid monitoring services; see the store for details.
