import re

from pydantic import BaseModel, Field, field_validator

TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 5
TICKER_PATTERN = re.compile(r"^[A-Z]+$")


class StockInput(BaseModel):
    ticker: str = Field(
        min_length=TICKER_MIN_LENGTH,
        max_length=TICKER_MAX_LENGTH,
        description="Stock ticker symbol (e.g., AAPL, GOOGL)",
    )

    @field_validator("ticker")
    @classmethod
    def normalize_and_validate_ticker(cls, value: str) -> str:
        normalized_ticker = value.strip().upper()
        is_valid_ticker_format = bool(TICKER_PATTERN.match(normalized_ticker))
        if not is_valid_ticker_format:
            raise ValueError("Ticker must contain only letters A-Z")
        return normalized_ticker


class StockOutput(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    price: float = Field(description="Current stock price in USD")
    currency: str = Field(default="USD", description="Currency code")
    timestamp: str = Field(description="ISO 8601 timestamp of the trade")
    change: str = Field(description="Price change from previous close with sign (e.g., '+2.34', '-1.50')")
    change_percent: str = Field(description="Percentage change from previous close with sign (e.g., '+1.32%', '-0.85%')")
