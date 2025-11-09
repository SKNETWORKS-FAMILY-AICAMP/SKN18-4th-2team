from typing import Any, Dict, List

from langchain.text_splitter import RecursiveCharacterTextSplitter

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def split_chunk_rows(
    rows: List[Dict[str, Any]],
    chunk_size: int,
    chunk_overlap: int,
    separators: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Split each row's chunk_text into smaller segments and add chunk_index metadata.

    Args:
        rows: CSV rows that include chunk_text/metadata.
        chunk_size: Max characters per chunk passed to the splitter.
        chunk_overlap: Overlap size between adjacent chunks.
        separators: Optional custom separators (defaults to DEFAULT_SEPARATORS).
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators or DEFAULT_SEPARATORS,
    )

    chunked_rows: List[Dict[str, str]] = []

    for row in rows:
        text = (row.get("chunk_text") or "").strip()
        if not text:
            continue

        splits = splitter.split_text(text)
        if not splits:
            continue

        for idx, split_text in enumerate(splits):
            chunk_text = split_text.strip()
            if not chunk_text:
                continue

            new_row = dict(row)
            new_row["chunk_index"] = idx
            new_row["chunk_text"] = chunk_text
            chunked_rows.append(new_row)

    return chunked_rows
