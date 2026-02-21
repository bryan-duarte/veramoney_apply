import re


CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1f\x7f-\x9f]")
DEFAULT_MAX_LOG_LENGTH = 100


def sanitize_for_log(value: str, max_length: int = DEFAULT_MAX_LOG_LENGTH) -> str:
    if not value:
        return ""

    sanitized = CONTROL_CHAR_PATTERN.sub(
        lambda m: f"\\x{ord(m.group()):02x}",
        value,
    )

    is_too_long = len(sanitized) > max_length
    if is_too_long:
        sanitized = f"{sanitized[:max_length]}..."

    return sanitized
