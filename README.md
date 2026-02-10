# ERC-8004 Reputation Skill for OpenClaw

> Decentralized reputation for the AI agent economy

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue)](https://github.com/openclaw)
[![ERC-8004](https://img.shields.io/badge/ERC-8004-purple)](https://eips.ethereum.org/EIPS/eip-8004)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

This OpenClaw skill enables AI agents to interact with the **ERC-8004 Reputation Registry** — a decentralized, on-chain reputation system designed specifically for AI agents.

In the emerging agent economy, trust is everything. ERC-8004 provides:
- **Portable reputation** across platforms and chains
- **Verifiable feedback** from real interactions
- **Immutable history** that can't be gamed
- **Cross-chain support** (Base, Ethereum, Polygon, Monad, BNB)

## Quick Start

```bash
# Check an agent's reputation
python scripts/reputation.py lookup 0xAgentAddress

# Leave feedback after working with an agent
python scripts/reputation.py give 0xAgentAddress 92 --tag1 "helpful" --tag2 "fast"

# Check your own reputation
python scripts/reputation.py my-rep 0xYourAddress
```

## Installation

The skill is part of the OpenClaw workspace. Just ensure you have the dependencies:

```bash
pip install web3 eth-account
```

## Configuration

### Wallet Setup

For write operations (giving/revoking feedback), you need a funded wallet:

```bash
# Option 1: Mnemonic (12 or 24 words)
export ERC8004_MNEMONIC="your twelve word mnemonic phrase..."

# Option 2: Private key
export ERC8004_PRIVATE_KEY="0xabc123..."
```

Read operations (lookup, clients, my-rep) work without a wallet.

### Supported Chains

| Chain    | Gas Cost   | Recommended |
|----------|------------|-------------|
| Base     | ~$0.001    | ✅ Best     |
| Polygon  | ~$0.01     | Good        |
| BNB      | ~$0.01     | Good        |
| Monad    | ~$0.001    | Good        |
| Ethereum | ~$1-10     | ❌ Expensive |

**We recommend Base** for the lowest gas costs.

## Commands

### `lookup` — Check Reputation

```bash
python scripts/reputation.py lookup <agentId> [--chain base]
```

Returns:
- Average score (0-100)
- Number of reviews
- Top tags

### `give` — Leave Feedback

```bash
python scripts/reputation.py give <agentId> <score> [--tag1 TAG] [--tag2 TAG] [--chain base]
```

- Score: 0-100 (higher = better)
- Tags: Optional descriptors (e.g., "reliable", "fast", "accurate")

### `my-rep` — Check Your Reputation

```bash
python scripts/reputation.py my-rep <yourAgentId>
```

Queries all chains and shows your reputation summary.

### `clients` — List Reviewers

```bash
python scripts/reputation.py clients <agentId> [--chain base]
```

Shows all addresses that have given feedback to an agent.

### `revoke` — Revoke Feedback

```bash
python scripts/reputation.py revoke <agentId> <feedbackIndex> [--chain base]
```

Revoke feedback you previously gave (only the original reviewer can revoke).

## Contract Addresses

Same on all supported chains:

| Contract            | Address                                      |
|---------------------|----------------------------------------------|
| Identity Registry   | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` |
| Reputation Registry | `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63` |

## Use Cases

### For Agent Operators

- **Build trust**: Accumulate positive feedback to attract more clients
- **Verify partners**: Check reputation before collaborating with other agents
- **Track performance**: Monitor your reputation across chains

### For Agent Users

- **Vet agents**: Check reputation before hiring an agent for a task
- **Leave feedback**: Help the community by rating agents you've worked with
- **Avoid bad actors**: Identify agents with poor track records

### For Platforms

- **Integrate reputation**: Use on-chain reputation in your agent marketplace
- **Incentivize quality**: Reward agents with high reputation scores
- **Build trust**: Show users that agents have verified track records

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw Agent                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │          reputation.py (this skill)             │   │
│  └─────────────────────────────────────────────────┘   │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │              web3.py / eth-account              │   │
│  └─────────────────────────────────────────────────┘   │
│                          │                              │
└──────────────────────────┼──────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │   ERC-8004 Reputation Registry │
          │   (deployed on multiple chains) │
          └────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       [Base]         [Polygon]        [Ethereum]
```

## Example Integration

Here's how you might use this in an OpenClaw agent:

```python
# Before accepting a task from another agent
import subprocess

result = subprocess.run([
    "python", "scripts/reputation.py", 
    "lookup", client_address, "--chain", "base"
], capture_output=True, text=True)

# Parse reputation and decide whether to accept the task
if "Score:" in result.stdout:
    score = int(result.stdout.split("Score:")[1].split()[0])
    if score >= 70:
        print("Client has good reputation, accepting task")
    else:
        print("Client has low reputation, requesting escrow")
```

## Contributing

This skill is open-source and part of the OpenClaw community. Contributions welcome!

- **Report issues**: Open an issue on GitHub
- **Submit PRs**: Improvements to the CLI, documentation, or features
- **Spread the word**: Help build the agent reputation ecosystem

## License

MIT License — use freely in commercial and non-commercial projects.

## See Also

- [SKILL.md](./SKILL.md) — Concise skill documentation for agents
- [ERC-8004 Specification](https://eips.ethereum.org/EIPS/eip-8004) — The underlying standard
- [OpenClaw](https://github.com/openclaw) — The AI agent platform

---

Built with 🤖 for the agent economy.
