import os

import dotenv
import uvloop
import httpx
from bs4 import BeautifulSoup
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery, InputMediaPhoto
import aiofiles

import const
import utils
from quote import Quote


CONF = dotenv.dotenv_values()
uvloop.install()
app = Client('TestBot')
http_client = httpx.AsyncClient()


@app.on_message(filters.command('start'))
async def start(client: Client, message: Message):
    await message.reply('Перед началом использования настоятельно '
                        'рекомендую прочитать инструкцию (/help). 📄')


@app.on_message(filters.command('help'))
async def help(client: Client, message: Message):
    await message.reply('Инструкция в процессе написания…')


@app.on_message(filters.command('random'))
async def random(client: Client, message: Message):
    response = await http_client.get(const.RANDOM_URL)
    if response.status_code == 200:
        quote = Quote(response.text)
        photos = [InputMediaPhoto(url) for url in quote.images]
        if photos:
            message, = await message.reply_media_group(photos)
        await message.reply(
            str(quote), quote=bool(photos),
            reply_markup=quote.keyboard,
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )


@app.on_message(filters.regex(const.QUOTE_PATTERN))
async def quote_by_link(client: Client, message: Message):
    response = await http_client.get(message.text)
    if response.status_code == 200:
        quote = Quote(response.text)
        photos = [InputMediaPhoto(url) for url in quote.images]
        if photos:
            message, = await message.reply_media_group(photos)
        await message.reply(
            str(quote), quote=bool(photos),
            reply_markup=quote.keyboard,
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )


@app.on_callback_query(filters.regex(const.ORIGINAL_CALLBACK_PATTERN))
async def original_request(client: Client, callback_query: CallbackQuery):
    id, = const.ORIGINAL_CALLBACK_PATTERN.match(callback_query.data).groups()
    response = await http_client.get(const.AJAX_URL % id)
    if response.status_code == 200:
        original_text = BeautifulSoup(response.json()[1]['data'], 'lxml').text
        await callback_query.answer(
            utils.normalize(original_text),
            show_alert=True,
            cache_time=120
        )
    else:
        await callback_query.answer(
            'Ошибка подключения к сайту! Повторите попытку позже.',
            cache_time=30
        )


@app.on_callback_query()
async def callback_echo(client: Client, callback_query: CallbackQuery):
    await callback_query.answer(
        callback_query.data,
        show_alert=True,
        cache_time=120
    )


app.run()
