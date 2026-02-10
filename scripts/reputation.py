#!/usr/bin/env python3
"""
ERC-8004 Reputation Registry CLI

Interact with the decentralized reputation layer for AI agents.
Part of the OpenClaw skill ecosystem.

Usage:
    python reputation.py lookup <agentId> [--chain base|ethereum|polygon|monad|bnb]
    python reputation.py give <agentId> <score> [--tag1 TAG] [--tag2 TAG] [--chain CHAIN]
    python reputation.py my-rep <agentId>
    python reputation.py clients <agentId> [--chain CHAIN]
    python reputation.py revoke <agentId> <feedbackIndex> [--chain CHAIN]
"""

import argparse
import json
import os
import sys
from typing import Optional, Tuple

from web3 import Web3
from eth_account import Account

# =============================================================================
# CONSTANTS
# =============================================================================

# Contract addresses (same on all chains)
IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
REPUTATION_REGISTRY = "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63"

# Chain configurations
CHAINS = {
    "base": {
        "id": 8453,
        "rpc": "https://mainnet.base.org",
        "name": "Base",
        "symbol": "ETH",
    },
    "ethereum": {
        "id": 1,
        "rpc": "https://eth.llamarpc.com",
        "name": "Ethereum",
        "symbol": "ETH",
    },
    "polygon": {
        "id": 137,
        "rpc": "https://polygon-rpc.com",
        "name": "Polygon",
        "symbol": "MATIC",
    },
    "monad": {
        "id": 143,
        "rpc": "https://rpc.monad.xyz",
        "name": "Monad",
        "symbol": "MON",
    },
    "bnb": {
        "id": 56,
        "rpc": "https://bsc-rpc.publicnode.com",
        "name": "BNB Chain",
        "symbol": "BNB",
    },
}

DEFAULT_CHAIN = "base"

# Reputation Registry ABI (minimal, only what we need)
REPUTATION_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "agent", "type": "address"},
            {"internalType": "uint8", "name": "score", "type": "uint8"},
            {"internalType": "bytes32", "name": "tag1", "type": "bytes32"},
            {"internalType": "bytes32", "name": "tag2", "type": "bytes32"},
        ],
        "name": "giveFeedback",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "agent", "type": "address"},
            {"internalType": "uint256", "name": "index", "type": "uint256"},
        ],
        "name": "readFeedback",
        "outputs": [
            {"internalType": "address", "name": "reviewer", "type": "address"},
            {"internalType": "uint8", "name": "score", "type": "uint8"},
            {"internalType": "bytes32", "name": "tag1", "type": "bytes32"},
            {"internalType": "bytes32", "name": "tag2", "type": "bytes32"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "bool", "name": "revoked", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "agent", "type": "address"}],
        "name": "readAllFeedback",
        "outputs": [
            {
                "components": [
                    {"internalType": "address", "name": "reviewer", "type": "address"},
                    {"internalType": "uint8", "name": "score", "type": "uint8"},
                    {"internalType": "bytes32", "name": "tag1", "type": "bytes32"},
                    {"internalType": "bytes32", "name": "tag2", "type": "bytes32"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                    {"internalType": "bool", "name": "revoked", "type": "bool"},
                ],
                "internalType": "struct IReputationRegistry.Feedback[]",
                "name": "",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "agent", "type": "address"}],
        "name": "getSummary",
        "outputs": [
            {"internalType": "uint256", "name": "totalScore", "type": "uint256"},
            {"internalType": "uint256", "name": "feedbackCount", "type": "uint256"},
            {"internalType": "uint256", "name": "averageScore", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "agent", "type": "address"},
            {"internalType": "uint256", "name": "index", "type": "uint256"},
        ],
        "name": "revokeFeedback",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "agent", "type": "address"}],
        "name": "getClients",
        "outputs": [
            {"internalType": "address[]", "name": "", "type": "address[]"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "agent", "type": "address"}],
        "name": "getLastIndex",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "agent", "type": "address"},
            {"internalType": "uint256", "name": "feedbackIndex", "type": "uint256"},
            {"internalType": "string", "name": "response", "type": "string"},
        ],
        "name": "appendResponse",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "agent", "type": "address"},
            {"internalType": "uint256", "name": "feedbackIndex", "type": "uint256"},
        ],
        "name": "getResponseCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


# =============================================================================
# HELPERS
# =============================================================================


def get_web3(chain: str) -> Web3:
    """Get Web3 instance for the specified chain."""
    if chain not in CHAINS:
        raise ValueError(f"Unsupported chain: {chain}. Use: {', '.join(CHAINS.keys())}")
    
    rpc_url = CHAINS[chain]["rpc"]
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to {chain} RPC: {rpc_url}")
    
    return w3


def get_contract(w3: Web3):
    """Get Reputation Registry contract instance."""
    return w3.eth.contract(
        address=Web3.to_checksum_address(REPUTATION_REGISTRY),
        abi=REPUTATION_ABI,
    )


def get_wallet() -> Optional[Account]:
    """Load wallet from environment variables."""
    mnemonic = os.environ.get("ERC8004_MNEMONIC")
    private_key = os.environ.get("ERC8004_PRIVATE_KEY")
    
    if mnemonic:
        Account.enable_unaudited_hdwallet_features()
        return Account.from_mnemonic(mnemonic)
    elif private_key:
        # Strip 0x prefix if present
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        return Account.from_key(private_key)
    
    return None


def validate_address(address: str) -> str:
    """Validate and checksum an Ethereum address."""
    if not address.startswith("0x") or len(address) != 42:
        raise ValueError(f"Invalid address format: {address}")
    
    try:
        return Web3.to_checksum_address(address)
    except Exception:
        raise ValueError(f"Invalid address: {address}")


def bytes32_from_string(s: str) -> bytes:
    """Convert a string to bytes32 (padded or truncated)."""
    if not s:
        return b'\x00' * 32
    
    encoded = s.encode('utf-8')[:32]
    return encoded.ljust(32, b'\x00')


def string_from_bytes32(b: bytes) -> str:
    """Convert bytes32 to a string (strip null bytes)."""
    return b.rstrip(b'\x00').decode('utf-8', errors='ignore')


def format_wei(wei: int, symbol: str) -> str:
    """Format wei as readable token amount."""
    eth = wei / 10**18
    return f"{eth:.6f} {symbol}"


# =============================================================================
# COMMANDS
# =============================================================================


def cmd_lookup(args):
    """Look up an agent's reputation summary."""
    agent = validate_address(args.agent_id)
    chain = args.chain or DEFAULT_CHAIN
    
    w3 = get_web3(chain)
    contract = get_contract(w3)
    
    try:
        total_score, feedback_count, avg_score = contract.functions.getSummary(agent).call()
    except Exception as e:
        # Contract may revert for addresses with no feedback, treat as no feedback
        error_str = str(e).lower()
        if 'revert' in error_str or 'execution' in error_str:
            total_score, feedback_count, avg_score = 0, 0, 0
        else:
            print(f"Error querying reputation: {e}", file=sys.stderr)
            sys.exit(1)
    
    print(f"Agent: {agent}")
    print(f"Chain: {chain} ({CHAINS[chain]['name']})")
    
    if feedback_count == 0:
        print("Score: No feedback yet")
        return
    
    print(f"Score: {avg_score} ({feedback_count} reviews)")
    
    # Get detailed feedback to count tags
    try:
        all_feedback = contract.functions.readAllFeedback(agent).call()
        tag_counts = {}
        
        for fb in all_feedback:
            if fb[5]:  # revoked
                continue
            
            tag1 = string_from_bytes32(fb[2])
            tag2 = string_from_bytes32(fb[3])
            
            if tag1:
                tag_counts[tag1] = tag_counts.get(tag1, 0) + 1
            if tag2:
                tag_counts[tag2] = tag_counts.get(tag2, 0) + 1
        
        if tag_counts:
            sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
            tag_str = ", ".join(f"{tag} ({count})" for tag, count in sorted_tags[:5])
            print(f"Tags: {tag_str}")
    except Exception:
        pass  # Tags are optional info


def cmd_give(args):
    """Give feedback to an agent."""
    agent = validate_address(args.agent_id)
    score = int(args.score)
    chain = args.chain or DEFAULT_CHAIN
    
    if not 0 <= score <= 100:
        print("Error: Score must be between 0 and 100", file=sys.stderr)
        sys.exit(1)
    
    wallet = get_wallet()
    if not wallet:
        print("Error: Wallet not configured. Set ERC8004_MNEMONIC or ERC8004_PRIVATE_KEY", file=sys.stderr)
        sys.exit(1)
    
    w3 = get_web3(chain)
    contract = get_contract(w3)
    
    tag1 = bytes32_from_string(args.tag1 or "")
    tag2 = bytes32_from_string(args.tag2 or "")
    
    # Build transaction
    try:
        nonce = w3.eth.get_transaction_count(wallet.address)
        gas_price = w3.eth.gas_price
        
        tx = contract.functions.giveFeedback(
            agent, score, tag1, tag2
        ).build_transaction({
            'from': wallet.address,
            'nonce': nonce,
            'gasPrice': gas_price,
            'chainId': CHAINS[chain]['id'],
        })
        
        # Estimate gas
        tx['gas'] = w3.eth.estimate_gas(tx)
        
        # Sign and send
        signed = wallet.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        # Wait for receipt
        print("Submitting feedback...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            gas_cost = receipt['gasUsed'] * gas_price
            print(f"✓ Feedback submitted!")
            print(f"  Agent: {agent}")
            print(f"  Score: {score}")
            if args.tag1 or args.tag2:
                tags = [t for t in [args.tag1, args.tag2] if t]
                print(f"  Tags: {', '.join(tags)}")
            print(f"  Tx: {tx_hash.hex()}")
            print(f"  Gas: {format_wei(gas_cost, CHAINS[chain]['symbol'])}")
        else:
            print(f"✗ Transaction failed: {tx_hash.hex()}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error submitting feedback: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_my_rep(args):
    """Check your own agent's reputation across all chains."""
    agent = validate_address(args.agent_id)
    
    print(f"Reputation for: {agent}\n")
    
    for chain_name, chain_info in CHAINS.items():
        try:
            w3 = get_web3(chain_name)
            contract = get_contract(w3)
            total_score, feedback_count, avg_score = contract.functions.getSummary(agent).call()
            
            if feedback_count > 0:
                print(f"  {chain_info['name']}: {avg_score} ({feedback_count} reviews)")
            else:
                print(f"  {chain_info['name']}: No feedback")
        except Exception as e:
            error_str = str(e).lower()
            if 'revert' in error_str or 'execution' in error_str:
                print(f"  {chain_info['name']}: No feedback")
            else:
                print(f"  {chain_info['name']}: Error - {e}")


def cmd_clients(args):
    """List all addresses that have given feedback to an agent."""
    agent = validate_address(args.agent_id)
    chain = args.chain or DEFAULT_CHAIN
    
    w3 = get_web3(chain)
    contract = get_contract(w3)
    
    try:
        clients = contract.functions.getClients(agent).call()
        
        if not clients:
            print(f"No clients have given feedback to {agent}")
            return
        
        print(f"Clients who gave feedback to {agent}:")
        print(f"Chain: {chain}\n")
        
        for i, client in enumerate(clients, 1):
            print(f"  {i}. {client}")
        
        print(f"\nTotal: {len(clients)} client(s)")
        
    except Exception as e:
        print(f"Error querying clients: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_revoke(args):
    """Revoke feedback you previously gave."""
    agent = validate_address(args.agent_id)
    index = int(args.feedback_index)
    chain = args.chain or DEFAULT_CHAIN
    
    wallet = get_wallet()
    if not wallet:
        print("Error: Wallet not configured. Set ERC8004_MNEMONIC or ERC8004_PRIVATE_KEY", file=sys.stderr)
        sys.exit(1)
    
    w3 = get_web3(chain)
    contract = get_contract(w3)
    
    try:
        # Verify the feedback exists and belongs to us
        feedback = contract.functions.readFeedback(agent, index).call()
        reviewer = feedback[0]
        
        if reviewer.lower() != wallet.address.lower():
            print(f"Error: Feedback at index {index} was not given by your wallet", file=sys.stderr)
            print(f"  Reviewer: {reviewer}")
            print(f"  Your address: {wallet.address}")
            sys.exit(1)
        
        if feedback[5]:  # revoked
            print(f"Feedback at index {index} is already revoked")
            return
        
        # Build and send revoke transaction
        nonce = w3.eth.get_transaction_count(wallet.address)
        gas_price = w3.eth.gas_price
        
        tx = contract.functions.revokeFeedback(agent, index).build_transaction({
            'from': wallet.address,
            'nonce': nonce,
            'gasPrice': gas_price,
            'chainId': CHAINS[chain]['id'],
        })
        
        tx['gas'] = w3.eth.estimate_gas(tx)
        
        signed = wallet.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        print("Revoking feedback...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            gas_cost = receipt['gasUsed'] * gas_price
            print(f"✓ Feedback revoked!")
            print(f"  Agent: {agent}")
            print(f"  Index: {index}")
            print(f"  Tx: {tx_hash.hex()}")
            print(f"  Gas: {format_wei(gas_cost, CHAINS[chain]['symbol'])}")
        else:
            print(f"✗ Transaction failed: {tx_hash.hex()}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error revoking feedback: {e}", file=sys.stderr)
        sys.exit(1)


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="ERC-8004 Reputation Registry CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s lookup 0x1234...abcd
  %(prog)s give 0x1234...abcd 85 --tag1 reliable --tag2 fast
  %(prog)s my-rep 0xYourAddress
  %(prog)s clients 0x1234...abcd
  %(prog)s revoke 0x1234...abcd 3
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # lookup
    p_lookup = subparsers.add_parser("lookup", help="Look up an agent's reputation")
    p_lookup.add_argument("agent_id", help="Agent address (0x...)")
    p_lookup.add_argument("--chain", choices=CHAINS.keys(), help=f"Chain (default: {DEFAULT_CHAIN})")
    p_lookup.set_defaults(func=cmd_lookup)
    
    # give
    p_give = subparsers.add_parser("give", help="Give feedback to an agent")
    p_give.add_argument("agent_id", help="Agent address (0x...)")
    p_give.add_argument("score", type=int, help="Score (0-100)")
    p_give.add_argument("--tag1", help="First tag (optional)")
    p_give.add_argument("--tag2", help="Second tag (optional)")
    p_give.add_argument("--chain", choices=CHAINS.keys(), help=f"Chain (default: {DEFAULT_CHAIN})")
    p_give.set_defaults(func=cmd_give)
    
    # my-rep
    p_myrep = subparsers.add_parser("my-rep", help="Check your own reputation")
    p_myrep.add_argument("agent_id", help="Your agent address (0x...)")
    p_myrep.set_defaults(func=cmd_my_rep)
    
    # clients
    p_clients = subparsers.add_parser("clients", help="List clients who gave feedback")
    p_clients.add_argument("agent_id", help="Agent address (0x...)")
    p_clients.add_argument("--chain", choices=CHAINS.keys(), help=f"Chain (default: {DEFAULT_CHAIN})")
    p_clients.set_defaults(func=cmd_clients)
    
    # revoke
    p_revoke = subparsers.add_parser("revoke", help="Revoke your feedback")
    p_revoke.add_argument("agent_id", help="Agent address (0x...)")
    p_revoke.add_argument("feedback_index", type=int, help="Feedback index to revoke")
    p_revoke.add_argument("--chain", choices=CHAINS.keys(), help=f"Chain (default: {DEFAULT_CHAIN})")
    p_revoke.set_defaults(func=cmd_revoke)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
