from app.services.tokenizer import count_tokens, count_messages_tokens

def test_count_tokens():
    assert count_tokens("") == 0
    assert count_tokens("Hello") == 1
    assert count_tokens("Hello, world! 123") >= 4

def test_count_messages_tokens():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum physics."}
    ]
    tokens = count_messages_tokens(messages)
    assert tokens > 10
