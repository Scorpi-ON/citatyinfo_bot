import typing
import enum
import copy
import functools

from selectolax.lexbor import LexborNode
from pyrogram.types import InputMediaPhoto

from src import utils
from src.entities.taxonomy_elem import TaxonomyElem


class QuoteTypes(enum.Enum):
    """
    Типы цитат, использующиеся в ссылках на цитаты.
    Examples:
        ``quote``: обычная цитата — https://citaty.info/quote/35045

        ``po``: пословица / поговорка — https://citaty.info/po/247673
        (подходят также цитаты вида https://citaty.info/proverb/110707, если вместо ``proverb`` использовать ``po``)

        ``pritcha``: притча — https://citaty.info/pritcha/121736
    """
    quote = 0
    po = 1
    pritcha = 2


class BaseQuote:
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

    def __init__(self, article_tag: LexborNode):
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
    def images(self) -> typing.List[InputMediaPhoto] | None:
        images = []
        for img_tag in self._quote_tag.css('img'):
            images.append(InputMediaPhoto(img_tag.attributes['src']))
        if images:
            return images

    @functools.cached_property
    def explanation(self) -> str | None:
        explanation_tag = self._quote_tag.css_first('div.field-name-field-description div.field-item')
        if explanation_tag is not None:
            explanation_text = utils.optimize_text(explanation_tag.text())
            return explanation_text

    @functools.cached_property
    def has_original(self) -> bool:
        """
        Имеет ли цитата оригинальную версию на иностранном языке.
        """
        return self._quote_tag.css_matches('div.quote__original')

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
                return text_tag.text().strip()
            case original_tag, translation_tag:
                return original_tag.text().strip(), translation_tag.text().strip()
            case _:
                raise ValueError('Отсутствует текст цитаты')

    @property
    def _pritcha_header(self) -> str:
        return self._quote_tag.css_first('h2').text()

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
        if self.type is QuoteTypes.pritcha:
            taxonomy_elem = self.get_taxonomy_elem('Притча')
            yield taxonomy_elem.add_content(self._pritcha_header)
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
                return f'Притча «{self._quote_tag.css_first("h2").text()}»'
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
