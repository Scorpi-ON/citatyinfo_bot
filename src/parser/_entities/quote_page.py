import json
import functools

from selectolax.lexbor import LexborHTMLParser

from .. import const, utils
from .quote import Quote
from .taxonomy_elem import TaxonomyElem


class QuotePage:
    """
    Страница с цитатами.
    """
    with open('src/parser/data/taxonomy_templates_by_links.json', encoding=const.STR_ENCODING) as f:
        raw_taxonomy_templates: list = json.load(f)
    TAXONOMY_TEMPLATES = {}
    for template in raw_taxonomy_templates:
        TAXONOMY_TEMPLATES[template['rel_link']] = TaxonomyElem(
            emoji=template['emoji'],
            title=template['title']
        )

    @classmethod
    def get_taxonomy_elem(cls, key: str) -> TaxonomyElem:
        """
        Копия элемента таксономии для редактирования.
        """
        return cls.TAXONOMY_TEMPLATES[key].copy()

    def __init__(self, html_page: str, url: str):
        self.rel_link = url.removeprefix(const.BASE_URL % '')
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
    def common_taxonomy_elem(self) -> TaxonomyElem | None:
        """
        Общий для всей страницы элемент таксономии, формирующийся по ссылке на эту страницу.
        Нужен по той причине, что на странице, к примеру, цитаты из определённого фильма элементы таксономии
        со ссылкой на этот фильм будут отсутствовать во избежание дублирования на сайте.
        Для правильного же вычленения единичных цитат со страницы его нужно формировать и добавлять
        к цитатам самостоятельно.
        """
        common_taxonomy_elem = None
        if self._tree.css_matches('div#breadcrumbs') and self.rel_link:
            for key in QuotePage.TAXONOMY_TEMPLATES:
                if self.rel_link.startswith(key):
                    common_taxonomy_elem = self.get_taxonomy_elem(key)
                    if key == 'music' and '/' in self.rel_link.removeprefix(key) \
                            and ' — ' in self.header:
                        common_taxonomy_elem = TaxonomyElem('🎵', 'Песня')
                        taxonomy_elem_content_title = self.header.rsplit(' — ', 1)[1]
                    else:
                        taxonomy_elem_content_title = self.header.rsplit(' — ', 1)[0]
                    common_taxonomy_elem.add_content(taxonomy_elem_content_title, const.BASE_URL % self.rel_link)
        return common_taxonomy_elem

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
                article_tag=article_tag,
                common_taxonomy_elem=self.common_taxonomy_elem
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
