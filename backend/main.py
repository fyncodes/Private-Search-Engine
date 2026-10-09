import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import initialize_database
from crawler import crawl
from search import SearchEngine
from semantic_search import SemanticSearch
from hybrid_search import HybridSearch


app = FastAPI(
    title="Private Search Engine"
)


# --------------------------------------------------
# CORS
# Allows our frontend to communicate with FastAPI
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# --------------------------------------------------
# Initialize database
# --------------------------------------------------

initialize_database()

# --------------------------------------------------
# Create search engine
# --------------------------------------------------

search_engine = SearchEngine()
semantic_search_engine = SemanticSearch()
hybrid_search_engine = HybridSearch()

# --------------------------------------------------
# Home
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "Private Search Engine is running!"
    }


# --------------------------------------------------
# Status
# --------------------------------------------------

@app.get("/status")
def status():

    return {

        "status": "online",

        "database": "connected",

        "documents": len(
            search_engine.documents
        )

    }


# --------------------------------------------------
# Crawl website
# --------------------------------------------------

@app.get("/crawl")
def crawl_website(
    url: str,
    max_pages: int = 10
):
    global semantic_search_engine
    global hybrid_search_engine

    pages = crawl(
        url,
        max_pages
    )

    # Rebuild keyword search index
    search_engine.rebuild()

    # Rebuild semantic search index
    semantic_search_engine = SemanticSearch()

    # Rebuild hybrid search index
    hybrid_search_engine = HybridSearch()

    return {
        "success": True,
        "pages_crawled": pages,
        "total_documents": len(
            search_engine.documents
        )
    }

# --------------------------------------------------
# Search
# --------------------------------------------------

@app.get("/search")
def search(
    q: str,
    limit: int = 10
):

    start_time = time.perf_counter()


    results = search_engine.search(
        q,
        limit
    )


    end_time = time.perf_counter()


    search_time = (
        end_time - start_time
    )


    return {

        "query": q,

        "results": results,

        "count": len(results),

        "search_time_ms": round(
            search_time * 1000,
            2
        )

    }

@app.get("/semantic-search")
def semantic_search(
    q: str,
    limit: int = 10
):
    results = semantic_search_engine.search(
        q,
        limit
    )

    return {
        "query": q,
        "results": results,
        "count": len(results)
    }

@app.get("/search-hybrid")
def search_hybrid(
    q: str,
    limit: int = 10,
    document_type: str = "all",
    page: int = 1
):
    start_time = time.perf_counter()

    results = hybrid_search_engine.search(
    q,
    limit * 10
    )

    end_time = time.perf_counter()

    search_time_ms = round(
        (end_time - start_time) * 1000,
        2
    )

    if document_type != "all":
        results = [
            result
            for result in results
            if result.get("document_type") == document_type
        ]

    start_index = (page - 1) * limit
    end_index = start_index + limit

    results = results[start_index:end_index]

    return {
        "query": q,
        "results": results,
        "count": len(results),
        "search_time_ms": search_time_ms
    }