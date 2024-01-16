import typing
import copy
import functools

from selectolax.lexbor import LexborHTMLParser

from .. import utils, const
from _quote import Quote
from _taxonomy_elem import TaxonomyElem


class QuotePage:
    TAXONOMY_TEMPLATES = {
        'man': TaxonomyElem('©️', 'Автор'),
        'character': TaxonomyElem('💬', 'Цитируемые персонажи'),
        'music': TaxonomyElem('🎤', 'Исполнители'),
        'book': TaxonomyElem('📖', 'Произведение'),
        'movie': TaxonomyElem('🎬', 'Фильм'),
        'cartoon': TaxonomyElem('🧸', 'Мультфильм'),
        'series': TaxonomyElem('🍿', 'Сериал'),
        'tv': TaxonomyElem('📺', 'Телешоу'),
        'theater': TaxonomyElem('🎭', 'Спектакль'),
        'game': TaxonomyElem('🎮', 'Игра'),
        'comics': TaxonomyElem('🦸🏻\u200d♂️', 'Комикс'),
        'anime': TaxonomyElem('🥷🏻', 'Аниме'),
        'samizdat': TaxonomyElem('✍🏻', 'Самиздат'),
        'po': TaxonomyElem('📜', 'Фольклор'),
        'kvn': TaxonomyElem('😂', 'Команда КВН')
    }

    @classmethod
    def get_taxonomy_elem(cls, key: str) -> TaxonomyElem:
        return copy.deepcopy(cls.TAXONOMY_TEMPLATES[key])

    def __init__(self, html_page: str, url: str):
        self.url = url
        self._tree = LexborHTMLParser(html_page)
        self._page_tag = self._tree.css_first('main > div')

    @functools.cached_property
    def header(self):
        return utils.optimize_text(
            self._tree.css_first('h1').text()
        )

    @functools.cached_property
    def common_taxonomy_elem(self) -> TaxonomyElem | None:
        common_taxonomy_elem = None
        if self._tree.css_matches('div#breadcrumbs') and self.url and self.url.startswith(const.BASE_URL % ''):
            for key in QuotePage.TAXONOMY_TEMPLATES:
                if self.url.startswith(const.BASE_URL % key):
                    common_taxonomy_elem = self.get_taxonomy_elem(key)
                    if key == 'music' and '/' in self.url.removeprefix(const.BASE_URL % key):
                        common_taxonomy_elem = TaxonomyElem('🎵', 'Песня')
                        taxonomy_elem_content_title = self.header.rsplit(' — ', 1)[1]
                    else:
                        taxonomy_elem_content_title = self.header.rsplit(' — ', 1)[0]
                    common_taxonomy_elem.add_content(taxonomy_elem_content_title, self.url)
        return common_taxonomy_elem

    @functools.cached_property
    def quotes(self) -> typing.List[Quote]:
        no_results = self._page_tag.css_first('h2')
        if no_results and no_results.text() == 'Ваш поиск не принес результатов':
            return []
        return [
            Quote(
                article_tag=article_tag,
                common_taxonomy_elem=self.common_taxonomy_elem
            ) for article_tag in self._page_tag.css('article')
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
            return const.NOTHING_FOUND_MSG
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
