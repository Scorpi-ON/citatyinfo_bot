import os

import dotenv
import uvloop
import httpx
from pyrogram import Client, filters
from pyrogram.types import Message

import const


uvloop.install()
CONF = dotenv.dotenv_values()
app = Client('TestBot')


@app.on_message(filters.command('start'))
async def start(client: Client, message: Message):
    await message.reply('Перед началом использования настоятельно '
                        'рекомендую прочитать инструкцию (/help). 📄')


@app.on_message(filters.command('help'))
async def help(client: Client, message: Message):
    await message.reply('Инструкция в процессе написания…')


@app.on_message(filters.regex(const.BASE_URL_PATTERN))
async def quote(client: Client, message: Message):
    ...


app.run()
