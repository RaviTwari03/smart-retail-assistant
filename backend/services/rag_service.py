import os

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Chroma

from langchain_huggingface import HuggingFaceEmbeddings


# =========================
# CONFIG
# =========================

DB_PATH = "./vector_db"

KB_PATH = "./knowledge_base"


# =========================
# EMBEDDING MODEL
# =========================

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# =========================
# CREATE VECTOR DATABASE
# =========================

def create_vector_db():

    documents = []

    # Check knowledge base exists
    if not os.path.exists(KB_PATH):

        print(f"Knowledge base folder not found: {KB_PATH}")
        return

    # Load all files
    for file in os.listdir(KB_PATH):

        file_path = os.path.join(KB_PATH, file)

        try:

            # TXT FILES
            if file.endswith(".txt"):

                print(f"Loading TXT file: {file}")

                loader = TextLoader(
                    file_path,
                    encoding="utf-8"
                )

                documents.extend(loader.load())

            # PDF FILES
            elif file.endswith(".pdf"):

                print(f"Loading PDF file: {file}")

                loader = PyPDFLoader(file_path)

                documents.extend(loader.load())

        except Exception as e:

            print(f"Error loading {file}: {e}")

    print(f"Total documents loaded: {len(documents)}")

    # Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )

    docs = splitter.split_documents(documents)

    print(f"Total chunks created: {len(docs)}")

    # Delete old DB if exists
    if os.path.exists(DB_PATH):

        print("Removing old vector DB...")

    # Create vector DB
    vector_db = Chroma.from_documents(
        documents=docs,
        embedding=embedding_model,
        persist_directory=DB_PATH
    )

    print("Vector DB created successfully")


# =========================
# SEARCH DOCUMENTS
# =========================

def search_documents(query):

    try:

        vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embedding_model
        )

        results = vector_db.similarity_search(
            query,
            k=3
        )

        return [
            doc.page_content
            for doc in results
        ]

    except Exception as e:

        print(f"Search Error: {e}")

        return []