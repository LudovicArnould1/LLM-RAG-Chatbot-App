from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import chromadb


def load_documents(input_dir: str,
                   sample_size: int = 50) -> list[Tuple[str, str]]:
    """Load documents from the specified input directory.

    Args:
    ----
        input_dir (str): The directory containing the input text files.
        sample_size (int): The number of files to load from the directory.
        Defaults to 50.

    Returns:
    -------
        List[Tuple[str, str]]: A list of tuples, each containing the content of
        a document and its file name.

    """
    file_names = os.listdir(input_dir)[:sample_size]
    documents = []
    for file_name in file_names:
        file_path = Path(input_dir) / file_name
        with file_path.open(encoding="utf-8") as file:
            content = file.read()
            documents.append((content, file_name))
    return documents

def split_into_chunks(text: str, chunk_size: int = 500,
                      overlap: int = 50) -> list[str]:
    """Split a document into smaller chunks of a given number of characters with overlap.

    Args:
    ----
        text (str): The content of the document.
        chunk_size (int): The maximum number of characters per chunk. Defaults to 500.
        overlap (int): The number of characters to overlap between chunks.
        Defaults to 50.

    Returns:
    -------
        List[str]: A list of text chunks.

    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def main() -> None:
    # Define paths and parameters
    input_dir = "data/wikipedia_articles"
    sample_size = len(os.listdir(input_dir))
    collection_name = "chroma_db"

    # Load and process documents
    documents_tuple = load_documents(input_dir, sample_size=sample_size)

    # Split documents into smaller chunks
    # Small overlap to preserve context
    documents = []
    id_list = []
    for doc_content, doc_id in documents_tuple:
        chunks = split_into_chunks(doc_content, chunk_size=500, overlap=50)
        documents.extend(chunks)
        id_list.extend([f"{doc_id}_chunk_{i}" for i in range(len(chunks))])

    # Add documents to the vector store
    chroma_client = chromadb.PersistentClient(path="data/chroma_db")
    db = chroma_client.create_collection(name=collection_name)
    db.add(documents=documents, ids=id_list)

    # Query the vector store and print the result
    print("A sample query to the vector store:")
    queries = ["Find something about Neural Networks"]
    result = db.query(query_texts=queries, n_results=3)
    print(f"Query: {queries[0]}")
    print(f"Result: {result['documents'][0][0]}")
    print(f"Distance: {result['distances'][0]}")

if __name__ == "__main__":
    main()
