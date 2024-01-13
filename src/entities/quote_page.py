from functools import cached_property
import typing

from selectolax.lexbor import LexborHTMLParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.entities.short_quote import ShortQuote
from src import utils, const


class QuotePage:
    def __init__(self, html_page: str):
        self._tree = LexborHTMLParser(html_page)
        self._page_tag = self._tree.css_first('main > div')
        self._quote_rel_links = []

    @property
    def header(self):
        return self._tree.css_first('h1').text()

    @property
    def quotes(self) -> typing.Generator[ShortQuote, None, None]:
        no_results = self._page_tag.css_first('h2')
        if not no_results or no_results.text() != 'Ваш поиск не принёс результатов':
            for quote_tag in self._page_tag.css('article'):
                short_quote = ShortQuote(quote_tag)
                self._quote_rel_links.append(short_quote.rel_link)
                yield short_quote

    @property
    def extra_result_groups(self) -> typing.Dict[str, typing.List[typing.Dict[str, str]]]:
        groups = {}
        for group in self._page_tag.css('div.search__results > div.search__results__group'):
            content = [
                {'text': link.text(), 'url': link.attributes['href']}
                for link in group.css('a')
            ]
            groups[group.css_first('div.search__results__group__title').text()] = content
        return groups

    @property
    def pagination(self) -> typing.List[int]:
        pagination = []
        pagination_tag = self._page_tag.css_first('div.pagination ul.pager-regular')
        if pagination_tag:
            for page in pagination_tag.css('a'):
                if page_text := page.text():
                    pagination.append(int(page_text))
        return pagination

    @cached_property
    def _string_representation(self) -> str:
        quotes = tuple(self.quotes)
        extra_links = self.extra_result_groups
        if not self._quote_rel_links and not extra_links:
            return 'Ничего не найдено по этому запросу. 🤷🏻‍♂️'
        text = f'**{self.header}**\n'
        for num, quote in enumerate(quotes, 1):
            text += f'\n**{num}.** {quote}\n'
        for group in extra_links:
            text += f'\n**{group}**'
            for link in extra_links[group]:
                text += f'\n[{link["text"]}]({link["url"]})'
            text += '\n'
        return utils.optimize_text(text)

    def __str__(self):
        return self._string_representation

    @cached_property
    def keyboard(self) -> InlineKeyboardMarkup | None:
        quote_rows = [[], []]
        number_of_quotes = len(self._quote_rel_links)
        number_of_quotes_per_row = number_of_quotes
        if number_of_quotes > const.MAX_ROW_BUTTON_COUNT:
            number_of_quotes_per_row = number_of_quotes // 2 + number_of_quotes % 2
        for num, rel_link in enumerate(self._quote_rel_links, 1):
            quote_rows[0 if num <= number_of_quotes_per_row else 1].append(
                InlineKeyboardButton(str(num), rel_link)
            )
        pagination_row = [
            InlineKeyboardButton(f'стр. {page}', f'p{page - 1}')
            for page in self.pagination
        ]
        rows = [*quote_rows, pagination_row]
        if any(rows):
            return InlineKeyboardMarkup(rows)
