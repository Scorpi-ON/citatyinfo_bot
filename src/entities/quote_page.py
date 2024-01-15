import functools
import typing

from selectolax.lexbor import LexborHTMLParser

from src.entities.quote import Quote
from src import utils, const


class QuotePage:
    def __init__(self, html_page: str):
        self._tree = LexborHTMLParser(html_page)
        self._page_tag = self._tree.css_first('main > div')

    @functools.cached_property
    def header(self):
        return utils.optimize_text(
            self._tree.css_first('h1').text()
        )

    @functools.cached_property
    def quotes(self) -> typing.List[Quote]:
        no_results = self._page_tag.css_first('h2')
        if no_results and no_results.text() == 'Ваш поиск не принес результатов':
            return []
        return [
            Quote(article_tag=quote_tag)
            for quote_tag in self._page_tag.css('article')
        ]

    @property
    def _extra_result_groups(self) -> typing.Dict[str, typing.List[typing.Dict[str, str]]]:
        groups = {}
        for group in self._page_tag.css('div.search__results > div.search__results__group'):
            content = [
                {'text': utils.optimize_text(link_tag.text()),
                 'url': link_tag.attributes['href']}
                for link_tag in group.css('a')
            ]
            group_title = utils.optimize_text(
                group.css_first('div.search__results__group__title').text()
            )
            groups[group_title] = content
        return groups

    @property
    def _pagination(self) -> typing.Generator[int, None, None]:
        pagination_tag = self._page_tag.css_first('div.pagination ul.pager-regular')
        if pagination_tag:
            for page in pagination_tag.css('a'):
                if page_text := page.text():
                    yield int(page_text)

    @functools.cached_property
    def formatted_text(self) -> str:
        extra_links = self._extra_result_groups
        if not self.quotes and not extra_links:
            return 'Ничего не найдено по этому запросу. 🤷🏻‍♂️'
        text = f'**{self.header}**\n'
        for num, quote in enumerate(self.quotes, 1):
            text += f'\n**{num}.** {quote.short_formatted_text}\n'
        for group in extra_links:
            text += f'\n**{group}**'
            for link in extra_links[group]:
                text += f'\n[{link["text"]}]({link["url"]})'
            text += '\n'
        text = text.replace('** **', ' ')
        return text

    @functools.cached_property
    def keyboard_data(self) -> typing.List[typing.List[typing.Dict[str, str]]] | None:
        if not self.quotes:
            return None
        quote_rows = ([], [])
        number_of_quotes = len(self.quotes)
        number_of_quotes_per_row = number_of_quotes
        if number_of_quotes > const.MAX_ROW_BUTTON_COUNT:
            number_of_quotes_per_row = number_of_quotes // 2 + number_of_quotes % 2
        for num, quote in enumerate(self.quotes, 1):
            row_num = 0 if num <= number_of_quotes_per_row else 1
            quote_rows[row_num].append(
                {'text': str(num), 'callback_data': quote.rel_link}
            )
        pagination_row = [
            {'text': f'стр. {page}', 'callback_data': f'p{page - 1}'}
            for page in self._pagination
        ]
        return [*quote_rows, pagination_row]
