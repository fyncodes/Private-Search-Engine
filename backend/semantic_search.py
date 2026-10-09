from sentence_transformers import SentenceTransformer
from database import get_documents
import numpy as np


class SemanticSearch:

    def __init__(self):

        print("Loading semantic search model...")

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        self.documents = []

        # Each chunk stores:
        # document_index + chunk text
        self.chunks = []

        self.embeddings = None

        self.rebuild()


    # --------------------------------------------------
    # BUILD SEMANTIC INDEX
    # --------------------------------------------------

    def rebuild(self):

        print("Building semantic index...")

        self.documents = get_documents()

        self.chunks = []

        if not self.documents:

            self.embeddings = None

            print(
                "Semantic index is empty."
            )

            return


        # Keep chunks safely below the model's
        # 256-token maximum.
        chunk_size = 160

        overlap = 40


        for document_index, document in enumerate(
            self.documents
        ):

            title = str(
                document["title"] or ""
            )

            content = str(
                document["content"] or ""
            )


            # Include title with every chunk so
            # the document topic is represented.
            words = (title + " " + content).split()

            if not words:

                continue


            start = 0

            while start < len(words):

                end = start + chunk_size

                chunk_words = words[start:end]

                chunk_text = " ".join(
                    chunk_words
                )


                self.chunks.append({
                    "document_index": document_index,
                    "text": chunk_text
                })


                if end >= len(words):

                    break


                start = end - overlap


        if not self.chunks:

            self.embeddings = None

            print(
                "Semantic index is empty."
            )

            return


        texts = [
            chunk["text"]
            for chunk in self.chunks
        ]


        self.embeddings = self.model.encode(
            texts,
            normalize_embeddings=True
        )


        print(
            f"Semantic index ready: "
            f"{len(self.documents)} documents, "
            f"{len(self.chunks)} chunks"
        )


    # --------------------------------------------------
    # SEARCH
    # --------------------------------------------------

    def search(
        self,
        query,
        limit=10
    ):

        if not self.documents:

            return []


        if self.embeddings is None:

            return []


        query = query.strip()


        if not query:

            return []


        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True
        )


        scores = np.dot(
            self.embeddings,
            query_embedding
        )


        # Keep the best matching chunk
        # for each document.
        best_document_scores = {}


        for chunk_index, score in enumerate(
            scores
        ):

            document_index = (
                self.chunks[chunk_index]
                ["document_index"]
            )


            score = float(score)


            if (
                document_index
                not in best_document_scores
            ):

                best_document_scores[
                    document_index
                ] = score

            elif score > best_document_scores[
                document_index
            ]:

                best_document_scores[
                    document_index
                ] = score


        # Rank documents by their best
        # matching semantic chunk.
        ranked_documents = sorted(
            best_document_scores.items(),
            key=lambda item: item[1],
            reverse=True
        )


        results = []


        for document_index, score in (
            ranked_documents[:limit]
        ):

            document = (
                self.documents[
                    document_index
                ]
            )


            results.append({

                "title":
                    document["title"],

                "url":
                    document["url"],

                "score":
                    round(score, 4)

            })


        return results


if __name__ == "__main__":

    engine = SemanticSearch()

    results = engine.search(
        "how to create a class",
        limit=5
    )

    for result in results:

        print(result)