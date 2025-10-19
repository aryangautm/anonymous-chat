"""Vector similarity search using pgvector."""

from typing import List, Dict
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embeddings.tools import embedding_tools


class VectorSearchService:
    """Service for vector similarity search."""

    async def search_similar_chunks(
        self,
        db: AsyncSession,
        persona_id: UUID,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Dict]:
        """
        Search for similar knowledge chunks using vector similarity.

        Args:
            db: Database session
            persona_id: Persona ID to search within
            query_text: Query text to search for
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of dicts with chunk info and similarity score
        """
        # Generate query embedding
        query_embedding = embedding_tools.embed_query(query_text)

        # Build SQL query with vector similarity
        # Using cosine distance (1 - cosine similarity)
        query_sql = text(
            """
            SELECT 
                kc.id,
                kc.module_id,
                kc.chunk_text,
                kc.chunk_index,
                kc.token_count,
                kc.metadata,
                km.module_type,
                km.title,
                km.priority,
                1 - (kc.embedding <=> :query_embedding) as similarity_score
            FROM knowledge_chunks kc
            JOIN knowledge_modules km ON kc.module_id = km.id
            WHERE km.persona_id = :persona_id
                AND km.is_active = true
                AND kc.embedding IS NOT NULL
                AND 1 - (kc.embedding <=> :query_embedding) >= :threshold
            ORDER BY 
                km.priority DESC,
                similarity_score DESC
            LIMIT :top_k
        """
        )

        result = await db.execute(
            query_sql,
            {
                "query_embedding": str(query_embedding),
                "persona_id": str(persona_id),
                "threshold": similarity_threshold,
                "top_k": top_k,
            },
        )

        rows = result.fetchall()

        return [
            {
                "chunk_id": row[0],
                "module_id": row[1],
                "chunk_text": row[2],
                "chunk_index": row[3],
                "token_count": row[4],
                "metadata": row[5],
                "module_type": row[6],
                "module_title": row[7],
                "module_priority": row[8],
                "similarity_score": float(row[9]),
            }
            for row in rows
        ]

    async def search_by_module_type(
        self,
        db: AsyncSession,
        persona_id: UUID,
        query_text: str,
        module_types: List[str],
        top_k: int = 3,
    ) -> List[Dict]:
        """
        Search within specific module types.

        Useful for targeted retrieval (e.g., only from 'qna' modules).
        """
        query_embedding = embedding_tools.embed_query(query_text)

        query_sql = text(
            """
            SELECT 
                kc.id,
                kc.module_id,
                kc.chunk_text,
                km.module_type,
                1 - (kc.embedding <=> :query_embedding) as similarity_score
            FROM knowledge_chunks kc
            JOIN knowledge_modules km ON kc.module_id = km.id
            WHERE km.persona_id = :persona_id
                AND km.module_type = ANY(:module_types)
                AND km.is_active = true
                AND kc.embedding IS NOT NULL
            ORDER BY 
                km.priority DESC,
                similarity_score DESC
            LIMIT :top_k
        """
        )

        result = await db.execute(
            query_sql,
            {
                "query_embedding": str(query_embedding),
                "persona_id": str(persona_id),
                "module_types": module_types,
                "top_k": top_k,
            },
        )

        rows = result.fetchall()
        return [
            {
                "chunk_id": row[0],
                "module_id": row[1],
                "chunk_text": row[2],
                "module_type": row[3],
                "similarity_score": float(row[4]),
            }
            for row in rows
        ]


vector_search_service = VectorSearchService()
