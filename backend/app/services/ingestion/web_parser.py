import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from typing import List


# Only keep post title, headers, and content from the full HTML.
async def load_web_content(url: str) -> List[Document]:
    """
    Load and parse web content from a URL.

    Args:
        url: The URL to load content from

    Returns:
        List of Document objects
    """
    bs4_strainer = bs4.SoupStrainer(
        class_=("post-title", "post-header", "post-content")
    )
    loader = WebBaseLoader(
        web_paths=(url,),
        bs_kwargs={"parse_only": bs4_strainer},
    )
    docs = await loader.aload()

    return docs
