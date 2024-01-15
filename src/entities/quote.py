import typing
import enum
import copy
import functools

from selectolax.lexbor import LexborHTMLParser, LexborNode

from src import utils, const
from src.entities.taxonomy_elem import TaxonomyElem


class QuoteTypes(enum.Enum):
    """
    Типы цитат, использующиеся в ссылках на них.
    Examples:
        ``quote``: обычная цитата — https://citaty.info/quote/35045

        ``po``: пословица / поговорка — https://citaty.info/po/247673
        (подходят также цитаты вида https://citaty.info/proverb/110707, если вместо ``proverb`` использовать ``po``)

        ``pritcha``: притча — https://citaty.info/pritcha/121736
    """
    quote = 0
    po = 1
    pritcha = 2


class Quote:
    SHORT_TEXT_LENGTH = 250
    TAXONOMY_TEMPLATES = {
        'Автор цитаты': TaxonomyElem('©️', 'Автор'),
        'Автор неизвестен': TaxonomyElem('©️', 'Автор').add_content('неизвестен'),
        'Цитируемый персонаж': TaxonomyElem('💬', 'Цитируемые персонажи'),
        'Исполнитель': TaxonomyElem('🎤', 'Исполнители'),
        'Цитата из книги': TaxonomyElem('📖', 'Произведение'),
        'Цитата из фильма': TaxonomyElem('🎬', 'Фильм'),
        'Цитата из мультфильма': TaxonomyElem('🧸', 'Мультфильм'),
        'Цитата из сериала': TaxonomyElem('🍿', 'Сериал'),
        'Цитата из телешоу': TaxonomyElem('📺', 'Телешоу'),
        'Цитата из спектакля': TaxonomyElem('🎭', 'Спектакль'),
        'Цитата из игры': TaxonomyElem('🎮', 'Игра'),
        'Цитата из комикса': TaxonomyElem('🦸🏻\u200d♂️', 'Комикс'),
        'Цитата из аниме': TaxonomyElem('🥷🏻', 'Аниме'),
        'Песня': TaxonomyElem('🎵', 'Песня'),
        'Самиздат': TaxonomyElem('✍🏻', 'Самиздат'),
        'Притча': TaxonomyElem('☯', 'Притча'),
        'Фольклор': TaxonomyElem('📜', 'Фольклор'),
        'Эпизод': TaxonomyElem('📀', 'Эпизод'),
        'КВН': TaxonomyElem('😂', 'Команда КВН')
    }

    @classmethod
    def get_taxonomy_elem(cls, key: str) -> TaxonomyElem:
        return copy.deepcopy(cls.TAXONOMY_TEMPLATES[key])

    @classmethod
    def get_original_text(cls, html_page: str) -> str:
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
            self._parable_header = tree.css_first('h1').text()
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
    def images(self) -> typing.List[str] | None:
        images = []
        for img_tag in self._quote_tag.css('img'):
            images.append(img_tag.attributes['src'])
        return images

    @functools.cached_property
    def explanation(self) -> str | None:
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
        if self.type is QuoteTypes.pritcha:
            return utils.optimize_text(
                self._parable_header or self._quote_tag.css_first('h2').text()
            )

    @property
    def _series(self) -> TaxonomyElem | None:
        """
        Дополнительные метаданные для сериалов (сезон, серия, эпизод и т. д.)
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

    @property
    def _taxonomy(self) -> typing.Generator[TaxonomyElem, None, None]:
        if self._common_taxonomy_elem:
            yield self._common_taxonomy_elem
        if self.type is QuoteTypes.pritcha:
            taxonomy_elem = self.get_taxonomy_elem('Притча')
            yield taxonomy_elem.add_content(self.parable_header)
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
                    yield taxonomy_elem
            if series := self._series:
                yield series

    @functools.cached_property
    def header(self) -> str | None:
        match self.type:
            case QuoteTypes.pritcha:
                return f'Притча «{self.parable_header}»'
            case QuoteTypes.po:
                for taxonomy_elem in self._taxonomy:
                    if taxonomy_elem.title == 'Фольклор':
                        return taxonomy_elem.plain_text
            case QuoteTypes.quote:
                authors = source = characters = None
                for taxonomy_elem in self._taxonomy:
                    match taxonomy_elem.title:
                        case 'Эпизод':
                            continue
                        case 'Цитируемые персонажи':
                            characters = 'Персонаж'
                            if taxonomy_elem.count > 1:
                                characters += 'и'
                            characters += f' {taxonomy_elem.plain_text}'
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
                elif characters:
                    return characters
                else:
                    return None

    @property
    def _topics(self) -> typing.Generator[dict, None, None]:
        topics = []
        topic_tag = self._quote_tag.css_first(f'div.node__topics')
        if topic_tag:
            topics.extend(topic_tag.css('a'))                        # Основные теги, приведённые под цитатой
        topics.extend(self._quote_tag.css('div.field-name-body a'))  # Теги, встроенные в текст цитаты
        for num, topic in enumerate(topics):
            topic = {'text': topic.text().lower()
                                         .replace(' ', '_')
                                         .replace(',_', ' #'),
                     'url': topic.attributes['href']}  # Преобразуем теги в удобные для использования словари
            if topic['url'] not in topics:             # и отсеиваем, если такие ссылки уже есть
                yield topic
            topics[num] = topic['url']                 # (именно ссылки, а не текст, т. к. он может отличаться)

    @property
    def _text(self) -> str | typing.Tuple[str, str]:
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
            case (text_tag, ):
                return utils.optimize_text(text_tag.text())
            case original_tag, translation_tag:
                return utils.optimize_text(original_tag.text()), \
                    utils.optimize_text(translation_tag.text())
            case _:
                raise ValueError('Отсутствует текст цитаты')

    @functools.cached_property
    def short_text(self) -> str:
        text = self._text
        if isinstance(text, tuple):
            text = f'{text[0]}\n\n{text[1]}'
        return utils.trim_text(text, Quote.SHORT_TEXT_LENGTH)

    @functools.cached_property
    def short_formatted_text(self):
        text = self.short_text
        if self.header:
            text = f'**{self.header}**\n{text}'
        return utils.trim_text(text, Quote.SHORT_TEXT_LENGTH)

    @functools.cached_property
    def formatted_text(self) -> str:
        text = self._text
        topics = tuple(self._topics)
        if isinstance(text, tuple):
            text = f'**Оригинал:**\n{text[0]}\n\n**Перевод:**\n{text[1]}'
        text += '\n\n'
        for taxonomy_elem in self._taxonomy:
            text += f'{taxonomy_elem}\n'
        text += '\n'
        for topic in topics:
            text += f'[#{topic["text"]}]({topic["url"]}) '
        return text

    @functools.cached_property
    def keyboard_data(self) -> typing.List[typing.List[typing.Dict[str, str]]]:
        row = []
        if explanation := self.explanation:
            explanation = explanation.encode(const.STR_ENCODING)
            if len(explanation) > const.MAX_CALLBACK_DATA_LENGTH:
                explanation = f'e{self.rel_link}'
            row.append({'text': '🔮 Пояснение', 'callback_data': explanation})
        if self.has_original:
            row.append({'text': '🇬🇧 Оригинал', 'callback_data': f'o{self.id}'})
        row.append({'text': '🔗 Открыть', 'url': const.BASE_URL % self.rel_link})
        return [row]
