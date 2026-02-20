REQUEST_TIMEOUT_SECONDS = 120.0
STARTER_LABEL_MAX_LENGTH = 60
HTTP_STATUS_RATE_LIMITED = 429
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2

SUGGESTED_PROMPTS = [
    "What's the weather like in Montevideo, Uruguay?",
    "What is the current stock price of Apple (AAPL)?",
    "How is the weather in New York and what's the MSFT stock price?",
    "Compare the stock performance of TSLA and NVDA",
]

ERROR_MESSAGE_UNAUTHORIZED = "Unable to connect to the service. Please contact support."
ERROR_MESSAGE_RATE_LIMITED = "Please wait a moment before sending another message."
ERROR_MESSAGE_SERVER_ERROR = "Something went wrong. Please try again."
ERROR_MESSAGE_TIMEOUT = "Request timed out. Please try again."
ERROR_MESSAGE_NETWORK = "Connecting to service..."
ERROR_MESSAGE_GENERIC = "An unexpected error occurred. Please try again."
