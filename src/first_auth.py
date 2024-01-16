from pyrogram import Client
from dotenv import dotenv_values

"""
Перед запуском создайте файл ".env" со следующим содержанием:
name=SESSION_NAME
api_id=YOUR_API_ID
api_hash=YOUR_API_HASH
bot_token=YOUR_BOT_TOKEN

Измените значения констант в файле и название сессии ниже на ваши.
"""


app = Client(**dotenv_values())
app.run()
