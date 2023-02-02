import os

import dotenv
import uvloop
import httpx
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
import aiofiles

import const
import utils
from quote import Quote
from quotes_page import QuotesPage


CONF = dotenv.dotenv_values()
CALLBACK_CACHE_TIME = 120
ERROR_CALLBACK_CACHE_TIME = 30

uvloop.install()
app = Client('TestBot')
http_client = httpx.AsyncClient()


@app.on_message(filters.command(['start', 'help']))
async def help(client: Client, message: Message):
    await message.reply('Инструкция в процессе написания…')


@app.on_message(filters.command('random'))
async def random(client: Client, message: Message):
    response = await http_client.get(const.RANDOM_URL)
    if response.status_code == 200:
        quote = Quote(response.text)
        if quote.images:
            messages = await message.reply_media_group(quote.images)
            message = messages[0]
        await message.reply(
            str(quote), quote=bool(quote.images),
            reply_markup=quote.keyboard,
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )


@app.on_message(filters.command(list(const.MULTIPLE_QUOTES_COMMANDS)))
async def category_commands(client: Client, message: Message):
    response = await http_client.get(
        const.MULTIPLE_QUOTES_COMMANDS[message.command[0]]
    )
    if response.status_code == 200:
        quotes_page = QuotesPage(response.text)
        await message.reply(
            str(quotes_page),
            reply_markup=quotes_page.keyboard,
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
        if quote.images:
            messages = await message.reply_media_group(quote.images)
            message = messages[0]
        await message.reply(
            str(quote), quote=bool(quote.images),
            reply_markup=quote.keyboard,
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )


@app.on_message()
async def quote_search(client: Client, message: Message):
    response = await http_client.get(const.SEARCH_URL % message.text)
    if response.status_code == 200:
        quotes_page = QuotesPage(response.text)
        await message.reply(
            str(quotes_page),
            reply_markup=quotes_page.keyboard,
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
            cache_time=CALLBACK_CACHE_TIME
        )
    else:
        await callback_query.answer(
            'Ошибка подключения к сайту! Повторите попытку позже.',
            cache_time=ERROR_CALLBACK_CACHE_TIME
        )


@app.on_callback_query(filters.regex(const.EXPLANATION_CALLBACK_PATTERN))
async def explanation_request(client: Client, callback_query: CallbackQuery):
    rel_link = callback_query.data[1:]
    response = await http_client.get(const.BASE_URL % rel_link)
    if response.status_code == 200:
        quote = Quote(response.text)
        await callback_query.answer(
            quote.explanation,
            show_alert=True,
            cache_time=CALLBACK_CACHE_TIME
        )
    else:
        await callback_query.answer(
            'Ошибка подключения к сайту! Повторите попытку позже.',
            cache_time=ERROR_CALLBACK_CACHE_TIME
        )


@app.on_callback_query(filters.regex(const.GET_QUOTE_CALLBACK_PATTERN))
async def quote_by_callback(client: Client, callback_query: CallbackQuery):
    response = await http_client.get(const.BASE_URL % callback_query.data)
    if response.status_code == 200:
        quote = Quote(response.text)
        if quote.images:
            messages = await app.send_media_group(
                callback_query.from_user.id,
                quote.images
            )
            await messages[0].reply(
                str(quote), quote=bool(quote.images),
                reply_markup=quote.keyboard,
                disable_web_page_preview=True
            )
        else:
            await app.send_message(
                callback_query.from_user.id, str(quote),
                reply_markup=quote.keyboard,
                disable_web_page_preview=True
            )
    else:
        await app.send_message(
            callback_query.from_user.id,
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )
    await callback_query.answer(cache_time=CALLBACK_CACHE_TIME)


@app.on_callback_query()
async def callback_echo(client: Client, callback_query: CallbackQuery):
    await callback_query.answer(
        callback_query.data,
        show_alert=True,
        cache_time=CALLBACK_CACHE_TIME
    )


app.run()
