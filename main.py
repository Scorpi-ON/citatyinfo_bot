import os


for path in os.listdir():
    if path.endswith('.session'):
        import src.bot
        break
else:
    import src.first_auth
