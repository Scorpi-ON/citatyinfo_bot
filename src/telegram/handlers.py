import asyncio

from pyrogram import Client
from pyrogram.types import Message, CallbackQuery, InlineQuery

from ..parser import Quote, QuotePage, utils
from ..parser import const as parser_const
from .formatters.quote import TgQuoteFormatter
from .formatters.quote_page import TgPageFormatter
from .utils import http_request, refresh_page_quotes
from . import const as tg_const


async def help_(_, msg: Message):
    """
    Сообщение с описанием функционала бота.
    """
    await msg.reply(
        text='Справка с полным описанием функционала бота пока не написана.'
        ' Но вы можете начать его использование с команд.'
        ' Также можно искать цитаты по гиперссылкам из сообщений'
        ' и по собственным текстовым запросам.'
    )


async def single_quote(_, msg: Message):
    """
    Единичная цитата по команде ``/random`` (случайная цитата)
    или по ссылке, присланной в сообщении.
    """
    if msg.command:
        url = parser_const.RANDOM_URL
    else:
        url = msg.text
    if response := await http_request(url, msg):
        quote = TgQuoteFormatter(Quote(html_page=response.text))
        if quote.media:
            quote_image_msg_group = await msg.reply_media_group(
                media=quote.media,
                disable_notification=True
            )
            msg = quote_image_msg_group[0]
        await msg.reply(
            text=quote.text,
            quote=bool(quote.media),
            reply_markup=quote.reply_markup,
            disable_web_page_preview=True
        )


async def quote_by_callback(app: Client, query: CallbackQuery):
    """
    Цитата по относительной ссылке из коллбэка.
    """
    if response := await http_request(
            url=parser_const.BASE_URL % query.data,
            callback_query=query
    ):
        await query.answer(cache_time=tg_const.RESULT_CACHE_TIME)
        quote = TgQuoteFormatter(Quote(html_page=response.text))
        reply_to_message_id = None
        if quote.media:
            messages = await app.send_media_group(
                chat_id=query.from_user.id,
                media=quote.media,
                disable_notification=True
            )
            reply_to_message_id = messages[0].id
        await app.send_message(
            chat_id=query.from_user.id,
            text=quote.text,
            reply_markup=quote.reply_markup,
            reply_to_message_id=reply_to_message_id,
            disable_web_page_preview=True
        )


async def multiple_quotes(_, msg: Message):
    """
    Список цитат по соответствующим им командам,
    ссылке на страницу с цитатами или поисковому запросу.
    """
    if msg.via_bot and msg.via_bot.is_self:
        return
    if msg.command:
        url = tg_const.MULTIPLE_COMMAND_LINKS[msg.command[0]]
    elif parser_const.COMMON_URL_PATTERN.match(msg.text):
        url = msg.text
    else:
        url = parser_const.SEARCH_URL % msg.text
    if response := await http_request(
            url=url,
            message=msg
    ):
        quote_page = TgPageFormatter(QuotePage(html_page=response.text, url=url))
        await msg.reply(
            text=quote_page.text,
            quote=True,
            reply_markup=quote_page.reply_markup,
            disable_web_page_preview=True
        )


async def multiple_quotes_inline(_, query: InlineQuery):
    """
    Список цитат по соответствующим им командам,
    ссылке на страницу с цитатами или поисковому запросу.
    """
    if not query.query:
        return
    if query.query in tg_const.MULTIPLE_COMMAND_LINKS:
        url = tg_const.MULTIPLE_COMMAND_LINKS[query.query]
    elif parser_const.COMMON_URL_PATTERN.match(query.query):
        url = query.query
    else:
        url = parser_const.SEARCH_URL % query.query
    page = query.offset or None
    if response := await http_request(
            url=url,
            page=page if page != '0' else None
    ):
        raw_quote_page = QuotePage(html_page=response.text, url=url)
        await refresh_page_quotes(raw_quote_page, page)
        quote_page = TgPageFormatter(raw_quote_page)
        await query.answer(
            results=quote_page.inline_results(query.query),
            next_offset=quote_page.inline_offset(page)
        )


async def turn_page(_, query: CallbackQuery):
    """
    Переключение страницы в сообщении с набором цитат.
    """
    page = query.data[1:]
    request_msg = query.message.reply_to_message
    request = request_msg.text
    if not request:
        await query.message.edit(
            'Невозможно переключить страницу: сообщение с запросом, по'
            ' которому она должна формироваться, удалено. Отправьте этот'
            ' запрос снова и повторите попытку.'
        )
        return
    if request[1:] in tg_const.MULTIPLE_COMMAND_LINKS:      # В сообщениях, полученных не по фильтру
        url = tg_const.MULTIPLE_COMMAND_LINKS[request[1:]]  # команд, не работает метод command
    elif parser_const.COMMON_URL_PATTERN.match(request):
        url = request
    else:
        url = parser_const.SEARCH_URL % request
    if response := await http_request(
            url=url,
            callback_query=query,
            page=page if page != '0' else None
    ):
        quote_page = TgPageFormatter(QuotePage(html_page=response.text, url=url))
        await query.message.edit(
            text=quote_page.text,
            reply_markup=quote_page.reply_markup,
            disable_web_page_preview=True
        )


async def original(_, query: CallbackQuery):
    """
    Оригинал цитаты на иностранном языке
    по ID из коллбэка.
    """
    quote_id = query.data[1:]
    if response := await http_request(
            url=parser_const.AJAX_URL % quote_id,
            callback_query=query
    ):
        original_text = Quote.get_original_text(
            html_page=response.json()[1]['data']
        )
        original_text = utils.trim_text(original_text, tg_const.MAX_CALLBACK_ANSWER_LENGTH)
        await query.answer(
            text=original_text,
            show_alert=True,
            cache_time=tg_const.RESULT_CACHE_TIME
        )


async def explanation(_, query: CallbackQuery):
    """
    Пояснение к цитате в виде уведомления
    по относительной ссылке из коллбэка.
    """
    rel_link = query.data[1:]
    if response := await http_request(
            url=parser_const.BASE_URL % rel_link,
            callback_query=query
    ):
        quote = Quote(html_page=response.text)
        explanation_text = utils.trim_text(quote.explanation, tg_const.MAX_CALLBACK_ANSWER_LENGTH)
        await query.answer(
            text=explanation_text,
            show_alert=True,
            cache_time=tg_const.RESULT_CACHE_TIME
        )


async def callback_echo(_, query: CallbackQuery):
    """
    Вывод данных коллбэка в виде уведомления.
    """
    text = query.data
    if isinstance(text, bytes):
        text = text.decode(parser_const.STR_ENCODING)
    await query.answer(
        text=text,
        show_alert=True,
        cache_time=tg_const.RESULT_CACHE_TIME
    )
