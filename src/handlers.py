from pyrogram import Client
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, \
    InputTextMessageContent, InputMediaPhoto, InlineQuery, InlineQueryResultArticle

from src import const, utils
from src.entities.quote import Quote
from src.entities.quote_page import QuotePage


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
        url = const.RANDOM_URL
    else:
        url = msg.text
    if response := await utils.http_request(url, msg):
        quote = Quote(html_page=response.text)
        if quote.images:
            quote_image_msg_group = await msg.reply_media_group(
                media=[InputMediaPhoto(url) for url in quote.images],
                disable_notification=True
            )
            msg = quote_image_msg_group[0]
        await msg.reply(
            text=quote.formatted_text,
            quote=bool(quote.images),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(**button_data) for button_data in row]
                for row in quote.keyboard_data
            ]),
            disable_web_page_preview=True
        )


async def quote_by_callback(app: Client, query: CallbackQuery):
    """
    Цитата по относительной ссылке из коллбэка.
    """
    if response := await utils.http_request(
            url=const.BASE_URL % query.data,
            callback_query=query
    ):
        await query.answer(cache_time=const.RESULT_CACHE_TIME)
        quote = Quote(html_page=response.text)
        reply_to_message_id = None
        if quote.images:
            messages = await app.send_media_group(
                chat_id=query.from_user.id,
                media=[InputMediaPhoto(url) for url in quote.images],
                disable_notification=True
            )
            reply_to_message_id = messages[0].id
        await app.send_message(
            chat_id=query.from_user.id,
            text=quote.formatted_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(**button_data) for button_data in row]
                for row in quote.keyboard_data
            ]),
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
        url = const.MULTIPLE_QUOTES_COMMANDS[msg.command[0]]
    elif const.COMMON_URL_PATTERN.match(msg.text):
        url = msg.text
    else:
        url = const.SEARCH_URL % msg.text
    if response := await utils.http_request(url, msg):
        quote_page = QuotePage(response.text)
        await msg.reply(
            text=quote_page.formatted_text,
            quote=True,
            reply_markup=None if not quote_page.keyboard_data else InlineKeyboardMarkup([
                [InlineKeyboardButton(**button_data) for button_data in row]
                for row in quote_page.keyboard_data
            ]),
            disable_web_page_preview=True
        )


async def multiple_quotes_inline(_, query: InlineQuery):
    """
    Список цитат по соответствующим им командам,
    ссылке на страницу с цитатами или поисковому запросу.
    """
    if not query.query:
        return
    if query.query in const.MULTIPLE_QUOTES_COMMANDS:
        url = const.MULTIPLE_QUOTES_COMMANDS[query.query]
    elif const.COMMON_URL_PATTERN.match(query.query):
        url = query.query
    else:
        url = const.SEARCH_URL % query.query
    page = query.offset or None
    if response := await utils.http_request(
            url=url,
            page=page if page != '0' else None
    ):
        quote_page = QuotePage(response.text)
        results = []
        for quote in quote_page.quotes:
            results.append(InlineQueryResultArticle(
                title=quote.header or quote_page.header,
                description=quote.short_text,
                input_message_content=InputTextMessageContent(
                    message_text=quote.formatted_text,
                    disable_web_page_preview=True
                ),
                thumb_url=quote.images[0] if quote.images else None,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(**button_data) for button_data in row]
                    for row in quote.keyboard_data
                ])
            ))
        if not quote_page.keyboard_data or not quote_page.keyboard_data[-1]:
            page = None
        elif page:
            page = str(int(page) + 1)
        else:
            page = '1'
        await query.answer(
            results=results,
            next_offset=page
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
    if request[1:] in const.MULTIPLE_QUOTES_COMMANDS:      # в сообщениях, полученных не по фильтру
        url = const.MULTIPLE_QUOTES_COMMANDS[request[1:]]  # команд, не работает метод command
    elif const.COMMON_URL_PATTERN.match(request):
        url = request
    else:
        url = const.SEARCH_URL % request
    if response := await utils.http_request(
            url=url,
            callback_query=query,
            page=page if page != '0' else None
    ):
        quote_page = QuotePage(response.text)
        await query.message.edit(
            text=quote_page.formatted_text,
            reply_markup=None if not quote_page.keyboard_data else InlineKeyboardMarkup([
                [InlineKeyboardButton(**button_data) for button_data in row]
                for row in quote_page.keyboard_data
            ]),
            disable_web_page_preview=True
        )


async def original(_, query: CallbackQuery):
    """
    Оригинал цитаты на иностранном языке
    по ID из коллбэка.
    """
    quote_id = query.data[1:]
    if response := await utils.http_request(
            url=const.AJAX_URL % quote_id,
            callback_query=query
    ):
        original_text = Quote.get_original_text(
            html_page=response.json()[1]['data']
        )
        original_text = utils.trim_text(original_text, const.MAX_CALLBACK_ANSWER_LENGTH)
        await query.answer(
            text=original_text,
            show_alert=True,
            cache_time=const.RESULT_CACHE_TIME
        )


async def explanation(_, query: CallbackQuery):
    """
    Пояснение к цитате в виде уведомления
    по относительной ссылке из коллбэка.
    """
    rel_link = query.data[1:]
    if response := await utils.http_request(url=const.BASE_URL % rel_link, callback_query=query):
        quote = Quote(html_page=response.text)
        explanation_text = utils.trim_text(quote.explanation, const.MAX_CALLBACK_ANSWER_LENGTH)
        await query.answer(
            text=explanation_text,
            show_alert=True,
            cache_time=const.RESULT_CACHE_TIME
        )


async def callback_echo(_, query: CallbackQuery):
    """
    Вывод данных коллбэка в виде уведомления.
    """
    text = query.data
    if isinstance(text, bytes):
        text = text.decode(const.STR_ENCODING)
    await query.answer(
        text=text,
        show_alert=True,
        cache_time=const.RESULT_CACHE_TIME
    )
