#!/usr/bin/env python3
"""Seed the database with synthetic tool definitions (get_card_info, get_cards)."""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bootstrap import create_clients
from app.models import (
    InputSchema,
    OutputSchema,
    PropertyDefinition,
    ResponseSchema,
    ServiceEndpoints,
    Tool,
    ToolMetadata,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock base URL for synthetic tools (httpbin echoes requests)
MOCK_BASE = "https://httpbin.org"


def get_cards_tool() -> Tool:
    """List user's cards."""
    return Tool(
        name="get_cards",
        version="1.0.0",
        title="Get Cards",
        description="Retrieve a list of all cards associated with the user account.",
        metadata=ToolMetadata(
            category="cards",
            tags=["cards", "banking", "accounts"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "accountId": PropertyDefinition(
                    type="string",
                    description="Account ID to fetch cards for",
                ),
                "includeInactive": PropertyDefinition(
                    type="boolean",
                    description="Include inactive/closed cards",
                    default=False,
                ),
            },
            required=["accountId"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "cards": {"type": "array", "description": "List of card objects"},
                    "totalCount": {"type": "integer", "description": "Number of cards"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def get_card_info_tool() -> Tool:
    """Get detailed info for a specific card."""
    return Tool(
        name="get_card_info",
        version="1.0.0",
        title="Get Card Info",
        description="Retrieve detailed information for a specific card by ID.",
        metadata=ToolMetadata(
            category="cards",
            tags=["cards", "banking", "card-details"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "cardId": PropertyDefinition(
                    type="string",
                    description="Unique card identifier",
                ),
                "includeTransactions": PropertyDefinition(
                    type="boolean",
                    description="Include recent transactions",
                    default=False,
                ),
            },
            required=["cardId"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "cardId": {"type": "string", "description": "Card identifier"},
                    "lastFour": {"type": "string", "description": "Last 4 digits"},
                    "status": {"type": "string", "description": "Active, Inactive, etc."},
                    "transactions": {"type": "array", "description": "Recent transactions if requested"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def get_accounts_tool() -> Tool:
    """List user's accounts."""
    return Tool(
        name="get_accounts",
        version="1.0.0",
        title="Get Accounts",
        description="Retrieve a list of all accounts (checking, savings, etc.) for the user.",
        metadata=ToolMetadata(
            category="accounts",
            tags=["accounts", "banking", "balance"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "userId": PropertyDefinition(
                    type="string",
                    description="User identifier",
                ),
                "accountTypes": PropertyDefinition(
                    type="string",
                    description="Comma-separated account types to filter (e.g. checking,savings)",
                ),
            },
            required=["userId"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "accounts": {"type": "array", "description": "List of account objects"},
                    "totalCount": {"type": "integer", "description": "Number of accounts"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def get_account_balance_tool() -> Tool:
    """Get balance for a specific account."""
    return Tool(
        name="get_account_balance",
        version="1.0.0",
        title="Get Account Balance",
        description="Retrieve the current balance for a specific account.",
        metadata=ToolMetadata(
            category="accounts",
            tags=["accounts", "banking", "balance"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "accountId": PropertyDefinition(
                    type="string",
                    description="Account identifier",
                ),
                "includePending": PropertyDefinition(
                    type="boolean",
                    description="Include pending transactions in balance",
                    default=True,
                ),
            },
            required=["accountId"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "accountId": {"type": "string", "description": "Account ID"},
                    "availableBalance": {"type": "number", "description": "Available balance"},
                    "currentBalance": {"type": "number", "description": "Current balance"},
                    "currency": {"type": "string", "description": "Currency code"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def get_transactions_tool() -> Tool:
    """Fetch transaction history for an account."""
    return Tool(
        name="get_transactions",
        version="1.0.0",
        title="Get Transactions",
        description="Retrieve transaction history for an account with optional date range and filters.",
        metadata=ToolMetadata(
            category="transactions",
            tags=["transactions", "banking", "history"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "accountId": PropertyDefinition(
                    type="string",
                    description="Account identifier",
                ),
                "startDate": PropertyDefinition(
                    type="string",
                    format="date",
                    description="Start date (YYYY-MM-DD)",
                ),
                "endDate": PropertyDefinition(
                    type="string",
                    format="date",
                    description="End date (YYYY-MM-DD)",
                ),
                "limit": PropertyDefinition(
                    type="integer",
                    description="Max number of transactions to return",
                    default=50,
                ),
            },
            required=["accountId"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "transactions": {"type": "array", "description": "List of transactions"},
                    "totalCount": {"type": "integer", "description": "Total matching transactions"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def transfer_funds_tool() -> Tool:
    """Transfer funds between accounts."""
    return Tool(
        name="transfer_funds",
        version="1.0.0",
        title="Transfer Funds",
        description="Transfer funds from one account to another.",
        metadata=ToolMetadata(
            category="transactions",
            tags=["transfer", "banking", "payments"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "fromAccountId": PropertyDefinition(
                    type="string",
                    description="Source account ID",
                ),
                "toAccountId": PropertyDefinition(
                    type="string",
                    description="Destination account ID",
                ),
                "amount": PropertyDefinition(
                    type="number",
                    description="Amount to transfer",
                ),
                "currency": PropertyDefinition(
                    type="string",
                    description="Currency code (e.g. USD)",
                    default="USD",
                ),
                "memo": PropertyDefinition(
                    type="string",
                    description="Optional memo for the transfer",
                ),
            },
            required=["fromAccountId", "toAccountId", "amount"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "transferId": {"type": "string", "description": "Transfer reference ID"},
                    "status": {"type": "string", "description": "Pending, Completed, Failed"},
                    "completedAt": {"type": "string", "description": "Completion timestamp"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def make_payment_tool() -> Tool:
    """Make a bill payment or external payment."""
    return Tool(
        name="make_payment",
        version="1.0.0",
        title="Make Payment",
        description="Initiate a bill payment or payment to an external payee.",
        metadata=ToolMetadata(
            category="payments",
            tags=["payments", "bills", "banking"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "accountId": PropertyDefinition(
                    type="string",
                    description="Account to debit",
                ),
                "payeeId": PropertyDefinition(
                    type="string",
                    description="Payee or biller identifier",
                ),
                "amount": PropertyDefinition(
                    type="number",
                    description="Payment amount",
                ),
                "scheduledDate": PropertyDefinition(
                    type="string",
                    format="date",
                    description="Date to process payment (YYYY-MM-DD)",
                ),
            },
            required=["accountId", "payeeId", "amount"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "paymentId": {"type": "string", "description": "Payment reference"},
                    "status": {"type": "string", "description": "Pending, Scheduled, Completed"},
                    "scheduledFor": {"type": "string", "description": "Scheduled date"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def get_user_profile_tool() -> Tool:
    """Get the current user's profile."""
    return Tool(
        name="get_user_profile",
        version="1.0.0",
        title="Get User Profile",
        description="Retrieve profile information for the authenticated user.",
        metadata=ToolMetadata(
            category="user",
            tags=["user", "profile", "settings"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "includePreferences": PropertyDefinition(
                    type="boolean",
                    description="Include notification and display preferences",
                    default=True,
                ),
            },
            required=[],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "userId": {"type": "string", "description": "User ID"},
                    "email": {"type": "string", "description": "Email address"},
                    "name": {"type": "string", "description": "Display name"},
                    "preferences": {"type": "object", "description": "User preferences"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def send_notification_tool() -> Tool:
    """Send a notification to the user."""
    return Tool(
        name="send_notification",
        version="1.0.0",
        title="Send Notification",
        description="Send a notification (email, push, or in-app) to the user.",
        metadata=ToolMetadata(
            category="notifications",
            tags=["notifications", "alerts", "messaging"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "userId": PropertyDefinition(
                    type="string",
                    description="Target user ID",
                ),
                "channel": PropertyDefinition(
                    type="string",
                    enum=["email", "push", "sms", "in_app"],
                    description="Notification channel",
                ),
                "subject": PropertyDefinition(
                    type="string",
                    description="Subject or title",
                ),
                "body": PropertyDefinition(
                    type="string",
                    description="Notification body content",
                ),
                "priority": PropertyDefinition(
                    type="string",
                    enum=["low", "normal", "high", "urgent"],
                    default="normal",
                ),
            },
            required=["userId", "channel", "subject", "body"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "notificationId": {"type": "string", "description": "Notification ID"},
                    "status": {"type": "string", "description": "Sent, Queued, Failed"},
                    "deliveredAt": {"type": "string", "description": "Delivery timestamp"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def get_spending_summary_tool() -> Tool:
    """Get spending analytics summary."""
    return Tool(
        name="get_spending_summary",
        version="1.0.0",
        title="Get Spending Summary",
        description="Retrieve aggregated spending summary by category for a time period.",
        metadata=ToolMetadata(
            category="analytics",
            tags=["analytics", "spending", "reports"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "accountId": PropertyDefinition(
                    type="string",
                    description="Account ID (or 'all' for all accounts)",
                ),
                "period": PropertyDefinition(
                    type="string",
                    enum=["week", "month", "quarter", "year"],
                    description="Time period",
                    default="month",
                ),
            },
            required=["accountId"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "byCategory": {"type": "object", "description": "Spending by category"},
                    "total": {"type": "number", "description": "Total spending"},
                    "period": {"type": "string", "description": "Period covered"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def search_merchants_tool() -> Tool:
    """Search for merchants by name or category."""
    return Tool(
        name="search_merchants",
        version="1.0.0",
        title="Search Merchants",
        description="Search for merchants in the directory by name, category, or location.",
        metadata=ToolMetadata(
            category="directory",
            tags=["merchants", "search", "directory"],
        ),
        inputSchema=InputSchema(
            type="object",
            properties={
                "query": PropertyDefinition(
                    type="string",
                    description="Search query (merchant name, category, etc.)",
                ),
                "category": PropertyDefinition(
                    type="string",
                    description="Filter by merchant category",
                ),
                "limit": PropertyDefinition(
                    type="integer",
                    description="Max results to return",
                    default=20,
                ),
            },
            required=["query"],
        ),
        outputSchema=OutputSchema(
            contentType="application/json",
            schema=ResponseSchema(
                type="object",
                properties={
                    "merchants": {"type": "array", "description": "List of matching merchants"},
                    "totalCount": {"type": "integer", "description": "Total matches"},
                },
            ),
        ),
        endpoints=ServiceEndpoints(
            baseUrl=f"{MOCK_BASE}/post",
            healthEndpoint="/get",
            customEndpoints={"invoke": "/post"},
        ),
    )


def all_seed_tools() -> list[Tool]:
    """Return all seed tools in definition order."""
    return [
        get_cards_tool(),
        get_card_info_tool(),
        get_accounts_tool(),
        get_account_balance_tool(),
        get_transactions_tool(),
        transfer_funds_tool(),
        make_payment_tool(),
        get_user_profile_tool(),
        send_notification_tool(),
        get_spending_summary_tool(),
        search_merchants_tool(),
    ]


async def main() -> None:
    tools = all_seed_tools()
    async with create_clients() as (_, __, registry):
        for tool in tools:
            try:
                created = await registry.register(tool)
                logger.info("Registered: %s", created.name)
            except Exception as e:
                logger.exception("Failed to register %s: %s", tool.name, e)
                raise
    logger.info("Seeded %d tools", len(tools))


if __name__ == "__main__":
    asyncio.run(main())
