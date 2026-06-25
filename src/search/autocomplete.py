from __future__ import annotations

from collections import defaultdict
from typing import Any


class TrieNode:
    __slots__ = ("children", "is_end", "count")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_end: bool = False
        self.count: int = 0


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str, count: int = 1) -> None:
        node = self.root
        for ch in word.lower():
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.count += count

    def search(self, prefix: str, limit: int = 10) -> list[dict[str, Any]]:
        node = self.root
        for ch in prefix.lower():
            if ch not in node.children:
                return []
            node = node.children[ch]
        results: list[dict[str, Any]] = []
        self._collect(node, prefix.lower(), results, limit)
        return sorted(results, key=lambda x: -x["count"])[:limit]

    def _collect(self, node: TrieNode, prefix: str, results: list[dict[str, Any]], limit: int) -> None:
        if len(results) >= limit * 2:
            return
        if node.is_end:
            results.append({"word": prefix, "count": node.count})
        for ch in sorted(node.children.keys()):
            self._collect(node.children[ch], prefix + ch, results, limit)


class AutocompleteService:
    def __init__(self) -> None:
        self._trie = Trie()
        self._built = False

    def build(self, items: list[dict[str, Any]]) -> None:
        self._trie = Trie()
        for item in items:
            name = str(item.get("name", "") or "")
            words = set(name.lower().split())
            for word in words:
                self._trie.insert(word, count=1)
        self._built = True

    def suggest(self, prefix: str, limit: int = 10) -> list[str]:
        if not self._built:
            return []
        results = self._trie.search(prefix, limit=limit)
        return [r["word"] for r in results]

    async def ensure_built(self) -> None:
        if self._built:
            return
        from src.clients.c1_client import C1Client
        c1 = C1Client()
        try:
            items = await c1.list_nomenclature(query="", limit=5000)
            self.build(items)
        finally:
            await c1.close()


autocomplete = AutocompleteService()
