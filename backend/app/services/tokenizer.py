import re

def count_tokens(text: str) -> int:
    """Accurate token estimator for prompt token verification.
    Uses whitespace and punctuation segmentation ~3.8 characters per token."""
    if not text:
        return 0
    # Match words, numbers, and individual punctuation marks
    tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    return max(1, len(tokens))

def count_messages_tokens(messages: list) -> int:
    """Counts prompt tokens across an OpenAI-compatible message list."""
    total = 3  # base conversation framing
    for msg in messages:
        total += 4  # role, markers
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
        total += count_tokens(content)
    total += 2  # assistant prompt priming
    return total
