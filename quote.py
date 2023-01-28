import typing
from copy import deepcopy
from bs4 import BeautifulSoup
import utils
from const import *


class TaxonomyElem:
    def __init__(self, title, category_url=None):
        self.title = title
        self.category_url = category_url
        self.content = []

    def add_content(self, text, url=None):
        self.content.append({'text': text, 'url': url} if url else text)
        return self

    def __str__(self):
        if self.category_url is None:
            text = f'**{self.title}:** '
        else:
            text = f'**[{self.title}]({self.category_url}):** '
        for content_item in self.content:
            if isinstance(content_item, dict):
                text += f'[{content_item["text"]}]({content_item["url"]}), '
            else:
                text += f'{content_item}, '
        return text.removesuffix(', ')


class Quote:
    TAXONOMY_TEMPLATES = {
        'Автор цитаты': TaxonomyElem('©️ Автор', BASE_CATEGORY_URL % 'man'),
        'Автор неизвестен': TaxonomyElem('©️ Автор', BASE_CATEGORY_URL % 'man')
            .add_content('неизвестен', BASE_URL % 'other'),
        'Цитируемый персонаж': TaxonomyElem('💬 Цитируемые персонажи'),
        'Исполнитель': TaxonomyElem('🎤 Исполнители', BASE_CATEGORY_URL % 'music'),
        'Цитата из книги': TaxonomyElem('📖 Произведение', BASE_CATEGORY_URL % 'book'),
        'Цитата из фильма': TaxonomyElem('🎬 Фильм', BASE_CATEGORY_URL % 'movie'),
        'Цитата из мультфильма': TaxonomyElem('🧸 Мультфильм', BASE_CATEGORY_URL % 'cartoon'),
        'Цитата из сериала': TaxonomyElem('🎥 Сериал', BASE_CATEGORY_URL % 'series'),
        'Цитата из телешоу': TaxonomyElem('📺 Телешоу', BASE_CATEGORY_URL % 'tv'),
        'Цитата из спектакля': TaxonomyElem('🎭 Спектакль', BASE_CATEGORY_URL % 'theater'),
        'Цитата из игры': TaxonomyElem('🎮 Игра', BASE_CATEGORY_URL % 'game'),
        'Цитата из комикса': TaxonomyElem('🦸🏻\u200d♂️ Комикс', BASE_CATEGORY_URL % 'comics'),
        'Цитата из аниме': TaxonomyElem('ツ Аниме', BASE_CATEGORY_URL % 'anime'),
        'Песня': TaxonomyElem('🎵 Песня', BASE_CATEGORY_URL % 'music'),
        'Самиздат': TaxonomyElem('✍🏻 Самиздат', BASE_CATEGORY_URL % 'self'),
        'Притча': TaxonomyElem('☯ Притча', BASE_URL % 'pritchi'),
        'Фольклор': TaxonomyElem('📜 Фольклор', BASE_URL % 'po')
    }

    def __init__(self, html_page: str):
        quote_tag = BeautifulSoup(html_page, features='lxml').article
        self._content_tag, self._rating_tag, _ = quote_tag.findChildren(recursive=False)
        self._main_body_tag = self._content_tag.findChildren(recursive=False)[0].extract()

    @property
    def text(self) -> str | typing.Tuple[str]:
        match self._main_body_tag.findChildren(recursive=False):
            case original_tag, translated_tag:
                return original_tag.text.strip(), translated_tag.text.strip()
            case (text_tag,):
                return text_tag.text.strip()

    @property
    def topics(self) -> typing.Generator[dict, None, None]:
        topics = []
        topics_tag = self._main_body_tag.find('div', class_='node__topics')
        if topics_tag is not None:
            topics.extend(topics_tag.find_all('a'))       # основные темы, приведённые под цитатой
        topics.extend(self._main_body_tag.find_all('a'))  # темы, встроенные в текст цитаты
        for num, topic in enumerate(topics):
            topics[num] = None
            topic = {'text': topic.text, 'url': topic['href']}  # преобразуем теги в удобные для использования словари
            if topic not in topics:                             # и отсеиваем, если они уже есть в списке
                yield topic

    @property
    def rating(self) -> typing.Tuple[str]:
        rating_tag = self._rating_tag.find(
            'div', class_='rate-widget-rating__inner')
        sum, neg, pos = rating_tag.findChildren(recursive=False)
        return sum.text.strip(), neg.text, pos.text

    @property
    def has_original(self) -> bool:
        return bool(self._content_tag.find('div', class_='quote__original'))

    @property
    def taxonomy(self) -> typing.Generator[TaxonomyElem, None, None]:
        taxonomy_tags = self._content_tag.find_all(
            'div', class_='field-type-taxonomy-term-reference',
            recursive=False)
        for tag in taxonomy_tags:
            key = tag.a.get('title', 'Фольклор')  # ссылки на пословицы не имеют атрибута title
            taxonomy_elem = deepcopy(self.TAXONOMY_TEMPLATES[key])
            if key != 'Автор неизвестен':
                for link_tag in tag.find_all('a'):
                    taxonomy_elem.add_content(link_tag.text, link_tag['href'])
            yield taxonomy_elem

    @property
    def images(self) -> typing.Generator[str, None, None]:
        for img_tag in self._content_tag.find_all('img'):
            yield img_tag['src']

    @property
    def explanation(self) -> str | None:
        explanation_tag = self._content_tag.find(
            'div', class_='field-name-field-description', recursive=False)
        if explanation_tag is not None:
            return explanation_tag.text.strip().splitlines()[-1]  # отсекаем надпись «Пояснение к цитате»

    @property
    def series(self) -> str | None:
        series_tag = self._content_tag.find(
            'div', class_='node__series', recursive=False)
        if series_tag is not None:
            for serie_tag in series_tag.find_all('div', class_='field-item'):
                if link_tag := serie_tag.find('a'):
                    yield {'text': link_tag.text, 'url': link_tag['href']}
                else:
                    yield serie_tag.text.strip()

    def __str__(self):
        if isinstance(text := self.text, tuple):
            text = f'**Оригинал:**\n{text[0]}\n\n**Перевод:**\n{text[1]}'
        text += '\n\n'
        for taxonomy_elem in self.taxonomy:
            text += f'{taxonomy_elem}\n'
        rating = self.rating
        if rating != ('0', '0', '0'):
            text += '**⭐ Рейтинг:** '
            if rating[1] == '0':
                text += rating[0]
            elif rating[2] == '0':
                text += f'-{rating[0]}'
            else:
                text += f'{rating[2]} - {rating[1]} = {rating[0]}'
            text += '\n'
        text += '\n'
        for topic in self.topics:
            text += f'[#{topic["text"]}]({topic["url"]}) '
        return utils.normalize(text)
