import functools

from . import utils


class TaxonomyElem:
    def __init__(self, emoji: str, title: str,
                 content: list[str | dict[str, str]] = []):
        self.emoji = emoji
        self.title = utils.optimize_text(title)
        self.content = content

    def add_content(self, text: str,
                    url: str = None) -> 'TaxonomyElem':
        self.content.append(
            {'text': utils.optimize_text(text), 'url': url}
            if url else text
        )
        return self

    @functools.cached_property
    def count(self) -> int:
        return len(self.content)

    def copy(self) -> 'TaxonomyElem':
        return TaxonomyElem(self.emoji, self.title, self.content.copy())

    @functools.cached_property
    def plain_content(self) -> str:
        text = []
        for content_item in self.content:
            if isinstance(content_item, str):
                text.append(content_item)
            else:
                text.append(content_item['text'])
        return ', '.join(text)
