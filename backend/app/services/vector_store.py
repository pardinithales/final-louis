# Arquivo app/services/vector_store.py

import logging
from typing import List, Dict, Any, Optional
import chromadb # type: ignore
from chromadb.utils import embedding_functions # type: ignore
import time
import os
from fastapi import HTTPException

from backend.app.core.config import settings

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Configuração básica do logging para este módulo
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Serviço para interagir com o banco de dados vetorial ChromaDB.
    Gerencia a conexão, criação/obtenção de coleções e operações CRUD de vetores.
    """
    _client: Optional[chromadb.PersistentClient] = None
    _collection: Optional[chromadb.Collection] = None
    _embedding_function: Optional[embedding_functions.SentenceTransformerEmbeddingFunction] = None

    def __init__(
        self,
        db_path: str = settings.CHROMA_PERSIST_DIRECTORY,
        collection_name: str = settings.CHROMA_COLLECTION_NAME,
        embedding_model_name: str = settings.EMBEDDING_MODEL_NAME,
    ):
        """
        Inicializa o serviço, garantindo que o cliente e a coleção estejam prontos.

        Args:
            db_path: Caminho para o diretório de persistência do ChromaDB.
            collection_name: Nome da coleção a ser usada.
            embedding_model_name: Nome do modelo de embedding a ser usado pelo ChromaDB
                                   (se não for fornecer embeddings pré-calculados).
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        self._initialize_client()
        self._initialize_embedding_function()
        self._initialize_collection()

    def _initialize_client(self):
        """Inicializa o cliente ChromaDB de forma segura (singleton pattern)."""
        if VectorStoreService._client is None:
            logger.info(f"Inicializando cliente ChromaDB persistente em: {self.db_path}")
            # Garante que o diretório exista antes de inicializar
            os.makedirs(self.db_path, exist_ok=True)
            try:
                VectorStoreService._client = chromadb.PersistentClient(path=self.db_path)
                # Tenta uma operação simples para verificar a conexão/estado
                VectorStoreService._client.heartbeat()
                logger.info("Cliente ChromaDB inicializado e conectado com sucesso.")
            except Exception as e:
                logger.exception(f"Falha ao inicializar o cliente ChromaDB em {self.db_path}: {e}")
                VectorStoreService._client = None # Garante que não fique em estado inválido
                raise ConnectionError(f"Não foi possível conectar ao ChromaDB em {self.db_path}") from e
        else:
             logger.debug("Reutilizando cliente ChromaDB existente.")


    def _initialize_embedding_function(self):
        """Inicializa a função de embedding (singleton pattern)."""
        # Nota: Esta função só é realmente *necessária* se você deixar o ChromaDB
        # calcular os embeddings (passando `documents` mas não `embeddings` para `add`).
        # Como estamos calculando embeddings no RAGService, ela pode não ser usada diretamente
        # pelo ChromaDB nas operações `add` que faremos, mas é bom tê-la configurada
        # corretamente na coleção para consistência e possíveis usos futuros.
        if VectorStoreService._embedding_function is None:
            logger.info(f"Configurando função de embedding para ChromaDB com modelo: {self.embedding_model_name}")
            try:
                VectorStoreService._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.embedding_model_name
                )
                logger.info("Função de embedding configurada.")
            except Exception as e:
                logger.exception(f"Falha ao configurar a função de embedding '{self.embedding_model_name}': {e}")
                VectorStoreService._embedding_function = None
                # Pode ser um erro não fatal se formos sempre fornecer embeddings pré-calculados
                # raise RuntimeError("Falha ao configurar função de embedding.") from e
        else:
             logger.debug("Reutilizando função de embedding existente.")

    def _initialize_collection(self):
        """Obtém ou cria a coleção no ChromaDB de forma segura (singleton pattern)."""
        if VectorStoreService._collection is None and self._client is not None:
            logger.info(f"Acessando/Criando coleção ChromaDB: {self.collection_name}")
            start_time = time.time()
            try:
                # Usamos get_or_create para simplificar
                VectorStoreService._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=VectorStoreService._embedding_function, # Mesmo se não usada no add, é bom ter
                    metadata={"hnsw:space": "cosine"} # Define a métrica de distância (cosine é comum para embeddings)
                )
                duration = time.time() - start_time
                logger.info(f"Coleção '{self.collection_name}' pronta. (Levou {duration:.2f}s)")
                # Log do número inicial de itens na coleção
                count = self.count_documents()
                logger.info(f"Coleção '{self.collection_name}' contém atualmente {count} itens.")
            except Exception as e:
                logger.exception(f"Falha ao obter/criar a coleção '{self.collection_name}': {e}")
                VectorStoreService._collection = None
                raise ConnectionError(f"Não foi possível acessar/criar a coleção '{self.collection_name}'") from e
        elif self._client is None:
             logger.error("Cliente ChromaDB não inicializado. Impossível obter coleção.")
             raise ConnectionError("Cliente ChromaDB não está disponível.")
        else:
             logger.debug(f"Reutilizando coleção '{self.collection_name}' existente.")


    @property
    def collection(self) -> chromadb.Collection:
        """Retorna a instância da coleção, garantindo que foi inicializada."""
        if self._collection is None:
            logger.error("A coleção ChromaDB não foi inicializada corretamente.")
            # Tenta reinicializar como último recurso
            self._initialize_collection()
            if self._collection is None:
                 raise ConnectionError("Coleção ChromaDB não disponível.")
        return self._collection

    async def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Adiciona documentos (com embeddings pré-calculados) à coleção.
        Usa `upsert` para adicionar ou atualizar se o ID já existir.

        Args:
            ids: Lista de IDs únicos para cada documento/chunk.
            documents: Lista dos textos dos documentos/chunks.
            embeddings: Lista dos vetores de embedding correspondentes.
            metadatas: Lista opcional de metadados para cada documento/chunk.
        """
        if not (len(ids) == len(documents) == len(embeddings)):
            msg = f"Inconsistência nos tamanhos das listas: ids({len(ids)}), documents({len(documents)}), embeddings({len(embeddings)})"
            logger.error(msg)
            raise ValueError(msg)
        if metadatas is not None and len(metadatas) != len(ids):
             msg = f"Inconsistência nos tamanhos das listas: ids({len(ids)}), metadatas({len(metadatas)})"
             logger.error(msg)
             raise ValueError(msg)


        logger.debug(f"Adicionando/Atualizando {len(ids)} documentos na coleção '{self.collection_name}'...")
        start_time = time.time()
        try:
            # Usar upsert é mais seguro pois lida com IDs duplicados (atualiza)
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            duration = time.time() - start_time
            logger.info(f"{len(ids)} documentos adicionados/atualizados em {duration:.2f}s.")
        except Exception as e:
            logger.exception(f"Erro ao adicionar/atualizar documentos na coleção '{self.collection_name}': {e}")
            # Re-lança a exceção para que a camada superior possa tratá-la
            raise

    async def query_documents(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: List[str] = ["metadatas", "documents", "distances"]
    ) -> Dict[str, Any]:
        """
        Realiza uma busca por similaridade na coleção usando embeddings de consulta.

        Args:
            query_embeddings: Lista de embeddings das consultas.
            n_results: Número de resultados a retornar por consulta.
            where: Filtro opcional baseado em metadados. Ex: {"source": "Aula 5"}
            where_document: Filtro opcional baseado no conteúdo do documento. Ex: {"$contains":"FastAPI"}
            include: Quais informações retornar para cada resultado.

        Returns:
            Um dicionário contendo os resultados da busca (ids, documents, metadatas, distances).
        """
        logger.debug(f"Executando query na coleção '{self.collection_name}' com {len(query_embeddings)} embedding(s). N_results={n_results}, Include={include}")
        start_time = time.time()
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=include
            )
            duration = time.time() - start_time
            num_results_found = len(results.get("ids", [[]])[0]) if results else 0
            logger.debug(f"Query executada em {duration:.2f}s. Encontrados {num_results_found} resultados.")
            return results
        except Exception as e:
            logger.exception(f"Erro ao executar query na coleção '{self.collection_name}': {e}")
            # Retorna um dicionário vazio ou lança a exceção
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]} # Estrutura vazia

    def count_documents(self) -> int:
        """Retorna o número total de documentos/chunks na coleção."""
        try:
            count = self.collection.count()
            logger.debug(f"Contagem de documentos na coleção '{self.collection_name}': {count}")
            return count
        except Exception as e:
            logger.exception(f"Erro ao contar documentos na coleção '{self.collection_name}': {e}")
            return -1 # Indica erro

    def delete_documents(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None):
        """
        Remove documentos da coleção por IDs ou filtro de metadados.

        Args:
            ids: Lista de IDs a serem removidos.
            where: Filtro de metadados para selecionar documentos a serem removidos.
                   Use com CUIDADO, pode remover muitos dados.
        """
        if not ids and not where:
             logger.warning("Tentativa de deletar documentos sem especificar IDs ou filtro 'where'.")
             raise ValueError("É necessário fornecer 'ids' ou 'where' para deletar documentos.")

        logger.warning(f"Solicitação para deletar documentos da coleção '{self.collection_name}'. IDs: {ids}, Where: {where}")
        try:
            self.collection.delete(ids=ids, where=where)
            logger.info(f"Documentos deletados com sucesso (critério: IDs={bool(ids)}, Where={bool(where)}).")
        except Exception as e:
            logger.exception(f"Erro ao deletar documentos da coleção '{self.collection_name}': {e}")
            raise

# --- Função de Dependência (FastAPI) ---

# Cache da instância do serviço para reutilização nas requests
_vector_store_instance: Optional[VectorStoreService] = None

def get_vector_store_service() -> VectorStoreService:
    """
    Função de dependência FastAPI para obter uma instância singleton do VectorStoreService.
    Garante que a inicialização ocorra apenas uma vez.
    """
    global _vector_store_instance
    # Em um ambiente assíncrono concorrido, um asyncio.Lock seria mais robusto aqui
    
    # Forçar recriação da instância para usar novas configurações
    if _vector_store_instance is not None:
        logger.info("Recriando instância do VectorStoreService para usar novas configurações...")
        _vector_store_instance = None
        
    if _vector_store_instance is None:
        logger.info("Criando instância singleton do VectorStoreService...")
        try:
            _vector_store_instance = VectorStoreService()
            logger.info("Instância do VectorStoreService criada com sucesso.")
        except (ConnectionError, RuntimeError, Exception) as e:
             logger.exception("Falha crítica ao inicializar o VectorStoreService na primeira chamada!")
             # Decide se lança um erro 500 ou permite que a app continue degradada
             raise HTTPException(status_code=503, detail=f"Serviço de banco de vetores indisponível: {e}") from e
    else:
         logger.debug("Reutilizando instância existente do VectorStoreService.")

    # Verificação rápida do estado da coleção antes de retornar
    if _vector_store_instance._collection is None:
         logger.error("Instância do VectorStoreService existe, mas a coleção não está inicializada!")
         # Tenta reinicializar
         try:
             _vector_store_instance._initialize_collection()
             if _vector_store_instance._collection is None:
                  raise ConnectionError("Falha ao reinicializar coleção.")
         except Exception as e:
              raise HTTPException(status_code=503, detail=f"Coleção do banco de vetores indisponível: {e}") from e

    return _vector_store_instance
