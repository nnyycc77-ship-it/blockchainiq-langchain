"""LangChain tool for the Blockchain IQ x402 market brief.

The tool calls Blockchain IQ's brief endpoint (GET /api/x402/v1/brief)
through the x402 protocol on Base and returns the brief JSON together
with the response proof (payer, network, transaction hash) decoded
from the PAYMENT-RESPONSE header.

The x402 flow is handled by the official x402 Python SDK: the first
request answers HTTP 402, the SDK signs a USDC
transferWithAuthorization (EIP-3009, gasless for the caller) with the
wallet in AGENT_PRIVATE_KEY, and retries with the authorization
attached. A limit in the client caps any single call at the brief
amount.

Use a dedicated wallet holding a small USDC balance on Base. Never a
main wallet.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Optional, Type

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

BRIEF_URL = "https://www.blockchainiq.co/api/x402/v1/brief"
BRIEF_PRICE_USD = 0.01


class BlockchainIQBriefInput(BaseModel):
    """The brief endpoint takes no parameters; the input is empty by design."""

    pass


def fetch_brief(private_key: str, max_amount_usd: float = BRIEF_PRICE_USD) -> dict:
    """Call the brief endpoint and return data plus the response proof."""
    import requests
    from eth_account import Account
    from x402 import x402ClientSync
    from x402.http.clients.requests import wrapRequestsWithPayment
    from x402.http.utils import decode_payment_response_header
    from x402.mechanisms.evm.exact.client import ExactEvmScheme
    from x402.mechanisms.evm.signers import EthAccountSigner

    account = Account.from_key(private_key)
    client = x402ClientSync()
    client.register("eip155:*", ExactEvmScheme(EthAccountSigner(account)))
    client.set_spend_controls({"max_amount_per_payment": max_amount_usd})

    session = wrapRequestsWithPayment(requests.Session(), client)
    # The retry waits on settlement; allow it real time.
    response = session.get(BRIEF_URL, timeout=280)
    response.raise_for_status()
    body = response.json()
    raw_header = response.headers.get("payment-response")
    settlement = decode_payment_response_header(raw_header) if raw_header else None
    return {
        "data": body.get("data", body),
        "settlement": (
            {
                "success": settlement.success,
                "payer": settlement.payer,
                "network": settlement.network,
                "transaction": settlement.transaction,
                "amount": settlement.amount,
            }
            if settlement is not None
            else None
        ),
    }


class BlockchainIQBriefTool(BaseTool):
    """Fetch the Blockchain IQ crypto market brief via x402.

    Returns BTC, ETH, SOL and XRP prices with 24h, 7d and 30d moves,
    scheduled macro and crypto events in the next 48 hours, and short
    risk flags, plus the on chain response proof.
    """

    name: str = "blockchainiq_market_brief"
    description: str = (
        "Fetch the Blockchain IQ crypto market brief over x402 on Base: "
        "BTC, ETH, SOL and XRP prices with 24h, 7d and 30d moves and "
        "rank, scheduled macro and crypto events in the next 48 hours, "
        "and short risk flags. Use as the opening call of a trading, "
        "portfolio or research loop. Returns the brief JSON plus the "
        "response proof."
    )
    args_schema: Type[BaseModel] = BlockchainIQBriefInput

    private_key_env: str = Field(default="AGENT_PRIVATE_KEY")
    max_amount_usd: float = Field(default=BRIEF_PRICE_USD)

    def _private_key(self) -> str:
        key = os.environ.get(self.private_key_env, "")
        if not key:
            raise ValueError(
                f"{self.private_key_env} is not set. Set it to the private key "
                "of a dedicated wallet holding a small USDC balance on Base."
            )
        return key

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        result = fetch_brief(self._private_key(), self.max_amount_usd)
        return json.dumps(result, indent=2)

    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return await asyncio.to_thread(self._run, None)


__all__ = ["BlockchainIQBriefTool", "BlockchainIQBriefInput", "fetch_brief", "BRIEF_URL"]
