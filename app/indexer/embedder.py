import os
import sys
import uuid
from qdrant_client import QdrantClient

# Add root dir to path so we can import the parser
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.indexer.parser import CodeParser

class CodeEmbedder:
    def __init__(self, collection_name="pr_review_codebase"):
        # Read from .env, fallback to localhost if not found
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
        
        # Connect to Qdrant (Cloud or Local)
        self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        self.collection_name = collection_name
        
        self.client.set_model("BAAI/bge-small-en-v1.5")
        
        if not self.client.collection_exists(self.collection_name):
            print(f"Creating Qdrant collection: {self.collection_name}...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=self.client.get_fastembed_vector_params()
            )

    def embed_and_store(self, chunks: list[str], file_path: str):
        """Takes code chunks, embeds them locally, and saves to Qdrant."""
        if not chunks:
            return
        
        # Create metadata so we know exactly which file the chunk came from
        metadata =[{"file_path": file_path, "chunk_index": i} for i in range(len(chunks))]
        
        # Generate unique IDs for the database
        ids = [uuid.uuid4().hex for _ in chunks]

        print(f"Embedding and saving {len(chunks)} chunks to Qdrant...")
        
        # client.add() automatically converts the text to vectors using FastEmbed!
        self.client.add(
            collection_name=self.collection_name,
            documents=chunks,
            metadata=metadata,
            ids=ids
        )
        print("Successfully saved to database!\n")

    def search_similar_code(self, query: str, limit: int = 5):
        """Searches the database for code with similar semantic meaning."""
        print(f"Searching Qdrant for: '{query}'...")
        results = self.client.query(
            collection_name=self.collection_name,
            query_text=query,
            limit=limit
        )
        return results

# ==========================================
# PHASE 2 SUCCESS CHECK (TEST BLOCK)
# ==========================================
if __name__ == "__main__":
    # 1. We start with the same sample code
    sample_code = b"""
    function calculateTotal(price: number, tax: number): number {
        return price + tax;
    }

    class User {
        getUserData(id: string) {
            console.log("Fetching user...");
            return { id: id, name: "Thanvitha" };
        }
    }
    """

    # 2. Parse it using your bulletproof AST Walker
    parser = CodeParser()
    chunks = parser.extract_functions(sample_code)

    # 3. Initialize Qdrant connection
    embedder = CodeEmbedder()

    # 4. Embed the chunks and save them to the database
    embedder.embed_and_store(chunks, file_path="src/sample.ts")

    # 5. THE SUCCESS CHECK: Ask a question in plain English, and watch Qdrant find the code!
    search_query = "How is the total price and tax calculated?"
    
    results = embedder.search_similar_code(query=search_query, limit=1)

    print("-" * 50)
    print("VECTOR SEARCH RESULT:")
    for res in results:
        # The 'document' holds the raw code chunk, 'metadata' holds the file path
        print(f"File: {res.metadata['file_path']}")
        print(f"Score: {res.score:.4f} (Higher means more relevant)")
        print(f"Code:\n{res.document}")
    print("-" * 50)