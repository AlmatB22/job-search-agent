"""Load and chunk the candidate's documents; BM25 search over the chunks.

Each chunk gets a readable id (resume.pdf#p1-2, projects.md#ules-1) that the
matcher cites and the guard checks. BM25 is keyword search: no embedding model,
no GPU, deterministic results. Its blind spot is synonyms ("JS" vs "JavaScript").
"""

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader
from rank_bm25 import BM25Okapi

CHUNK_CHARS = 800
TOP_PER_SKILL = 3
MAX_CHUNKS = 20

_HEADING = re.compile(r"^#{1,6}\s+(.*)")


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    text: str


def docs_dir() -> str:
    return os.environ.get("JSA_DOCS_DIR", "data/my_docs")


def tokenize(text: str) -> list[str]:
    # Keep + # . inside tokens so "c++", "c#" and "node.js" survive; drop sentence dots.
    tokens = (t.rstrip(".") for t in re.findall(r"[a-z0-9+#.]+", text.lower()))
    return [t for t in tokens if t]


def _paragraphs(text: str) -> list[str]:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return [p.strip() for p in re.split(r"\n\s*\n", "\n".join(lines)) if p.strip()]


def _pack(paragraphs: list[str], size: int = CHUNK_CHARS) -> list[str]:
    """Join paragraphs into chunks of about `size` characters.

    A paragraph longer than `size` is split on its line breaks first.
    """
    units: list[str] = []
    for p in paragraphs:
        units.extend(p.splitlines() if len(p) > size else [p])
    chunks: list[str] = []
    current = ""
    for unit in units:
        if current and len(current) + 1 + len(unit) > size:
            chunks.append(current)
            current = unit
        else:
            current = f"{current}\n{unit}" if current else unit
    if current:
        chunks.append(current)
    return chunks


def _slug(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")[:40] or "section"


def _pdf_chunks(path: Path) -> list[Chunk]:
    chunks = []
    for page_no, page in enumerate(PdfReader(path).pages, 1):
        # Layout mode keeps line and paragraph breaks; the default mode breaks
        # some PDFs into one word per line.
        text = page.extract_text(extraction_mode="layout")
        for n, piece in enumerate(_pack(_paragraphs(text)), 1):
            chunks.append(Chunk(f"{path.name}#p{page_no}-{n}", path.name, piece))
    return chunks


def _markdown_chunks(path: Path) -> list[Chunk]:
    # Split into sections at headings; each section keeps its heading line as context.
    sections: list[tuple[str, list[str]]] = [("intro", [])]
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _HEADING.match(line)
        if m:
            sections.append((_slug(m.group(1)), []))
        sections[-1][1].append(line)
    chunks = []
    counts: dict[str, int] = {}
    for slug, lines in sections:
        for piece in _pack(_paragraphs("\n".join(lines))):
            counts[slug] = counts.get(slug, 0) + 1
            chunks.append(Chunk(f"{path.name}#{slug}-{counts[slug]}", path.name, piece))
    return chunks


def load_chunks(directory: str | Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(Path(directory).iterdir()):
        if path.name.startswith("."):
            continue
        if path.suffix.lower() == ".pdf":
            chunks.extend(_pdf_chunks(path))
        elif path.suffix.lower() in (".md", ".txt"):
            chunks.extend(_markdown_chunks(path))
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk]):
        if not chunks:
            raise ValueError("No documents to search; check JSA_DOCS_DIR")
        self.chunks = chunks
        self.bm25 = BM25Okapi([tokenize(c.text) for c in chunks])

    def search(self, skills: list[str], per_skill: int = TOP_PER_SKILL,
               limit: int = MAX_CHUNKS) -> list[Chunk]:
        """Top `per_skill` chunks for each skill, deduplicated, at most `limit`.

        Each skill gets its own query so common skills can't crowd out rare ones.
        Results are taken rank by rank across skills (every skill's best chunk
        first), so the cap cuts the weakest matches rather than the last skills.
        """
        ranked: list[list[int]] = []
        for skill in skills:
            query = tokenize(skill)
            if not query:
                continue
            scores = self.bm25.get_scores(query)
            top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:per_skill]
            ranked.append([i for i in top if scores[i] > 0])
        picked: dict[str, Chunk] = {}
        for rank in range(per_skill):
            for hits in ranked:
                if rank < len(hits) and len(picked) < limit:
                    chunk = self.chunks[hits[rank]]
                    picked.setdefault(chunk.id, chunk)
        return list(picked.values())


@lru_cache
def get_retriever(directory: str) -> Retriever:
    """Load and index a directory once per process."""
    return Retriever(load_chunks(directory))
