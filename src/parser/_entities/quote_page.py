import functools

from selectolax.lexbor import LexborHTMLParser

from .. import utils
from .quote import Quote


class QuotePage:
    """
    Страница с цитатами.
    """
    def __init__(self, html_page: str):
        self._tree = LexborHTMLParser(html_page)
        self._page_tag = self._tree.css_first('main > div')

    @functools.cached_property
    def header(self) -> str:
        """
        Заголовок страницы с цитатами.
        """
        return utils.optimize_text(
            self._tree.css_first('h1').text()
        )

    @functools.cached_property
    def quotes(self) -> list[Quote]:
        """
        Список цитат, находящихся на странице.
        """
        no_results = self._page_tag.css_first('h2')
        if no_results and no_results.text() == 'Ваш поиск не принес результатов':
            return []
        return [
            Quote(
                article_tag=article_tag
            ) for article_tag in self._page_tag.css('article')
        ]

    @functools.cached_property
    def non_quote_search_results(self) -> dict[str, list[dict[str, str]]]:
        """
        Словарь результатов поиска, являющихся не цитатами, а ссылками на категории цитат, название которых
        совпадает с запросом. Например, по запросу «любовь»: авторы с именем Любовь,
        произведения, в названиях которых фигурирует слово «любовь» и так далее.
        """
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
    def pagination(self) -> list[int]:
        """
        Номера страниц пагинации, доступные с данной страницы.
        """
        pages = []
        pagination_tag = self._page_tag.css_first('div.pagination ul.pager-regular')
        if pagination_tag:
            for page in pagination_tag.css('a'):
                if page_text := page.text():
                    pages.append(int(page_text))
        return pages
