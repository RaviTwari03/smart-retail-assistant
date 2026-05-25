# def search_documents(query):
    
#     vector_db = Chroma(
#         persist_directory=DB_PATH,
#         embedding_function=embedding_model
#     )

#     results = vector_db.similarity_search(query, k=3)

#     return [doc.page_content for doc in results]
from services.rag_service import create_vector_db

create_vector_db()