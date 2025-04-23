# Arquivo app/services/rag_service.py
#
# Serviço RAG responsável por:
# 1. Dividir textos clínicos em chunks coerentes (usando RecursiveCharacterTextSplitter).
# 2. Gerar embeddings para esses chunks com Sentence‑Transformers.
# 3. Persistir e recuperar embeddings no ChromaDB.
# 4. Sintetizar respostas de localização vascular de AVC com o modelo OpenAI de forma assíncrona.

import logging
from typing import List, Dict, Any, Optional

from sentence_transformers import SentenceTransformer  # type: ignore
from fastapi import Depends
from openai import AsyncOpenAI  # Cliente assíncrono

from langchain.text_splitter import RecursiveCharacterTextSplitter  # ← novo import

from backend.app.core.config import settings
from backend.app.services.vector_store import (
    VectorStoreService,
    get_vector_store_service,
)
from backend.app.schemas.query import RetrievedChunk

# Importar o seletor de imagens
import sys
import os
from backend.image_selector import process_syndrome_response

# Configuração básica do logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RAGService:
    """
    Serviço RAG para localização neurológica em AVC:
    - Chunking de textos clínicos (RecursiveCharacterTextSplitter).
    - Geração de embeddings.
    - Armazenamento / busca em vector store.
    - Síntese de resposta via LLM especializado em neurologia vascular.
    """

    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

        # --- Splitter recursivo ---
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        logger.info(
            "RecursiveCharacterTextSplitter configurado "
            f"(chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap})."
        )

        # Modelo de embedding
        logger.info(f"Carregando modelo de embedding: {settings.EMBEDDING_MODEL_NAME}")
        try:
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.exception("Falha ao carregar o modelo de embedding.")
            raise RuntimeError("Não foi possível carregar o modelo de embedding.") from e
        logger.info("Modelo de embedding carregado com sucesso.")

        # Cliente OpenAI assíncrono
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY não encontrada nas variáveis de ambiente. Usando valor padrão do dotenv.")
            api_key = settings.OPENAI_API_KEY
        self.ai_client = AsyncOpenAI(api_key=api_key)
        logger.info("RAGService inicializado com sucesso!")

    # ----------------------------------------------------------------- #
    # --------------------------- UTILITÁRIOS -------------------------- #
    # ----------------------------------------------------------------- #

    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Divide o texto clínico em chunks coerentes usando RecursiveCharacterTextSplitter.
        Retorna lista de strings (chunks) preservando sobreposição.
        """
        if not text:
            return []
        return self.text_splitter.split_text(text)

    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings usando Sentence‑Transformers."""
        if not texts:
            return []
        return self.embedding_model.encode(texts, show_progress_bar=False).tolist()

    async def _synthesize_answer(
        self, question: str, context_chunks: List[RetrievedChunk]
    ) -> str:
        """
        Usa o LLM para produzir uma localização neurológica precisa baseada nos chunks.
        Retorna string vazia caso falhe.
        """
        try:
            trechos = [
                f"(Trecho {idx}) {ch.text}"
                for idx, ch in enumerate(context_chunks, start=1)
            ]
            prompt_user = (
                f"Pergunta: {question}\n\n"
                "Trechos de contexto:\n"
                + "\n\n".join(trechos)
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a bilingual neurovascular assistant embedded in a Retrieval‑Augmented Generation (RAG) "
                        "engine dedicated to stroke‑lesion localization.\n\n"
                        
                        "Pipeline (do NOT reveal these steps):\n"
                        "1 Detect the input language (L₀).\n"
                        "2 If L₀ ≠ English, translate the full input to English with gpt‑4o‑mini → EN_QUERY.\n"
                        "3 Retrieve context passages (CTX) with EN_QUERY.\n"
                        "4 Extract the three most salient *symptom* keywords from EN_QUERY, ignoring stop‑words.\n"
                        "5 From CTX + EN_QUERY, retain only vascular syndromes whose classic picture includes **all** keywords; "
                        "rank the top four (#1 → #4).\n"
                        "6 For each ranked syndrome output KEY‑VALUE pairs exactly as follows:\n"
                        '   • \"syndrome\": Title Case (no abbreviations)\n'
                        '   • \"artery\": always \"Full Artery Name (ABBR)\", repeat the full form whenever a **new** abbreviation appears '
                        '(e.g. \"Lateral Branch of Posterior Inferior Cerebellar Artery (lPICA)\").\n'
                        '   • \"lesion_site\": precise singular anatomical noun; never use only \"bulbo\"; prefer \"lateral medulla\" or '
                        '\"lateral bulbo medullary\"; strip words \"territory\", \"region\", or \"area\".\n'
                        "7 Do NOT select an image or include any Imagem line in your response. The system will handle image selection separately.\n"
                        "8 Write a rationale paragraph of **exactly five** explanatory sentences (≤ 25 words each), prefixed \"#1:\" … \"#5:\".\n"
                        "   • #1 compares 1 vs 2; #2 compares 2 vs 3; #3 compares 3 vs 4; #4 explains why #1 addresses every keyword; "
                        "#5 gives a practical drawback of #4.\n"
                        "   • In every sentence cite ≤ 10 words from CTX or EN_QUERY inside double quotes.\n"
                        "9 Translate the finished answer back to L₀, keeping JSON keys, artery names and anatomical terms in English.\n"
                        "10 End with \"[database]\".\n\n"
                        
                        "Synonym constraints:\n"
                        "• Treat \"Wallenberg Syndrome\" and \"Síndrome Bulbo Lateral\" (a.k.a. \"Lateral Medullary Syndrome\") as EXACT synonyms; "
                        "never list them separately or count them as different syndromes.\n\n"
                        
                        "Response format (output nothing else):\n"
                        "Lista de síndromes: [{\"syndrome\":\"…\",\"artery\":\"…\",\"lesion_site\":\"…\"}, … ×4]\n"
                        "Notas: <five‑sentence rationale>\n"
                        "[database]\n\n"
                        
                        "Style constraints:\n"
                        "• Do NOT use bullets, dashes or numbered lists in the visible answer.\n"
                        "• Avoid vague terms like \"importante\", \"essencial\", \"relevante\", \"eficaz\".\n"
                        "• JSON must be valid; preserve the ranking order.\n"
                    )
                },
                {"role": "user", "content": prompt_user}
            ]

            completion = await self.ai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.1,
                max_tokens=1500,
                presence_penalty=0.1,
                frequency_penalty=0.2,
            )
            
            llm_response = completion.choices[0].message.content.strip()
            
            # Selecionar a imagem adequada baseada na resposta
            enhanced_response = await self._add_appropriate_image(llm_response)
            
            return enhanced_response
        except Exception as e:
            logger.error(f"Erro na chamada OpenAI: {e}", exc_info=True)
            return ""
    
    async def _add_appropriate_image(self, llm_response: str) -> str:
        """
        Adiciona a imagem mais adequada à resposta do LLM.
        Utiliza o módulo image_selector para selecionar dinamicamente 
        a imagem mais adequada para a primeira síndrome da lista.
        """
        try:
            # Usar o novo módulo de seleção de imagens
            enhanced_response = await process_syndrome_response(llm_response)
            return enhanced_response
        except Exception as e:
            logger.error(f"Erro ao adicionar imagem: {e}", exc_info=True)
            return llm_response

    # ----------------------------------------------------------------- #
    # ------------------ FLUXO PÚBLICO DE OPERAÇÃO -------------------- #
    # ----------------------------------------------------------------- #

    async def process_and_store_clinical_text(
        self, text: str, document_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Processa texto clínico: chunking, embeddings e storage."""
        if not text.strip():
            raise ValueError("O texto clínico não pode ser vazio.")
        if not document_id:
            raise ValueError("O document_id não pode ser vazio.")

        chunks = self._split_text_into_chunks(text)
        if not chunks:
            return 0

        embeddings = await self._generate_embeddings(chunks)
        if len(embeddings) != len(chunks):
            raise RuntimeError("Inconsistência na geração de embeddings.")

        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        base_meta = metadata or {}
        metadatas = [
            {**base_meta, "document_id": document_id, "chunk_index": i}
            for i in range(len(chunks))
        ]

        await self.vector_store.add_documents(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    async def retrieve_relevant_chunks(
        self, query: str, top_k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        """Recupera chunks mais relevantes para a query de localização de AVC."""
        logger.debug(f"Iniciando retrieve_relevant_chunks para query: '{query}'")
        if not query:
            logger.warning("Query vazia recebida em retrieve_relevant_chunks.")
            return []

        k = top_k if (top_k and top_k > 0) else settings.DEFAULT_TOP_K
        logger.debug(f"Gerando embedding para a query...")
        query_embedding = await self._generate_embeddings([query])
        if not query_embedding:
            logger.error("Falha ao gerar embedding para a query.")
            return []

        logger.debug(f"Consultando vector store com top_k={k}...")
        results = await self.vector_store.query_documents(
            query_embeddings=query_embedding, n_results=k
        )

        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        logger.debug(f"Vector store retornou {len(ids)} resultados.")

        chunks: List[RetrievedChunk] = []
        for i, cid in enumerate(ids):
            score = 1.0 - dists[i] if dists[i] is not None else 0.0
            meta = metas[i] if metas else {}
            chunk_data = RetrievedChunk(
                document_id=meta.get("document_id", "desconhecido"),
                chunk_id=cid,
                text=docs[i],
                score=score,
                metadata=meta,
            )
            chunks.append(chunk_data)
            logger.debug(f"Chunk recuperado: ID={cid}, Score={score:.4f}")

        logger.debug(f"Total de {len(chunks)} chunks relevantes recuperados.")
        return chunks

    async def analyze_stroke_location(
        self, clinical_question: str, top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Pipeline completo: busca, síntese e retorno da localização neurológica.
        Retorna a imagem separadamente para facilitar a exibição.
        """
        retrieved = await self.retrieve_relevant_chunks(clinical_question, top_k)
        
        # Gerar resposta com o LLM
        llm_response = await self._synthesize_answer(clinical_question, retrieved)
        if not llm_response:
            llm_response = "Erro ao gerar resposta de localização neurológica com o modelo LLM."
            return {
                "query": clinical_question,
                "answer": llm_response,
                "retrieved_chunks": retrieved,
                "image": None
            }
        
        # Extrair imagem da resposta, se houver
        image_path = None
        image_name = None
        
        import re
        image_match = re.search(r'Imagem: (.*?)\.png', llm_response)
        if image_match:
            image_name = f"{image_match.group(1)}.png"
            # Caminho completo para a imagem
            image_path = os.path.join("images", image_name)
            
            # Remover a linha da imagem da resposta para separá-la
            llm_response = re.sub(r'Imagem: .*?\.png\n', '', llm_response)
        
        return {
            "query": clinical_question,
            "answer": llm_response,
            "retrieved_chunks": retrieved,
            "image": {
                "name": image_name,
                "path": image_path
            } if image_name else None
        }


# --------------------------------------------------------------------- #
# ---------------- FASTAPI DEPENDENCY – SINGLETON STYLE ---------------- #
# --------------------------------------------------------------------- #

_rag_service_instance: Optional[RAGService] = None


def get_rag_service(
    vector_store: VectorStoreService = Depends(get_vector_store_service),
) -> RAGService:
    """Dependency que devolve singleton de RAGService."""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService(vector_store=vector_store)
    return _rag_service_instance
