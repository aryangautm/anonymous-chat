from typing import List

from langchain_core.documents import Document
from app.core.config import settings


from typing import List, Tuple
import tiktoken


class TextProcessor:
    """Handles text chunking and token counting."""

    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize with encoding for specific model."""
        self.encoding = tiktoken.encoding_for_model(model_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def chunk_text(
        self,
        text: str,
        chunk_size: int = settings.CHUNK_SIZE_TOKENS,
        overlap: int = settings.CHUNK_OVERLAP_TOKENS,
    ) -> List[Document]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text to chunk
            chunk_size: Max tokens per chunk
            overlap: Token overlap between chunks

        Returns:
            List of Document objects
        """
        tokens = self.encoding.encode(text)
        chunks = []
        start = 0

        while start < len(tokens):
            end = start + chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(
                Document(
                    page_content=chunk_text,
                    metadata={"token_count": len(chunk_tokens)},
                )
            )

            # Move start forward, leaving overlap
            start = end - overlap if end < len(tokens) else len(tokens)

        return chunks

    def extract_questions_and_answers(self, content: dict) -> List[Tuple[str, str]]:
        """
        Extract Q&A pairs from various content formats.

        Args:
            content: JSONB content from knowledge module

        Returns:
            List of (question, answer) tuples
        """
        pairs = []

        if "pairs" in content:
            # Direct Q&A format: {"pairs": [{"q": "...", "a": "..."}, ...]}
            for pair in content["pairs"]:
                if "q" in pair and "a" in pair:
                    pairs.append((pair["q"], pair["a"]))

        return pairs


# Singleton instance
text_processor = TextProcessor()
