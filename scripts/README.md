# Scripts

## seed_tools.py

Seeds the database with synthetic tool definitions for demo/testing.

```bash
python scripts/seed_tools.py
```

Creates:
- **get_cards** – Retrieve a list of all cards for an account (requires `accountId`)
- **get_card_info** – Get detailed info for a specific card (requires `cardId`)

Both tools use a mock endpoint (httpbin.org) for synthetic execution. They appear in the UI and MCP tools/list.
