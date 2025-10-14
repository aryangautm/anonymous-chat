from typing import List
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    CSVLoader,
    UnstructuredExcelLoader,
)
from langchain_core.documents import Document

from app.core.storage import get_s3_client


def load_document(file_storage_key: str) -> List[Document]:
    """
    Load a document from S3 storage using the appropriate loader based on file extension.

    Args:
        file_storage_key: S3 key/path to the file in storage

    Returns:
        List of Document objects
    """
    ext = Path(file_storage_key).suffix.lower()

    if ext not in [".pdf", ".doc", ".docx", ".csv", ".xls", ".xlsx"]:
        raise ValueError(f"Unsupported file type: {ext}")

    s3_client = get_s3_client()

    try:
        with s3_client.download_to_temp(file_storage_key, suffix=ext) as temp_path:
            if ext == ".pdf":
                loader = PyPDFLoader(temp_path)
            elif ext in [".doc", ".docx"]:
                loader = UnstructuredWordDocumentLoader(temp_path)
            elif ext == ".csv":
                loader = CSVLoader(temp_path)
            elif ext in [".xls", ".xlsx"]:
                loader = UnstructuredExcelLoader(temp_path)

            docs = loader.load()

            filename = Path(file_storage_key).name
            for doc in docs:
                doc.metadata["source"] = filename
                doc.metadata["storage_key"] = file_storage_key

            return docs

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error loading file {file_storage_key}: {str(e)}")
