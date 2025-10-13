import os
from typing import List

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    CSVLoader,
    UnstructuredExcelLoader,
)
from langchain_core.documents import Document


def load_document(file_path: str, filename: str) -> List[Document]:
    """
    Load a document using the appropriate loader based on file extension.

    Args:
        file_path: Path to the file
        filename: Original filename

    Returns:
        List of Document objects
    """
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext in [".doc", ".docx"]:
            loader = UnstructuredWordDocumentLoader(file_path)
        elif ext == ".csv":
            loader = CSVLoader(file_path)
        elif ext in [".xls", ".xlsx"]:
            loader = UnstructuredExcelLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        docs = loader.load()

        # Add source metadata
        for doc in docs:
            doc.metadata["source"] = filename

        return docs

    except Exception as e:
        raise Exception(f"Error loading file {filename}: {str(e)}")
