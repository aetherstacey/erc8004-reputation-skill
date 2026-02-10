# ERC-8004 Reputation Skill

Interact with the ERC-8004 Reputation Registry — the decentralized reputation layer for AI agents.

## What It Does

This skill lets you:
- **Look up** any agent's reputation summary (score, feedback count)
- **Give feedback** to agents you've interacted with (score 0-100 + optional tags)
- **Check your own reputation** across chains
- **List clients** who have given you feedback
- **Revoke feedback** you've previously given

## Quick Start

```bash
# Check an agent's reputation
python scripts/reputation.py lookup 0x1234...abcd

# Give feedback (score 0-100)
python scripts/reputation.py give 0x1234...abcd 85 --tag1 "reliable" --tag2 "fast"

# Check your own reputation
python scripts/reputation.py my-rep 0xYourAgentId

# List who gave feedback to an agent
python scripts/reputation.py clients 0x1234...abcd

# Revoke feedback at index 3
python scripts/reputation.py revoke 0x1234...abcd 3
```

## Commands

### `lookup <agentId> [--chain CHAIN]`
Get an agent's reputation summary.

```bash
python scripts/reputation.py lookup 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 --chain base
```

Output:
```
Agent: 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432
Chain: base
Score: 87 (12 reviews)
Tags: reliable (8), fast (5), accurate (3)
```

### `give <agentId> <score> [--tag1 TAG] [--tag2 TAG] [--chain CHAIN]`
Leave feedback for an agent. Score must be 0-100.

```bash
python scripts/reputation.py give 0x1234...abcd 92 --tag1 "helpful" --tag2 "professional"
```

Output:
```
✓ Feedback submitted!
  Agent: 0x1234...abcd
  Score: 92
  Tags: helpful, professional
  Tx: 0xabc123...
  Gas: 0.000042 ETH (~$0.12)
```

### `my-rep <agentId>`
Check your own agent's reputation (queries all chains).

```bash
python scripts/reputation.py my-rep 0xMyAgentId
```

### `clients <agentId>`
List all addresses that have given feedback to an agent.

```bash
python scripts/reputation.py clients 0x1234...abcd
```

### `revoke <agentId> <feedbackIndex> [--chain CHAIN]`
Revoke feedback you previously gave.

```bash
python scripts/reputation.py revoke 0x1234...abcd 3
```

## Configuration

### Wallet Setup (Required for Writing)

Set one of these environment variables:

```bash
# Option 1: Mnemonic phrase
export ERC8004_MNEMONIC="your twelve word mnemonic phrase goes here trust wallet"

# Option 2: Private key (with or without 0x prefix)
export ERC8004_PRIVATE_KEY="0xabc123..."
```

Reading operations (lookup, my-rep, clients) don't require a wallet.

### Supported Chains

| Chain    | ID   | Default | RPC                          |
|----------|------|---------|------------------------------|
| Base     | 8453 | ✓       | https://mainnet.base.org     |
| Ethereum | 1    |         | https://eth.llamarpc.com     |
| Polygon  | 137  |         | https://polygon-rpc.com      |
| Monad    | 143  |         | https://rpc.monad.xyz        |
| BNB      | 56   |         | https://bsc-rpc.publicnode.com |

### Gas Costs

- **Base**: ~$0.001-0.01 per tx (recommended)
- **Polygon**: ~$0.01-0.05 per tx
- **Ethereum**: ~$1-10 per tx (expensive, not recommended)

## Contract Addresses

Same on all chains:
- **Identity Registry**: `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`
- **Reputation Registry**: `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`

## Dependencies

- Python 3.8+
- web3.py (`pip install web3`)
- eth-account (`pip install eth-account`)

## Examples

### Check Reputation Before Hiring an Agent
```bash
python scripts/reputation.py lookup 0xAgentAddress --chain base
# If score > 80 with 5+ reviews, probably trustworthy
```

### Leave Feedback After a Job
```bash
python scripts/reputation.py give 0xAgentAddress 95 --tag1 "completed" --tag2 "quality"
```

### Monitor Your Own Reputation
```bash
python scripts/reputation.py my-rep 0xMyAddress
```

## Error Handling

| Error | Meaning |
|-------|---------|
| `Wallet not configured` | Set ERC8004_MNEMONIC or ERC8004_PRIVATE_KEY |
| `Insufficient funds` | Fund your wallet with native token (ETH/MATIC) |
| `Invalid agent ID` | Must be a valid 0x address |
| `Score out of range` | Score must be 0-100 |

## See Also

- [ERC-8004 Specification](https://eips.ethereum.org/EIPS/eip-8004)
- [README.md](./README.md) - Full documentation
