#!/usr/bin/env python3
"""Solana Narrative Radar v0.1

Detects emerging narratives in the Solana ecosystem by fusing four free,
keyless signal sources and ranking them with explainable scores:

  1. DefiLlama   - per-protocol TVL and 7d change (onchain activity)
  2. CoinGecko   - Solana-ecosystem token movers (price/volume)
  3. GitHub      - new Solana repos by stars (developer activity)
  4. nostr       - 24h mention counts for `solana` (community signal)

Outputs (into --out dir, default cwd):
  signals.json - raw collected evidence
  report.md    - narrative report with build ideas
  radar.html   - standalone dashboard fragment (embeddable)

No API keys required. Refresh cadence: every 12h (bounty asks fortnightly
minimum; we over-deliver freshness). Python 3.10+, stdlib only.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; solana-narrative-radar/0.1; +https://github.com/economic-agent/solana-narrative-radar)"}

NARRATIVES = {
    "ai_agents": ["ai", "agent", "autonomous", "llm", "swarm", "eliza", "grift", "inference", "claude", "gpt"],
    "restaking_lst": ["restak", "jito", "solayer", "sanctum", "vault", "lst", "stake", "liquid"],
    "defi": ["dex", "swap", "amm", "lend", "borrow", "yield", "perp", "liquid", "dlmm", "clmm"],
    "payments": ["pay", "checkout", "stablecoin", "usdc", "usdt", "payments"],
    "depin_compute": ["depin", "compute", "gpu", "bandwidth", "sensor", "iot", "node", "infra"],
    "meme_launchpads": ["meme", "pump", "launchpad", "token launch", "fun."],
    "gaming": ["game", "play-to", "onchain game", "play2"],
    "developer_tooling": ["rpc", "indexer", "oracle", "validator", "sdk", "zk", "blink", "action", "compiler", "audit"],
    "dao_governance": ["dao", "govern", "realms", "tribe"],
    "identity_social": ["identity", "social", "reputation", "did", "proof of", "profile"],
}


def fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def llama_solana():
    try:
        data = fetch_json("https://api.llama.fi/protocols")
    except Exception as e:
        return {"error": str(e)}, []
    rows = []
    for p in data:
        chains = p.get("chains") or [p.get("chain")]
        if "Solana" not in chains:
            continue
        tvl = float(p.get("tvl") or 0)
        if tvl < 1_000_000:
            continue
        rows.append({
            "name": p.get("name", "?"),
            "category": p.get("category", "?"),
            "tvl": tvl,
            "change_7d": float(p.get("change_7d") or 0),
        })
    rows.sort(key=lambda x: -x["tvl"])
    return {"protocols": rows[:40]}, rows


def coingecko_solana():
    url = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
           "&category=solana-ecosystem&order=volume_desc&per_page=50&page=1"
           "&price_change_percentage=24h")
    try:
        data = fetch_json(url)
    except Exception as e:
        return {"error": str(e)}, []
    rows = []
    for c in data:
        rows.append({
            "symbol": (c.get("symbol") or "?").upper(),
            "name": c.get("name", "?"),
            "price_change_24h": c.get("price_change_percentage_24h") or 0.0,
            "volume": c.get("total_volume") or 0.0,
            "market_cap": c.get("market_cap") or 0.0,
        })
    return {"tokens": rows[:50]}, rows


REPO_BLOCKLIST = ("drainer", "scam", "steal", "clipper", "rug", "phish", "wallet-grabber")


def github_new_solana_repos():
    since = (dt.date.today() - dt.timedelta(days=14)).isoformat()
    q = urllib.parse.quote(f"solana created:>{since}")
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=20"
    try:
        data = fetch_json(url)
    except Exception as e:
        return {"error": str(e)}, []
    rows = []
    for r in data.get("items", []):
        text = f"{r.get('full_name','')} {r.get('description') or ''}".lower()
        if any(w in text for w in REPO_BLOCKLIST):
            continue
        rows.append({
            "name": r.get("full_name", "?"),
            "description": (r.get("description") or "")[:160],
            "stars": r.get("stargazers_count") or 0,
            "created": r.get("created_at", "?")[:10],
        })
    return {"repos": rows}, rows


def nostr_mentions(relays=("wss://nos.lol", "wss://relay.damus.io"), limit=200):
    sys.path.insert(0, os.path.expanduser("~/autonomous-agent/tools"))
    try:
        import nostr_lib as N
    except Exception as e:
        return {"error": f"nostr_lib import: {e}"}
    now = int(time.time())
    day_ago = now - 86400
    sub = json.dumps(["REQ", "radar", {"kinds": [1], "#t": ["solana"], "limit": limit, "since": day_ago}])
    counts = {}
    seen = set()
    for url in relays:
        try:
            ws = N.WS(url, timeout=15)
            ws.connect()
            ws.send_text(sub)
            deadline = time.time() + 15
            got = 0
            while time.time() < deadline:
                msg = ws.recv_text()
                if not msg:
                    break
                if "EOSE" in msg:
                    break
                try:
                    ev = json.loads(msg)
                except Exception:
                    continue
                if ev[0] == "EVENT":
                    e = ev[2]
                    eid = e.get("id")
                    if eid in seen:
                        continue
                    seen.add(eid)
                    got += 1
                    hour = dt.datetime.fromtimestamp(e.get("created_at", now), tz=dt.UTC).strftime("%Y-%m-%dT%H:00Z")
                    counts[hour] = counts.get(hour, 0) + 1
            ws.close()
            counts.setdefault(f"_relay_{url}", got)
        except Exception as e:
            counts.setdefault(f"_relay_{url}", f"ERR {str(e)[:40]}")
    total = sum(v for k, v in counts.items() if not k.startswith("_"))
    return {"hourly_counts": counts, "total_24h": total}, counts


def match_buckets(text):
    text = text.lower()
    hits = {}
    for bucket, kws in NARRATIVES.items():
        score = sum(1 for kw in kws if kw in text)
        if score:
            hits[bucket] = score
    return hits


def score_buckets(llama_rows, cg_rows, gh_rows, nostr_total):
    scores = {b: 0.0 for b in NARRATIVES}
    evidence = {b: [] for b in NARRATIVES}

    for r in llama_rows:
        text = f"{r['name']} {r['category']}"
        for b in match_buckets(text):
            w = min(max(r["change_7d"], -100), 300) / 100.0
            if abs(w) >= 0.05:
                scores[b] += w
                evidence[b].append(f"TVL {r['name']} 7d {r['change_7d']:+.1f}% (${r['tvl']/1e6:.1f}M)")

    for t in cg_rows:
        text = f"{t['symbol']} {t['name']}"
        for b in match_buckets(text):
            p = t["price_change_24h"]
            if abs(p) >= 5:
                w = p / 100.0 * 0.5
                scores[b] += w
                evidence[b].append(f"token {t['symbol']} 24h {p:+.1f}% (vol ${t['volume']/1e6:.0f}M)")

    for r in gh_rows:
        text = f"{r['name']} {r['description']}"
        for b in match_buckets(text):
            w = min(r["stars"], 300) / 300.0
            scores[b] += w
            evidence[b].append(f"new repo {r['name']} ★{r['stars']} (created {r['created']})")

    if nostr_total:
        w = min(nostr_total, 500) / 500.0
        scores["ai_agents"] += w * 0.5
        scores["meme_launchpads"] += w * 0.3
        evidence["ai_agents"].append(f"nostr: {nostr_total} solana-tagged notes in 24h")
        evidence["meme_launchpads"].append(f"nostr: {nostr_total} solana-tagged notes in 24h")

    return scores, evidence


BUILD_IDEAS = {
    "ai_agents": [
        ("Agent-paid inference marketplace on Solana", "Agents need sub-second inference without bank accounts. A pump.fun-style market where builders deposit USDC for API slots they resell to agents, settled via Solana paylinks, captures agent demand before it reaches exchanges."),
        ("Autonomous agent liveness oracle with slashing", "A Blinks-powered verifier that DVM-style services call hourly to prove they are alive; provers stake, challengers earn on missed heartbeats."),
        ("Solana-native agent telemetry indexer", "Streams onchain agent txs into a public dashboard: which programs agents touch most, gas spend, behavior drift. Sell premium feeds to researchers."),
    ],
    "restaking_lst": [
        ("LST yield dashboard with deposit routing", "Aggregate Jito/Solayer/Sanctum rates into one page and auto-route deposits to the highest real yield, taking a small routing fee in LST."),
        ("Restaking risk oracle", "A trust-scored registry of AVS-like Solana restaking programs: slashing history, token lockups, operator concentration. Sell as subscription data."),
    ],
    "defi": [
        ("CLMM LP auto-rebalancer", "An autonomous agent that rebalances concentrated positions across Raydium/Orca based on realized vol; fee = % of saved IL."),
        ("One-click intents router for Solana DeFi", "Natural-language intents (swap, lend, farm) routed across protocols by a solver network paid in priority fees."),
    ],
    "payments": [
        ("Micro-invoice rail for content", "Nostr note = invoice: a relay plugin that turns any note into a Blink-powered paywall; creator pays 1%."),
        ("Paylink analytics suite", "Tracking + conversion dashboards for Solana paylink sellers; monetize with freemium tiers."),
    ],
    "depin_compute": [
        ("Spot-market GPU pricing oracle", "Index DePIN node rental prices to help buyers arbitrage between providers; oracle feeds paid via data subscriptions."),
    ],
    "meme_launchpads": [
        ("Launch-quality scoring API", "Onchain heuristics (liquidity lock, holder distribution, dev sell history) scoring new pump.fun tokens pre-trade."),
    ],
    "gaming": [
        ("Onchain-game session analytics", "Reads game programs to build per-game MAU/retention boards that no centralized analytics covers; charge games for dashboards."),
    ],
    "developer_tooling": [
        ("Gas & latency benchmark bot", "Continuous public RPC benchmark leaderboard for Solana providers; sell premium alerting to the providers themselves."),
    ],
    "dao_governance": [
        ("Realms vote-delegation matcher", "Match small token holders with aligned delegates by voting history similarity; take a bps fee on delegated voting rewards."),
    ],
    "identity_social": [
        ("Onchain reputation passport for DMs", "Scored Solana wallet reputation (age, activity, protocol diversity) to filter spam in social inboxes."),
    ],
}


def build_report(scores, evidence, ts):
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    ranked = [(b, s) for b, s in ranked if s > 0.02][:5]
    lines = []
    lines.append(f"# Solana Narrative Radar — {ts.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("Detected narratives for the current window, ranked by composite signal")
    lines.append("(TVL momentum + token moves + new dev activity + community mentions).")
    lines.append("")
    if not ranked:
        lines.append("No narrative cleared the signal threshold this run.")
        return "\n".join(lines)
    for i, (b, s) in enumerate(ranked, 1):
        label = b.replace("_", " ").title()
        lines.append(f"## {i}. {label} — score {s:.2f}")
        lines.append("")
        ev = evidence.get(b, [])[:4]
        for e in ev:
            lines.append(f"- {e}")
        lines.append("")
    lines.append("## Build ideas")
    lines.append("")
    n = 0
    for b, s in ranked:
        for title, desc in BUILD_IDEAS.get(b, []):
            n += 1
            lines.append(f"### Idea {n}: {title}")
            lines.append("")
            lines.append(desc)
            lines.append("")
        if n >= 5:
            break
    lines.append("---")
    lines.append("Generated autonomously by economicagent (Superteam Earn agent).")
    lines.append("Data: DefiLlama, CoinGecko, GitHub Search, nostr relays. Raw data in signals.json.")
    return "\n".join(lines)


def html_dashboard(ranked, ts):
    rows = "".join(
        f"<tr><td>{i}</td><td>{b.replace('_',' ').title()}</td><td>{s:.2f}</td></tr>"
        for i, (b, s) in enumerate(ranked[:5], 1)
    )
    return f"""<section id="radar">
<h2>Solana Narrative Radar</h2>
<p>Last refresh: {ts.strftime('%Y-%m-%d %H:%M UTC')}. Sources: DefiLlama TVL, CoinGecko, GitHub, nostr.</p>
<table>
<thead><tr><th>#</th><th>Narrative</th><th>Score</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<p><a href="https://github.com/economic-agent/solana-narrative-radar">repo</a> · <a href="https://github.com/economic-agent/solana-narrative-radar/blob/main/report.md">full report</a></p>
</section>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--no-html", action="store_true")
    args = ap.parse_args()
    ts = dt.datetime.now(dt.UTC)

    ll_sum, ll_rows = llama_solana()
    cg_sum, cg_rows = coingecko_solana()
    gh_sum, gh_rows = github_new_solana_repos()
    ns_sum, ns_counts = nostr_mentions()
    nostr_total = ns_sum.get("total_24h", 0) if isinstance(ns_sum, dict) else 0

    scores, evidence = score_buckets(ll_rows, cg_rows, gh_rows, nostr_total)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])

    signals = {
        "generated_at": ts.isoformat(),
        "defillama": ll_sum,
        "coingecko": cg_sum,
        "github": gh_sum,
        "nostr": ns_sum,
        "narrative_scores": {b: round(s, 3) for b, s in ranked},
        "ranked": ranked[:5],
    }
    report = build_report(scores, evidence, ts)

    with open(os.path.join(args.out, "signals.json"), "w") as f:
        json.dump(signals, f, indent=2)
    with open(os.path.join(args.out, "report.md"), "w") as f:
        f.write(report)
    if not args.no_html:
        with open(os.path.join(args.out, "radar.html"), "w") as f:
            f.write(html_dashboard(ranked, ts))
    print(report)


if __name__ == "__main__":
    main()
