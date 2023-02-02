from enum import Enum
import typing
from copy import deepcopy
from functools import cached_property

from bs4 import BeautifulSoup
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, \
                           InputMediaPhoto

import utils
from const import *


class TaxonomyElem:
    def __init__(self, emoji: str, title: str):
        self.emoji = emoji
        self.title = title
        self._content = []

    def add_content(self, text: str,
                    url: str | None = None):
        self._content.append(
            {'text': text, 'url': url} if url else text
        )
        return self

    @cached_property
    def plain_text(self) -> str:
        text = []
        for content_item in self._content:
            if isinstance(content_item, str):
                text.append(content_item)
            else:
                text.append(content_item["text"])
        return ', '.join(text)

    def __str__(self):
        text = f'{self.emoji} **{self.title}:** '
        for content_item in self._content:
            if isinstance(content_item, dict):
                text += f'[{content_item["text"]}]({content_item["url"]}), '
            else:
                text += f'{content_item}, '
        return text.removesuffix(', ')


class Quote:
    TYPES = Enum('Quote types', 'quote po pritcha')
    TAXONOMY_TEMPLATES = {
        'Автор цитаты': TaxonomyElem('©️', 'Автор'),
        'Автор неизвестен': TaxonomyElem('©️', 'Автор').add_content('неизвестен'),
        'Цитируемый персонаж': TaxonomyElem('💬', 'Цитируемые персонажи'),
        'Исполнитель': TaxonomyElem('🎤', 'Исполнители'),
        'Цитата из книги': TaxonomyElem('📖', 'Произведение'),
        'Цитата из фильма': TaxonomyElem('🎬', 'Фильм'),
        'Цитата из мультфильма': TaxonomyElem('🧸', 'Мультфильм'),
        'Цитата из сериала': TaxonomyElem('🎥', 'Сериал'),
        'Цитата из телешоу': TaxonomyElem('📺', 'Телешоу'),
        'Цитата из спектакля': TaxonomyElem('🎭', 'Спектакль'),
        'Цитата из игры': TaxonomyElem('🎮', 'Игра'),
        'Цитата из комикса': TaxonomyElem('🦸🏻\u200d♂️', 'Комикс'),
        'Цитата из аниме': TaxonomyElem('🥷🏻', 'Аниме'),
        'Песня': TaxonomyElem('🎵', 'Песня'),
        'Самиздат': TaxonomyElem('✍🏻', 'Самиздат'),
        'Притча': TaxonomyElem('☯', 'Притча'),
        'Фольклор': TaxonomyElem('📜', 'Фольклор'),
        'Эпизод': TaxonomyElem('📀', 'Эпизод')
    }

    def __init__(self, html_page: str):
        self._soup = BeautifulSoup(html_page, 'lxml')
        self._quote_tag = self._soup.article
        self._content_tag, self._rating_tag, _ = self._quote_tag.findChildren(recursive=False)
        self._main_body_tag = self._content_tag.findChildren(recursive=False)[0].extract()
        self.id, self.type, self.header  # вызываем кеширование свойств, которые используют
        del self._soup, self._quote_tag  # избыточные теги, которые после этого удаляем

    @cached_property
    def id(self) -> str:
        return self._quote_tag['id'].removeprefix('node-')

    @cached_property
    def type(self) -> Enum:
        if 'node-po' in self._quote_tag['class']:
            type = Quote.TYPES.po
        elif 'node-pritcha' in self._quote_tag['class']:
            type = Quote.TYPES.pritcha
        else:
            type = Quote.TYPES.quote
        return type

    @cached_property
    def header(self) -> str | None:
        if self.type is Quote.TYPES.pritcha:
            header_tag = self._soup.h1
            if header_tag is None:                           # у случайных цитат хедер находится в теге,
                header_tag = self._content_tag.extract().h2  # отличном от обычных цитат
            return header_tag.text

    @cached_property
    def rel_link(self) -> str:
        return f'{self.type.name}/{self.id}'

    @cached_property
    def url(self) -> str:
        return BASE_URL % self.rel_link

    @property
    def text(self) -> str | typing.Tuple[str]:
        match self._main_body_tag.findChildren(recursive=False):
            case original_tag, translated_tag:
                return original_tag.text.strip(), translated_tag.text.strip()
            case (text_tag,):
                return text_tag.text.strip()

    @property
    def _series(self) -> TaxonomyElem | None:
        if self.type is Quote.TYPES.quote:
            series_tag = self._content_tag.find(
                'div', class_='node__series', recursive=False)
            if series_tag is not None:
                taxonomy_elem = deepcopy(Quote.TAXONOMY_TEMPLATES['Эпизод'])
                for serie_tag in series_tag.find_all('div', class_='field-item'):
                    if link_tag := serie_tag.find('a'):
                        taxonomy_elem.add_content(link_tag.text, link_tag['href'])
                    else:
                        taxonomy_elem.add_content(serie_tag.text.strip())
                return taxonomy_elem

    @property
    def taxonomy(self) -> typing.Generator[TaxonomyElem, None, None]:
        if self.type is Quote.TYPES.pritcha:
            yield deepcopy(Quote.TAXONOMY_TEMPLATES['Притча']).add_content(self.header)
        else:
            taxonomy_tags = self._content_tag.find_all(
                'div', class_='field-type-taxonomy-term-reference',
                recursive=False)
            for tag in taxonomy_tags:
                key = tag.a.get('title', 'Фольклор')  # ссылки на пословицы не имеют атрибута title
                taxonomy_elem = deepcopy(Quote.TAXONOMY_TEMPLATES[key])
                if key != 'Автор неизвестен':
                    for link_tag in tag.find_all('a'):
                        taxonomy_elem.add_content(link_tag.text, link_tag['href'])
                yield taxonomy_elem
            if series := self._series:
                yield series

    @property
    def topics(self) -> typing.Generator[dict, None, None]:
        topics = []
        topics_tag = self._content_tag.find('div', class_='node__topics')
        if topics_tag is not None:
            topics.extend(topics_tag.find_all('a'))       # основные темы, приведённые под цитатой
        topics.extend(self._main_body_tag.find_all('a'))  # темы, встроенные в текст цитаты
        for num, topic in enumerate(topics):
            topic = {'text': topic.text.lower().replace(', ', ' #'),
                     'url': topic['href']}  # преобразуем теги в удобные для использования словари
            if topic['url'] not in topics:  # и отсеиваем, если такие ссылки (не текст,
                yield topic
            topics[num] = topic['url']      # т. к. он может отличаться) уже есть

    @cached_property
    def images(self) -> typing.List[InputMediaPhoto] | None:
        images = []
        for img_tag in self._content_tag.find_all('img'):
            images.append(InputMediaPhoto(img_tag['src']))
        if images:
            return images

    @property
    def has_original(self) -> bool:
        return bool(
            self._content_tag.find('div', class_='quote__original')
        )

    @cached_property
    def explanation(self) -> str | None:
        explanation_tag = self._content_tag.find(
            'div', class_='field-name-field-description', recursive=False)
        if explanation_tag is not None:
            return utils.normalize(
                explanation_tag.text.strip().splitlines()[-1]
            )  # отсекаем надпись «Пояснение к цитате»

    @property
    def rating(self) -> str | None:
        rating_tag = self._rating_tag.find(
            'div', class_='rate-widget-rating__inner')
        sum, neg, pos = rating_tag.findChildren(recursive=False)
        sum, neg, pos = sum.text.strip(), neg.text, pos.text
        if (sum, neg, pos) != ('0', '0', '0'):
            if neg == '0':
                return sum
            elif pos == '0':
                return f'-{sum}'
            else:
                return f'{pos} - {neg} = {sum}'

    @cached_property
    def __string_representation(self) -> str:
        if isinstance(text := self.text, tuple):
            text = f'**Оригинал:**\n{text[0]}\n\n**Перевод:**\n{text[1]}'
        if self.type is Quote.TYPES.pritcha:
            text = f'**{self.header}**\n{text}'
        text += '\n\n'
        for taxonomy_elem in self.taxonomy:
            text += f'{taxonomy_elem}\n'
        text += '\n'
        for topic in self.topics:
            text += f'[#{topic["text"]}]({topic["url"]}) '
        return utils.normalize(text)

    def __str__(self):
        return self.__string_representation

    @cached_property
    def keyboard(self) -> InlineKeyboardMarkup:
        first_row = []
        if rating := self.rating:
            first_row.append(InlineKeyboardButton('⭐ Рейтинг', rating))
        if explanation := self.explanation:
            if explanation.__sizeof__() > 128:
                explanation = f'e{self.rel_link}'
            first_row.append(InlineKeyboardButton('🔮 Пояснение', explanation))
        if self.has_original:
            first_row.append(InlineKeyboardButton('🇬🇧 Оригинал', f'o{self.id}'))
        return InlineKeyboardMarkup([
            first_row,
            [InlineKeyboardButton('🔗 Открыть', url=self.url)]
        ])
