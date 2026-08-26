def test_chat_importable():
    import chat
    assert hasattr(chat, "main")
    assert hasattr(chat, "jalankan_task")

def test_help_lengkap():
    import chat
    for cmd in ("/stats", "/memory", "/reset", "/help", "/exit"):
        assert cmd in chat.HELP
