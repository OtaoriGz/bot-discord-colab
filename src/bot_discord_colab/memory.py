import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Tenta importar chromadb para busca vetorial. Se falhar, usa fallback JSON local.
HAS_CHROMADB = False
try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    logger.warning("ChromaDB não está instalado. Usando fallback baseado em JSON para memórias.")

class MemoryManager:
    def __init__(self, persist_dir: str = "memories"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        self.json_path = os.path.join(persist_dir, "memories.json")
        self.chroma_dir = os.path.join(persist_dir, "chromadb_store")
        
        self.client = None
        self.collection = None
        self.json_memories = []
        
        self.initialize()

    def initialize(self):
        """Inicializa o banco vetorial ChromaDB ou carrega memórias do fallback JSON."""
        if HAS_CHROMADB:
            try:
                self.client = chromadb.PersistentClient(path=self.chroma_dir)
                # Cria ou obtém a coleção de memórias do bot
                self.collection = self.client.get_or_create_collection(
                    name="bot_memories",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("ChromaDB inicializado com sucesso.")
                return
            except Exception as e:
                logger.error(f"Erro ao inicializar ChromaDB: {e}. Usando fallback para JSON.")
        
        # Fallback para JSON
        self.load_json_memories()

    def load_json_memories(self):
        """Carrega memórias a partir do arquivo JSON (fallback)."""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "memories" in data:
                        self.json_memories = data["memories"]
                    elif isinstance(data, list):
                        self.json_memories = data
                    else:
                        self.json_memories = []
                logger.info(f"Carregadas {len(self.json_memories)} memórias do fallback JSON.")
            except Exception as e:
                logger.error(f"Erro ao carregar memories.json: {e}")
                self.json_memories = []
        else:
            self.json_memories = []
            self.save_json_memories()

    def save_json_memories(self):
        """Salva a lista atual de memórias no arquivo JSON (fallback)."""
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump({"memories": self.json_memories}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar memories.json: {e}")

    def add_memory(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """Adiciona uma memória ao sistema."""
        if not metadata:
            metadata = {}
        
        # Garante metadados básicos
        import time
        if "timestamp" not in metadata:
            metadata["timestamp"] = int(time.time())
            
        mem_id = f"mem_{int(time.time() * 1000)}"
        
        if HAS_CHROMADB and self.collection is not None:
            try:
                # Converte metadados complexos para tipos suportados pelo ChromaDB (str, int, float, bool)
                clean_metadata = {}
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        clean_metadata[k] = v
                    else:
                        clean_metadata[k] = str(v)
                        
                self.collection.add(
                    documents=[text],
                    metadatas=[clean_metadata],
                    ids=[mem_id]
                )
                logger.info(f"Memória adicionada ao ChromaDB: '{text[:50]}...'")
                return mem_id
            except Exception as e:
                logger.error(f"Falha ao adicionar memória no ChromaDB: {e}. Salvando em JSON.")

        # Armazenamento Fallback JSON
        memory_entry = {
            "id": mem_id,
            "text": text,
            "metadata": metadata
        }
        self.json_memories.append(memory_entry)
        self.save_json_memories()
        logger.info(f"Memória adicionada ao JSON Fallback: '{text[:50]}...'")
        return mem_id

    def recall_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca memórias semanticamente relevantes baseadas no query."""
        if not query or query.strip() == "":
            return []

        if HAS_CHROMADB and self.collection is not None:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                
                memories = []
                if results and "documents" in results and results["documents"]:
                    documents = results["documents"][0]
                    metadatas = results["metadatas"][0] if "metadatas" in results else [{}] * len(documents)
                    ids = results["ids"][0] if "ids" in results else [""] * len(documents)
                    
                    for i in range(len(documents)):
                        memories.append({
                            "id": ids[i],
                            "text": documents[i],
                            "metadata": metadatas[i]
                        })
                return memories
            except Exception as e:
                logger.error(f"Erro ao buscar no ChromaDB: {e}. Usando busca por palavra-chave no JSON.")

        # Fallback JSON: Busca baseada em palavras-chave simples
        words = query.lower().split()
        scored_memories = []
        for mem in self.json_memories:
            text = mem["text"].lower()
            score = sum(1 for word in words if word in text)
            if score > 0:
                scored_memories.append((score, mem))
        
        # Ordena pelo score decrescente
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [mem for score, mem in scored_memories[:limit]]

    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Retorna todas as memórias salvas."""
        if HAS_CHROMADB and self.collection is not None:
            try:
                results = self.collection.get()
                memories = []
                if results and "documents" in results:
                    documents = results["documents"]
                    metadatas = results["metadatas"] if "metadatas" in results else [{}] * len(documents)
                    ids = results["ids"]
                    for i in range(len(documents)):
                        memories.append({
                            "id": ids[i],
                            "text": documents[i],
                            "metadata": metadatas[i]
                        })
                return memories
            except Exception as e:
                logger.error(f"Erro ao obter todas memórias do ChromaDB: {e}")
                
        # Fallback JSON
        return self.json_memories

    def delete_memory(self, mem_id: str) -> bool:
        """Deleta uma memória específica pelo ID."""
        if HAS_CHROMADB and self.collection is not None:
            try:
                self.collection.delete(ids=[mem_id])
                logger.info(f"Memória {mem_id} removida do ChromaDB.")
                return True
            except Exception as e:
                logger.error(f"Erro ao deletar do ChromaDB: {e}")

        # Fallback JSON
        initial_len = len(self.json_memories)
        self.json_memories = [m for m in self.json_memories if m["id"] != mem_id]
        if len(self.json_memories) < initial_len:
            self.save_json_memories()
            logger.info(f"Memória {mem_id} removida do JSON.")
            return True
        return False

    def clear_memories(self):
        """Limpa todas as memórias salvas."""
        if HAS_CHROMADB and self.collection is not None:
            try:
                # Exclui a coleção e recria
                self.client.delete_collection("bot_memories")
                self.collection = self.client.create_collection(
                    name="bot_memories",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("ChromaDB limpo com sucesso.")
            except Exception as e:
                logger.error(f"Erro ao limpar ChromaDB: {e}")
                
        # Limpa também o JSON
        self.json_memories = []
        self.save_json_memories()
        logger.info("JSON de memórias limpo.")

# Instância singleton global do gerenciador de memórias
memory_manager = MemoryManager()
