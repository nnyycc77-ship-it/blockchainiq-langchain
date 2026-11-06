"""Run the Blockchain IQ brief tool once and print the settlement proof.

Setup:
    pip install -e .
    export AGENT_PRIVATE_KEY=0x...   # dedicated wallet, a little USDC on Base

Run:
    python examples/run_brief.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from blockchainiq_langchain import BlockchainIQBriefTool


def main() -> None:
    tool = BlockchainIQBriefTool()
    result = json.loads(tool.invoke({}))
    print(json.dumps(result["data"], indent=2))
    proof = result["settlement"]
    print("\nSettlement proof:")
    print(f"  success:     {proof['success']}")
    print(f"  payer:       {proof['payer']}")
    print(f"  network:     {proof['network']}")
    print(f"  transaction: {proof['transaction']}")


if __name__ == "__main__":
    main()
