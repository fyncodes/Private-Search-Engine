import numpy as np

from search import SearchEngine
from semantic_search import SemanticSearch


class HybridSearch:
    def __init__(self):
        print("Initializing hybrid search...")

        self.keyword_search = SearchEngine()
        self.semantic_search = SemanticSearch()

    def search(self, query, limit=10):
        keyword_results = self.keyword_search.search(
            query,
            limit=len(self.keyword_search.documents)
        )

        semantic_results = self.semantic_search.search(
            query,
            limit=len(self.semantic_search.documents)
        )

        if not keyword_results and not semantic_results:
            return []

        # Collect all documents
        documents = {}

        for result in keyword_results:
            documents[result["url"]] = {
                "title": result["title"],
                "url": result["url"],
                "keyword_score": result["score"],
                "semantic_score": 0,
                "document_type": result.get("document_type", "html")
            }

        for result in semantic_results:
            if result["url"] not in documents:
                documents[result["url"]] = {
                    "title": result["title"],
                    "url": result["url"],
                    "keyword_score": 0,
                    "semantic_score": result["score"],
                    "document_type": result.get("document_type", "html")
                }
            else:
                documents[result["url"]]["semantic_score"] = (
                    result["score"]
                )

        # Get score arrays
        keyword_scores = np.array([
            item["keyword_score"]
            for item in documents.values()
        ], dtype=float)

        semantic_scores = np.array([
            item["semantic_score"]
            for item in documents.values()
        ], dtype=float)

        # Normalize keyword scores
        if keyword_scores.max() > keyword_scores.min():
            keyword_normalized = (
                (keyword_scores - keyword_scores.min())
                / (keyword_scores.max() - keyword_scores.min())
            )
        else:
            keyword_normalized = np.zeros_like(keyword_scores)

        # Normalize semantic scores
        if semantic_scores.max() > semantic_scores.min():
            semantic_normalized = (
                (semantic_scores - semantic_scores.min())
                / (semantic_scores.max() - semantic_scores.min())
            )
        else:
            semantic_normalized = np.zeros_like(semantic_scores)

        # Combine scores
        hybrid_scores = (
            0.4 * keyword_normalized
            + 0.6 * semantic_normalized
        )

        # ------------------------------------------
        # QUERY-AWARE RANKING
        # ------------------------------------------

        query_tokens = self.keyword_search.tokenize(
            query
        )

        normalized_query = query.strip().lower()

        exact_phrase_bonus = np.zeros(
            len(documents),
            dtype=float
        )

        for index, item in enumerate(documents.values()):

            for document in self.keyword_search.documents:

                if document["url"] == item["url"]:

                    title = str(
                        document["title"] or ""
                    ).lower()

                    content = str(
                        document["content"] or ""
                    ).lower()

                    # Strong boost when the complete
                    # query appears in the title
                    if normalized_query in title:

                        exact_phrase_bonus[index] = 0.30

                    # Smaller boost when the complete
                    # query appears in the content
                    elif normalized_query in content:

                        exact_phrase_bonus[index] = 0.20

                    break

        hybrid_scores = (
            hybrid_scores
            + exact_phrase_bonus
        )
        # If an exact phrase match exists,
        # slightly demote documents without that phrase.
        if np.any(exact_phrase_bonus > 0):

            no_exact_phrase = (
                exact_phrase_bonus == 0
            )

            hybrid_scores = np.where(
                no_exact_phrase,
                hybrid_scores - 0.15,
                hybrid_scores
            )

        # For multi-word queries, slightly penalize documents
        # that have no keyword match at all.

        if len(query_tokens) > 1:

            no_keyword_match = (
                keyword_scores == 0
            )

            hybrid_scores = np.where(
                no_keyword_match,
                hybrid_scores - 0.15,
                hybrid_scores
            )

        # Add final scores
        for index, item in enumerate(documents.values()):
            item["score"] = round(
            float(hybrid_scores[index]),
            4
        )

        # Add snippet for the React frontend
        for document in self.keyword_search.documents:
            if document["url"] == item["url"]:
                content = str(document["content"] or "")
                query_tokens = self.keyword_search.tokenize(query)

                item["snippet"] = (
                    self.keyword_search.create_snippet(
                        content,
                        query_tokens
                    )
                )

            break
        
        # Sort by hybrid score
        ranked_results = sorted(
            documents.values(),
            key=lambda item: item["score"],
            reverse=True
        )

        final_results = []

        for item in ranked_results[:limit]:

            for document in self.keyword_search.documents:
                if document["url"] == item["url"]:
                    content = str(
                        document["content"] or ""
                    )

                    query_tokens = (
                        self.keyword_search.tokenize(query)
                    )

                    item["snippet"] = (
                        self.keyword_search.create_snippet(
                            content,
                            query_tokens
                        )
                    )

                    break

            final_results.append(item)

        return final_results

if __name__ == "__main__":
    engine = HybridSearch()

    results = engine.search(
        "how to create a class",
        limit=5
    )

    for result in results:
        print(result)