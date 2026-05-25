import os

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

DB_PATH = "vector_db"

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def create_vector_db():

    documents = []

    kb_path = "knowledge_base"

    for file in os.listdir(kb_path):

        file_path = f"{kb_path}/{file}"

        # TXT FILES
        if file.endswith(".txt"):

            print(f"Loading TXT file: {file}")

            loader = TextLoader(file_path)

            documents.extend(loader.load())

        # PDF FILES
        elif file.endswith(".pdf"):

            print(f"Loading PDF file: {file}")

            loader = PyPDFLoader(file_path)

            documents.extend(loader.load())

    print(f"Total documents loaded: {len(documents)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )

    docs = splitter.split_documents(documents)

    print(f"Total chunks created: {len(docs)}")

    vector_db = Chroma.from_documents(
        docs,
        embedding_model,
        persist_directory=DB_PATH
    )

    vector_db.persist()

    print("Vector DB created successfully")


def search_documents(query):

    vector_db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding_model
    )

    results = vector_db.similarity_search(query, k=3)

    return [doc.page_content for doc in results]