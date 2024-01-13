from functools import cached_property


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
    def count(self) -> int:
        return len(self._content)

    @cached_property
    def plain_text(self) -> str:
        text = []
        for content_item in self._content:
            if isinstance(content_item, str):
                text.append(content_item)
            else:
                text.append(content_item['text'])
        return ', '.join(text)

    def __str__(self):
        text = f'{self.emoji} **{self.title}:** '
        for content_item in self._content:
            if isinstance(content_item, dict):
                text += f'[{content_item["text"]}]({content_item["url"]}), '
            else:
                text += f'{content_item}, '
        return text.removesuffix(', ')
