import bs4
from langchain_community.document_loaders import WebBaseLoader, GitLoader, YoutubeLoader
from langchain_core.documents import Document
from typing import List


# Only keep post title, headers, and content from the full HTML.
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
    print("Loaded", len(docs), "documents")

    return docs
