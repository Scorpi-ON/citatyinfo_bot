import enum
import typing
from copy import deepcopy
from functools import cached_property

from selectolax.lexbor import LexborHTMLParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, \
                           InputMediaPhoto

from src import utils, const
from src.const import *
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


class Quote:
    """
    Одиночная цитата.
    """
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
        return deepcopy(cls.TAXONOMY_TEMPLATES[key])

    def __init__(self, html_page: str):
        """
        Args:
            html_page: веб-страница, содержащая цитату
        """
        self._tree = LexborHTMLParser(html_page).body
        self._quote_with_meta_tag = self._tree.css_first('article')
        self._quote_tag = self._quote_with_meta_tag.css_first('div.node__content')
        # Здесь должно быть получение self.rating_tag, но на сайте его больше нет

    @cached_property
    def id(self) -> str:
        """
        ID цитаты. Нужен для формирования прямой ссылки.
        Examples:
            ``35045``: https://citaty.info/quote/35045
        """
        return self._quote_with_meta_tag.id.removeprefix('node-')

    @cached_property
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

    @cached_property
    def header(self) -> str | None:
        """
        Заголовок цитаты. Актуален только для притч, у остальных цитат отсутствует.
        """
        if self.type is QuoteTypes.pritcha:
            header_tag = self._tree.css_first('h1')
            if header_tag is None:                            # У случайных притч хедер находится
                header_tag = self._quote_tag.css_first('h2')  # непосредственно перед текстом
            return header_tag.text()

    @property
    def rel_link(self) -> str:
        """
        Относительная ссылка на цитату. Нужна для формирования
        полноценной ссылки в последующем.
        Examples:
            ``quote/35045``: https://citaty.info/quote/35045
        """
        return f'{self.type.name}/{self.id}'

    @property
    def text(self) -> str | typing.Tuple[str, str]:
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
                return text_tag.text().strip()
            case original_tag, translation_tag:
                return original_tag.text().strip(), translation_tag.text().strip()
            case _:
                raise ValueError('Отсутствует текст цитаты')

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
            yield taxonomy_elem.add_content(self.header)
        else:
            taxonomy_tags = self._quote_with_meta_tag.css('div.node__content > div.field-type-taxonomy-term-reference')
            for tag in taxonomy_tags:
                if link_tag := tag.css_first('a'):  # бывает, что находятся пустые div'ы без ссылок
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

    @cached_property
    def images(self) -> typing.List[InputMediaPhoto] | None:
        images = []
        for img_tag in self._quote_tag.css('img'):
            images.append(InputMediaPhoto(img_tag.attributes['src']))
        if images:
            return images

    @property
    def has_original(self) -> bool:
        """
        Имеет ли цитата оригинальную версию на иностранном языке.
        """
        return self._quote_tag.css_matches('div.quote__original')

    @cached_property
    def explanation(self) -> str | None:
        explanation_tag = self._quote_tag.css_first('div.field-name-field-description div.field-item')
        if explanation_tag is not None:
            explanation_text = utils.optimize_text(explanation_tag.text())
            return explanation_text

    @cached_property
    def _string_representation(self) -> str:
        text = self.text
        topics = tuple(self._topics)
        if isinstance(text, tuple):
            text = f'**Оригинал:**\n{text[0]}\n\n**Перевод:**\n{text[1]}'
        text += '\n\n'
        for taxonomy_elem in self._taxonomy:
            text += f'{taxonomy_elem}\n'
        text += '\n'
        for topic in topics:
            text += f'[#{topic["text"]}]({topic["url"]}) '
        return utils.optimize_text(text)

    def __str__(self):
        return self._string_representation

    @cached_property
    def keyboard(self) -> InlineKeyboardMarkup:
        row = []
        # if rating := self.rating:
        #     first_row.append(InlineKeyboardButton('⭐ Рейтинг', rating))
        if explanation := self.explanation:
            explanation = explanation.encode(const.STR_ENCODING)
            if len(explanation) > MAX_CALLBACK_DATA_LENGTH:
                explanation = f'e{self.rel_link}'
            row.append(InlineKeyboardButton('🔮 Пояснение', explanation))
        if self.has_original:
            row.append(InlineKeyboardButton('🇬🇧 Оригинал', f'o{self.id}'))
        row.append(InlineKeyboardButton('🔗 Открыть', url=BASE_URL % self.rel_link))
        return InlineKeyboardMarkup([row])

    # @property
    # def rating(self) -> str | None:
    #     rating_tag = self._rating_tag.find(
    #         'div', class_='rate-widget-rating__inner')
    #     sum, neg, pos = rating_tag.find_all(recursive=False)
    #     sum, neg, pos = sum.text(), neg.text(), pos.text()
    #     if (sum, neg, pos) != ('0', '0', '0'):
    #         if neg == '0':
    #             return sum
    #         elif pos == '0':
    #             return f'-{sum}'
    #         else:
    #             return f'{pos} - {neg} = {sum}'
