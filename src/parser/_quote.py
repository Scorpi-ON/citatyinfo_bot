import json
import functools

from selectolax.lexbor import LexborHTMLParser, LexborNode

from ._quote_types import QuoteTypes
from ._taxonomy_elem import TaxonomyElem
from ._topic import Topic
from . import const, utils


class Quote:
    """
    Единичная цитата.
    """
    with open('src/parser/taxonomy_templates_by_tags.json', encoding=const.STR_ENCODING) as f:
        raw_taxonomy_templates: list = json.load(f)
    TAXONOMY_TEMPLATES = {}
    for template in raw_taxonomy_templates:
        TAXONOMY_TEMPLATES[template['page_title']] = TaxonomyElem(
            emoji=template['emoji'],
            title=template['replacement'],
            content=template['content']
        )

    @classmethod
    def get_taxonomy_elem(cls, key: str) -> TaxonomyElem:
        """
        Копия элемента таксономии для редактирования.
        """
        return cls.TAXONOMY_TEMPLATES[key].copy()

    @classmethod
    def get_original_text(cls, html_page: str) -> str:
        """
        Оригинал цитаты, если есть.
        """
        tree = LexborHTMLParser(html_page)
        return utils.optimize_text(tree.text())

    def __init__(
            self,
            html_page: str = None,
            article_tag: LexborNode = None,
            common_taxonomy_elem: TaxonomyElem = None
    ):
        assert html_page and not (article_tag or common_taxonomy_elem) \
               or article_tag and not html_page
        self._parable_header = None
        self._common_taxonomy_elem = common_taxonomy_elem
        if html_page:
            tree = LexborHTMLParser(html_page).body
            article_tag = tree.css_first('article')
            self._parable_header = tree.css_first('h1')
            if self._parable_header is not None:  # Без проверки ломаются случайные цитаты
                self._parable_header = self._parable_header.text()
        self._quote_with_meta_tag = article_tag
        self._quote_tag = article_tag.css_first('div.node__content')

    @functools.cached_property
    def id(self) -> str:
        """
        ID цитаты. Нужен для формирования прямой ссылки.
        Examples:
            ``35045``: https://citaty.info/quote/35045
        """
        return self._quote_with_meta_tag.id.removeprefix('node-')

    @functools.cached_property
    def type(self) -> QuoteTypes:
        """
        Тип цитаты. Нужен для формирования прямой ссылки.
        """
        quote_class = self._quote_with_meta_tag.attributes['class']
        if 'node-po' in quote_class:
            return QuoteTypes.po
        elif 'node-pritcha' in quote_class:
            return QuoteTypes.pritcha
        else:
            return QuoteTypes.quote

    @functools.cached_property
    def rel_link(self) -> str:
        """
        Относительная ссылка на цитату. Нужна для формирования
        полноценной ссылки в последующем.
        Examples:
            ``quote/35045``: https://citaty.info/quote/35045
        """
        return f'{self.type.name}/{self.id}'

    @functools.cached_property
    def image_links(self) -> list[str]:
        """
        Ссылки на картинки в цитате.
        """
        images = []
        for img_tag in self._quote_tag.css('img'):
            images.append(img_tag.attributes['src'])
        return images

    @functools.cached_property
    def explanation(self) -> str | None:
        """
        Пояснение к цитате, если есть
        """
        explanation_tag = self._quote_tag.css_first('div.field-name-field-description div.field-item')
        if explanation_tag is not None:
            explanation_text = explanation_tag.text()
            return utils.optimize_text(explanation_text)

    @functools.cached_property
    def has_original(self) -> bool:
        """
        Имеет ли цитата оригинальную версию на иностранном языке.
        """
        return self._quote_tag.css_matches('div.quote__original')

    @functools.cached_property
    def parable_header(self) -> str | None:
        """
        Название притчи, если это притча.
        """
        if self.type is QuoteTypes.pritcha:
            return utils.optimize_text(
                self._parable_header or self._quote_tag.css_first('h2').text()
            )

    @property
    def _series(self) -> TaxonomyElem | None:
        """
        Дополнительные метаданные для сериала (сезон, серия, эпизод и т. д.), если это сериал
        """
        if self.type is QuoteTypes.quote:
            series_metadata_tag = self._quote_tag.css_first('div.node__series')
            if series_metadata_tag is not None:
                taxonomy_elem = self.get_taxonomy_elem('Эпизод')
                for series_tag in series_metadata_tag.css('div.field-item'):
                    if link_tag := series_tag.css_first('a'):
                        taxonomy_elem.add_content(link_tag.text(), link_tag.attributes['href'])
                    else:
                        taxonomy_elem.add_content(series_tag.text())
                return taxonomy_elem

    @functools.cached_property
    def taxonomy(self) -> list[TaxonomyElem]:
        """
        Все элементы таксономии цитаты.
        """
        taxonomy_elems = []
        if self._common_taxonomy_elem:
            taxonomy_elems.append(self._common_taxonomy_elem)
        if self.type is QuoteTypes.pritcha:
            taxonomy_elem = self.get_taxonomy_elem('Притча')
            taxonomy_elems.append(taxonomy_elem.add_content(self.parable_header))
        else:
            taxonomy_tags = self._quote_with_meta_tag.css('div.node__content > div.field-type-taxonomy-term-reference')
            for tag in taxonomy_tags:
                if link_tag := tag.css_first('a'):  # Бывает, что находятся пустые div'ы без ссылок
                    key = link_tag.attributes.get('title')
                    if not key:
                        if '/kvn/' in link_tag.attributes['href']:
                            key = 'КВН'
                        elif link_tag.attributes['href'] == '/other':
                            key = 'Автор неизвестен'
                        else:
                            key = 'Фольклор'
                    taxonomy_elem = self.get_taxonomy_elem(key)
                    if key != 'Автор неизвестен':
                        for link_tag in tag.css('a'):
                            taxonomy_elem.add_content(link_tag.text(), link_tag.attributes['href'])
                    taxonomy_elems.append(taxonomy_elem)
            if series := self._series:
                taxonomy_elems.append(series)
        return taxonomy_elems

    @functools.cached_property
    def header(self) -> str | None:
        """
        Заголовок цитаты для отображения в списке коротких цитат.
        """
        match self.type:
            case QuoteTypes.pritcha:
                return f'Притча «{self.parable_header}»'
            case QuoteTypes.po:
                for taxonomy_elem in self.taxonomy:
                    if taxonomy_elem.title == 'Фольклор':
                        return taxonomy_elem.plain_content
            case QuoteTypes.quote:
                authors = source = characters = None
                for taxonomy_elem in self.taxonomy:
                    match taxonomy_elem.title:
                        case 'Эпизод':
                            continue
                        case 'Цитируемые персонажи':
                            characters = 'Персонаж'
                            if taxonomy_elem.count > 1:
                                characters += 'и'
                            characters += f' {taxonomy_elem.plain_content}'
                        case 'Автор' | 'Исполнители':
                            authors = taxonomy_elem.plain_content
                            if authors == 'неизвестен':
                                authors = 'Неизвестный автор'
                        case 'Песня':
                            source = taxonomy_elem.plain_content
                        case _:
                            source = f'{taxonomy_elem.title.lower()} «{taxonomy_elem.plain_content}»'
                if authors and source:
                    return f'{authors} — {source}'
                elif source:
                    return f'{source[0].upper()}{source[1:]}'
                elif authors:
                    return authors
                elif characters:
                    return characters
                else:
                    return None

    @functools.cached_property
    def topics(self) -> list[Topic]:
        """
        Хэштеги (темы) цитаты.
        """
        topics, used_topic_urls = [], []
        topic_tag = self._quote_tag.css_first(f'div.node__topics')
        if topic_tag:
            used_topic_urls.extend(topic_tag.css('a'))                        # Основные теги, приведённые под цитатой
        used_topic_urls.extend(self._quote_tag.css('div.field-name-body a'))  # Теги, встроенные в текст цитаты
        for num, topic in enumerate(used_topic_urls):
            topic = Topic(topic.text(), topic.attributes['href'])  # Преобразуем теги в объекты класса
            if topic.url not in used_topic_urls:                   # и отсеиваем, если такие ссылки уже есть
                topics.append(topic)                               # (именно ссылки, а не текст,
            used_topic_urls[num] = topic.url                       # т. к. он может отличаться)
        return topics

    @functools.cached_property
    def text(self) -> str | tuple[str, str]:
        """
        Простой текст цитаты без дополнительных модификаций, заголовков, ссылок и тегов.
        Returns:
            *непосредственно текст*

            *оригинал и перевод*: для некоторых цитат на иностранном языке текст делится на эти две части
        Raises:
            ValueError: в случае отсутствия текста
        """
        translation_tags = self._quote_tag.css('div.field-name-body')
        match translation_tags:
            case (text_tag,):
                return utils.optimize_text(text_tag.text())
            case original_tag, translation_tag:
                return utils.optimize_text(original_tag.text()), \
                    utils.optimize_text(translation_tag.text())
            case _:
                raise ValueError('Отсутствует текст цитаты')
