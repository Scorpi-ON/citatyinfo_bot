import typing

from selectolax.lexbor import LexborHTMLParser

from src.entities.quote import Quote
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
    def quotes(self) -> typing.Generator[Quote, None, None]:
        no_results = self._page_tag.css_first('h2')
        if no_results or no_results.text() == 'Ваш поиск не принёс результатов':
            yield
        for quote_tag in self._page_tag.css('article'):
            quote = Quote(article_tag=quote_tag)
            self._quote_rel_links.append(quote.rel_link)
            yield quote

    @property
    def _extra_result_groups(self) -> typing.Dict[str, typing.List[typing.Dict[str, str]]]:
        groups = {}
        for group in self._page_tag.css('div.search__results > div.search__results__group'):
            content = [
                {'text': link.text(), 'url': link.attributes['href']}
                for link in group.css('a')
            ]
            groups[group.css_first('div.search__results__group__title').text()] = content
        return groups

    @property
    def _pagination(self) -> typing.Generator[int, None, None]:
        pagination_tag = self._page_tag.css_first('div.pagination ul.pager-regular')
        if pagination_tag:
            for page in pagination_tag.css('a'):
                if page_text := page.text():
                    yield int(page_text)

    @property
    def formatted_text(self) -> str:
        quotes = tuple(self.quotes)
        extra_links = self._extra_result_groups
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

    @property
    def keyboard(self) -> typing.List[typing.List[typing.Dict[str, str]]]:
        quote_rows = [[], []]
        number_of_quotes = len(self._quote_rel_links)
        number_of_quotes_per_row = number_of_quotes
        if number_of_quotes > const.MAX_ROW_BUTTON_COUNT:
            number_of_quotes_per_row = number_of_quotes // 2 + number_of_quotes % 2
        for num, rel_link in enumerate(self._quote_rel_links, 1):
            row_num = 0 if num <= number_of_quotes_per_row else 1
            quote_rows[row_num].append(
                {'text': str(num), 'callback_data': rel_link}
            )
        pagination_row = [
            {'text': f'стр. {page}', 'callback_data': f'p{page - 1}'}
            for page in self._pagination
        ]
        return [*quote_rows, pagination_row]
