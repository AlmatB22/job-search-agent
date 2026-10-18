from jsa.retrieve import CHUNK_CHARS, Retriever, _pack, load_chunks, tokenize


def test_tokenize_keeps_tech_names():
    assert tokenize("C++, C# and Node.js.") == ["c++", "c#", "and", "node.js"]


def test_pack_respects_size():
    paragraphs = ["x" * 300] * 5
    chunks = _pack(paragraphs)
    assert len(chunks) == 3
    assert all(len(c) <= CHUNK_CHARS for c in chunks)


def test_markdown_ids_use_heading_slug():
    ids = [c.id for c in load_chunks("data/sample_docs")]
    assert "projects.md#rental-listings-warehouse-1" in ids
    assert len(ids) == len(set(ids))


def test_search_finds_skill_and_dedupes():
    retriever = Retriever(load_chunks("data/sample_docs"))
    hits = retriever.search(["Airflow", "Airflow"])
    ids = [h.id for h in hits]
    assert "projects.md#rental-listings-warehouse-1" in ids
    assert len(ids) == len(set(ids))


def test_search_caps_results():
    retriever = Retriever(load_chunks("data/sample_docs"))
    assert len(retriever.search(["Python", "SQL", "Docker", "Airflow"], limit=2)) == 2


def test_markdown_chunks_keep_heading(tmp_path):
    body = "\n\n".join(["word " * 120] * 3)  # three ~600-char paragraphs
    (tmp_path / "notes.md").write_text(f"# Title\n\n## Long section\n\n{body}\n")
    chunks = load_chunks(tmp_path)
    assert [c.id for c in chunks] == [f"notes.md#long-section-{n}" for n in (1, 2, 3)]
    assert all(c.text.startswith("## Long section\n") for c in chunks)
