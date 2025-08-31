import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from index import handle_inverted_index_and_tf_idf
from utils.clean import clean_text
from utils.config import config
from utils.logger import pretty_logger

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/public", StaticFiles(directory="public"), name="public")


@app.get("/")
async def serve_html():
    html_file = os.path.join("public", "index.html")

    return FileResponse(html_file)


@app.get("/search")
def read_item(query: str = "", page: int = 1, size: int = 30):
    try:
        pretty_logger(f"q{query}")
        result = search(query=query)

        start = (page - 1) * size
        end = start + size
        total_data = result["totalData"]
        paginated = result["data"][start:end]

        return {
            "results": paginated,
            "page": page,
            "size": size,
            "totalData": total_data,
            "totalPages": max((total_data + size - 1) // size, 1),
        }
    except Exception as e:
        return {"error": str(e)}


def search(query: str = ""):
    """Perform TF-IDF + cosine similarity search."""
    scrap_result = []
    with open(f"{config.output_dir}/{config.pubs_file}", "r") as f:
        scrap_result = json.load(f)

    total_data = len(scrap_result)

    pretty_logger(query, "query")

    # No query → return all
    if not query.strip():
        return {"data": list(scrap_result), "totalData": total_data}

    list_inverted_index, tfidf_matrix, vectorizer = handle_inverted_index_and_tf_idf()

    # Preprocess query
    processed_query = clean_text(query.strip().lower())
    query_terms = processed_query.split()

    # Find candidate docs via inverted index
    relevant_docs = set()
    for term in query_terms:
        if term in list_inverted_index:
            relevant_docs.update(list_inverted_index[term])

    if not relevant_docs:
        return {"data": [], "totalData": 0}

    relevant_docs = list(relevant_docs)

    # pretty_logger(publication_list_after_stem)

    # Compute similarity only on candidates

    tfidf_query = vectorizer.transform([processed_query])
    cosine_similarities = cosine_similarity(tfidf_query, tfidf_matrix[relevant_docs])

    # Sort by similarity
    sorted_docs = sorted(
        zip(relevant_docs, cosine_similarities[0]), key=lambda x: x[1], reverse=True
    )

    pretty_logger(sorted_docs, "test")

    # Fetch results
    data = [scrap_result[idx - 1] for idx, _ in sorted_docs]

    pretty_logger(data, "me")
    return {"data": data, "totalData": len(data)}
