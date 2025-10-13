from typing import List

from tqdm import tqdm

from .model import EmbeddingModel


class EmbeddingTools:
    def __init__(self):
        self.embedding_model = EmbeddingModel.get_embedding_model()

    @classmethod
    def embed_query(cls, query: str) -> List[float]:
        """
        Embed a query string.
        """
        try:
            model = cls.embedding_model
            query_embedding = model.embed_query(query)
        except Exception as e:
            print(f"Error embedding query: {e}")
            return []

        return query_embedding

    @classmethod
    def embed_document(cls, text_document: List[str]) -> List[List[float]]:
        """
        Embed the document list
        """
        if not text_document:
            return []

        model = cls.embedding_model
        embeddings = []

        batch_size = 500
        for i in tqdm(
            range(0, len(text_document), batch_size),
            desc="Processing",
            unit="batch",
            bar_format="{l_bar}{bar} | {n_fmt}/{total_fmt} batches embedded",
            ncols=100,
            leave=False,
        ):
            batch = text_document[i : i + batch_size]
            try:
                batch_embeddings = model.embed_documents(batch)
                embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"Error embedding batch {i//batch_size}: {e}")
                return []

        print(f"Embedded total {len(embeddings)} documents!")
        return embeddings
