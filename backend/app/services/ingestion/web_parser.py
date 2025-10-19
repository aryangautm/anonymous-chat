from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from typing import List


def load_web_content(url: str) -> List[Document]:
    """
    Load and parse web content from a URL.

    Args:
        url: The URL to load content from

    Returns:
        List of Document objects
    """
    loader = WebBaseLoader(
        web_paths=(url,),
    )
    docs = loader.load()

    return docs
