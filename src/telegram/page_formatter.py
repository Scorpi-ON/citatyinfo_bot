from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, \
    InlineQueryResultArticle, InputTextMessageContent

import const as tg_const
from ..parser import Quote, QuotePage, utils
from quote_formatter import TgQuoteFormatter


class TgPageFormatter:
    def __init__(self, quote_page: QuotePage):
        self._page = quote_page

    @staticmethod
    def quote_short_text(quote: Quote):
        text = quote.text
        if isinstance(text, tuple):
            text = f'{text[0]}\n\n{text[1]}'
        if quote.header:
            text = f'**{quote.header}**\n{text}'
        return utils.trim_text(text, tg_const.QUOTE_SHORT_TEXT_LENGTH)

    @property
    def text(self) -> str:
        extra_links = self._page.non_quote_search_results
        if not self._page.quotes and not extra_links:
            return tg_const.NOTHING_FOUND_MSG
        text = f'**{self._page.header}**\n'
        for num, quote in enumerate(self._page.quotes, 1):
            text += f'\n**{num}.** {self.quote_short_text(quote)}\n'
        for group in extra_links:
            text += f'\n**{group}**'
            for link in extra_links[group]:
                text += f'\n[{link["text"]}]({link["url"]})'
            text += '\n'
        text = text.replace('** **', ' ')
        return text

    @property
    def reply_markup(self) -> InlineKeyboardMarkup | None:
        if not self._page.quotes:
            return None
        quote_rows = ([], [])
        number_of_quotes = len(self._page.quotes)
        number_of_quotes_per_row = number_of_quotes
        if number_of_quotes > tg_const.MAX_ROW_BUTTON_COUNT:
            number_of_quotes_per_row = number_of_quotes // 2 + number_of_quotes % 2
        for num, quote in enumerate(self._page.quotes, 1):
            row_num = 0 if num <= number_of_quotes_per_row else 1
            quote_rows[row_num].append(
                {'text': str(num), 'callback_data': quote.rel_link}
            )
        pagination_row = [
            {'text': f'стр. {page}', 'callback_data': f'p{page - 1}'}
            for page in self._page.pagination
        ]
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(**button_data) for button_data in row]
            for row in (*quote_rows, pagination_row)
        ])

    def inline_results(self, query: str) -> list[InlineQueryResultArticle]:
        results = []
        if not self._page.quotes:
            results.append(InlineQueryResultArticle(
                title=query,
                description=tg_const.NOTHING_FOUND_MSG,
                input_message_content=InputTextMessageContent(
                    message_text=f'__{query}__\n\n{tg_const.NOTHING_FOUND_MSG}'
                )
            ))
        else:
            for quote in self._page.quotes:
                formatted_quote = TgQuoteFormatter(quote)
                results.append(InlineQueryResultArticle(
                    title=quote.header or self._page.header,
                    description=self.quote_short_text(quote),
                    input_message_content=InputTextMessageContent(
                        message_text=formatted_quote.text,
                        disable_web_page_preview=True
                    ),
                    thumb_url=quote.image_links[0] if quote.image_links[0] else None,
                    reply_markup=formatted_quote.reply_markup
                ))
        return results

    def inline_offset(self, page: str | None):
        if not self._page.pagination:
            page = None
        elif page:
            page = str(int(page) + 1)
        else:
            page = '1'
        return page
