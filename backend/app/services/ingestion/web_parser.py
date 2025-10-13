import bs4
from langchain_community.document_loaders import WebBaseLoader


# Only keep post title, headers, and content from the full HTML.
def load_web_content(url: str):
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
    docs = loader.load()

    return docs
