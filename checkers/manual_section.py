from .base import BaseChecker


class ManualSectionChecker(BaseChecker):
    def __init__(self, title: str, note: str = ""):
        self.TITLE = title
        self.note = note

    def check(self, page, inn: str):
        print(f"  ⚠️  {self.TITLE}: ручной раздел. {self.note}")
        return None
