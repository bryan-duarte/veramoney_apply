import re
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator


class StockInput(BaseModel):
    TICKER_MIN_LENGTH: ClassVar[int] = 1
    TICKER_MAX_LENGTH: ClassVar[int] = 5
    TICKER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Z]+$")

    ticker: str = Field(
        min_length=1,
        max_length=5,
        description="Stock ticker symbol (e.g., AAPL, GOOGL)",
    )

    @field_validator("ticker")
    @classmethod
    def normalize_and_validate_ticker(cls, value: str) -> str:
        normalized_ticker = value.strip().upper()
        is_valid_ticker_format = bool(cls.TICKER_PATTERN.match(normalized_ticker))
        if not is_valid_ticker_format:
            raise ValueError("Ticker must contain only letters A-Z")
        return normalized_ticker


class StockOutput(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    price: float = Field(description="Current stock price in USD")
    currency: str = Field(default="USD", description="Currency code")
    timestamp: str = Field(description="ISO 8601 timestamp of the trade")
    change: str = Field(
        description="Price change from previous close with sign (e.g., '+2.34', '-1.50')"
    )
    change_percent: str = Field(
        description="Percentage change from previous close with sign (e.g., '+1.32%', '-0.85%')"
    )
