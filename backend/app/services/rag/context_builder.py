"""Builds context for LLM from retrieved chunks."""

from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.persona import Persona
from app.memory.vectorstore import _vector_store
from app.crud.crud_knowledge import knowledge_module_crud


class ContextBuilder:
    """Builds optimized context from retrieved knowledge."""

    def __init__(self, max_context_tokens: int = 2000):
        self.max_context_tokens = max_context_tokens

    async def build_context(
        self,
        db: AsyncSession,
        persona: Persona,
        query: str,
        conversation_history: List[Dict] = None,
    ) -> Dict[str, any]:
        """
        Build complete context for LLM generation.

        Args:
            db: Database session
            persona: Persona model
            query: User's query
            conversation_history: Previous messages in conversation

        Returns:
            Dict with 'system_prompt', 'context', 'sources'
        """

        modules = await knowledge_module_crud.get_by_persona(
            db=db, persona_id=persona.id
        )
        module_ids = [module.id for module in modules]
        # 1. Search for relevant chunks

        relevant_chunks = await _vector_store.asimilarity_search(
            query=query, k=5, filter={"module_id": {"$in": module_ids}}
        )

        # 2. Build system prompt
        system_prompt = self._build_system_prompt(persona)

        # 3. Build context from chunks
        context_parts = []
        total_tokens = 0
        sources_used = []

        for chunk in relevant_chunks:
            chunk_tokens = chunk["token_count"] or 0
            if total_tokens + chunk_tokens > self.max_context_tokens:
                break

            context_parts.append(
                f"[Source: {chunk['module_type']} - {chunk['module_title']}]\n"
                f"{chunk['chunk_text']}"
            )
            total_tokens += chunk_tokens
            sources_used.append(
                {
                    "chunk_id": str(chunk["chunk_id"]),
                    "module_id": str(chunk["module_id"]),
                    "module_type": chunk["module_type"],
                    "similarity_score": chunk["similarity_score"],
                }
            )

        context = "\n\n---\n\n".join(context_parts)

        # 4. Format conversation history
        history_text = ""
        if conversation_history:
            history_parts = []
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = "User" if msg["sender"] == "VISITOR" else "Assistant"
                history_parts.append(f"{role}: {msg['content']}")
            history_text = "\n".join(history_parts)

        return {
            "system_prompt": system_prompt,
            "context": context,
            "conversation_history": history_text,
            "sources_used": sources_used,
        }

    def _build_system_prompt(self, persona: Persona) -> str:
        """Build system prompt from persona configuration."""
        parts = []

        # Base prompt
        if persona.system_prompt:
            parts.append(persona.system_prompt)
        elif persona.base_prompt:
            parts.append(persona.base_prompt)
        else:
            parts.append(
                f"You are {persona.public_name}, an AI assistant. "
                "You provide helpful, accurate, and friendly responses."
            )

        # Instructions for using context
        parts.append(
            "\nYou have access to the following knowledge sources. "
            "Use them to provide accurate, specific answers. "
            "If the information isn't in the provided context, say so honestly."
        )

        return "\n\n".join(parts)


context_builder = ContextBuilder()
