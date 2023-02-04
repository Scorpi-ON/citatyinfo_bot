from functools import cached_property
import typing

from bs4 import BeautifulSoup, Tag
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from quote import Quote
import utils


class ShortQuote(Quote):
    MAX_LENGTH = 250

    def __init__(self, article_tag: Tag):
        self._content_tag = article_tag.div
        self._quote_tag = article_tag
        self.id, self.type
        del self._quote_tag

    @property
    def _rating(self) -> None:
        return None

    @property
    def _series(self) -> None:
        return None

    @property
    def text(self) -> str:
        return self._content_tag.div.text.strip()

    @property
    def header(self) -> str:
        match self.type:
            case Quote.TYPES.pritcha:
                return f'Притча «{self.header}»'
            case Quote.TYPES.po:
                for taxonomy_elem in self.taxonomy:
                    if taxonomy_elem.title == 'Фольклор':
                        return taxonomy_elem.plain_text
            case Quote.TYPES.quote:
                authors = source = None
                for taxonomy_elem in self.taxonomy:
                    match taxonomy_elem.title:
                        case 'Эпизод' | 'Цитируемые персонажи':
                            continue
                        case 'Автор' | 'Исполнители':
                            authors = taxonomy_elem.plain_text
                            if authors == 'неизвестен':
                                authors = 'Неизвестный автор'
                        case 'Песня':
                            source = taxonomy_elem.plain_text
                        case _:
                            source = f'{taxonomy_elem.title.lower()} «{taxonomy_elem.plain_text}»'
                if authors and source:
                    return f'{authors} — {source}'
                elif source:
                    return f'{source[0].upper()}{source[1:]}'
                elif authors:
                    return authors
                else:
                    return 'Неизвестный автор'

    def __str__(self) -> str:
        text = utils.normalize(
            f'**[{self.header}]({self.url})**\n{self.text}'
        )
        return utils.cut(text, ShortQuote.MAX_LENGTH)


class QuotesPage:
    def __init__(self, html_page: str):
        soup = BeautifulSoup(html_page, 'lxml')
        self.header = soup.h1.text
        self._page_tag = soup.main.div
        self.__quotes_rel_links = []

    @property
    def quotes(self) -> typing.Generator[ShortQuote, None, None]:
        for article_tag in self._page_tag.find_all('article'):
            short_quote = ShortQuote(article_tag)
            self.__quotes_rel_links.append(short_quote.rel_link)
            yield short_quote

    @property
    def pagination(self) -> typing.List[int]:
        pagination = []
        pagination_tag = self._page_tag.findChild(
            'div', class_='pagination', recursive=False)
        if not pagination_tag:
            pagination_tag = self._page_tag.div.findChild(
                'div', class_='pagination', recursive=False)
        if pagination_tag:
            for page in pagination_tag \
                    .find('ul', class_='pager-regular') \
                    .findChildren(recursive=False):
                if page.a:
                    if 'pager-previous' in page['class'] or 'pager-next' in page['class']:
                        pass
                    else:
                        pagination.append(int(page.a.text))
        return pagination

    @cached_property
    def __string_representation(self) -> str:
        text = f'**{self.header}**\n'
        for num, quote in enumerate(self.quotes, 1):
            text += f'\n**{num}.** {quote}\n'
        return utils.normalize(text)

    def __str__(self):
        return self.__string_representation

    @cached_property
    def keyboard(self) -> InlineKeyboardMarkup | None:
        quote_rows = [[], []]
        number_of_quotes = len(self.__quotes_rel_links)
        if number_of_quotes % 2 == 0:
            number_of_quotes = number_of_quotes // 2
        else:
            number_of_quotes = number_of_quotes // 2 + 1
        for num, rel_link in enumerate(self.__quotes_rel_links, 1):
            quote_rows[0 if num <= number_of_quotes else 1] \
                .append(InlineKeyboardButton(str(num), rel_link))
        page_row = [
            InlineKeyboardButton(f'стр. {page}', f'p{page - 1}')
            for page in self.pagination
        ]
        rows = [*quote_rows, page_row]
        if any(rows):
            return InlineKeyboardMarkup(rows)
