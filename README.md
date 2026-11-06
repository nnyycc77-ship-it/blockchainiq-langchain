# Blockchain IQ for LangChain

A LangChain tool that fetches the [Blockchain IQ](https://www.blockchainiq.co/agents)
crypto market brief through the x402 protocol on Base. No account and
no API key.

The brief works as the opening call of a trading, portfolio or research
loop: BTC, ETH, SOL and XRP prices with 24h, 7d and 30d moves and rank,
scheduled macro and crypto events in the next 48 hours, and short risk
flags. Refreshed every minute.

## How it works

1. The tool requests `GET /api/x402/v1/brief` with an x402 aware HTTP
   client (the official `x402` Python SDK over requests).
2. The first request answers HTTP 402 with the endpoint terms. The SDK
   signs a USDC `transferWithAuthorization` (EIP-3009) with the wallet
   in `AGENT_PRIVATE_KEY` and retries with the authorization attached.
   The flow is gasless for the caller, and an error response is never
   settled.
3. The completed response carries the brief JSON plus a
   `PAYMENT-RESPONSE` header. The tool decodes it and returns the
   response proof (payer, network, transaction hash) alongside the
   data.

A limit in the client caps the amount of any single call at the brief
amount by default, so a call can never exceed the endpoint terms.

## Install

```bash
pip install git+https://github.com/nnyycc77-ship-it/blockchainiq-langchain
# or, from a clone:
pip install -e .
```

## Configure

Use a dedicated wallet holding a small USDC balance on Base. Never a
main wallet.

```bash
export AGENT_PRIVATE_KEY=0x...
```

## Use it

```python
from blockchainiq_langchain import BlockchainIQBriefTool

tool = BlockchainIQBriefTool()
print(tool.invoke({}))
```

Or run the example:

```bash
python examples/run_brief.py
```

## Live run status

The tool was run against the production endpoint on 2026-11-05. The
first request returns the expected HTTP 402 response, and the tool
signs and sends a valid authorization. As of the last check, the
endpoint does not complete valid x402 requests: no response comes back
and nothing settles on chain, so there is no transaction hash to print
yet. This section will be updated after the first completed request.

- Payer: `0x2D98EE4949F391f957d10588C00D467AB1749fCe`
- Network: `eip155:8453` (Base)

## License

MIT
