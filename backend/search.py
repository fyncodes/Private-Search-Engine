import re

from rank_bm25 import BM25Okapi

from database import get_documents


class SearchEngine:

    def __init__(self):

        self.documents = []

        self.tokenized_documents = []

        self.bm25 = None

        self.rebuild()


    # --------------------------------------------------
    # TOKENIZER
    # --------------------------------------------------

    def tokenize(self, text):

        return re.findall(
            r"\b[a-zA-Z0-9]+\b",
            text.lower()
        )


    # --------------------------------------------------
    # BUILD SEARCH INDEX
    # --------------------------------------------------

    def rebuild(self):

        print("Building search index...")

        self.documents = get_documents()

        self.tokenized_documents = []


        for document in self.documents:

            title = str(
                document["title"] or ""
            )

            content = str(
                document["content"] or ""
            )

            # Give title words more importance
            searchable_text = (
                title + " " +
                title + " " +
                title + " " +
                content
            )

            tokens = self.tokenize(
                searchable_text
            )

            self.tokenized_documents.append(
                tokens
            )


        if self.tokenized_documents:

            self.bm25 = BM25Okapi(
                self.tokenized_documents
            )

            print(
                f"Search index ready: "
                f"{len(self.documents)} documents"
            )

        else:

            self.bm25 = None

            print(
                "Search index is empty."
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


        if self.bm25 is None:
            return []


        query = query.strip()


        if not query:
            return []


        query_tokens = self.tokenize(
            query
        )


        if not query_tokens:
            return []


        # ----------------------------------------------
        # BM25 scores
        # ----------------------------------------------

        scores = self.bm25.get_scores(
            query_tokens
        )


        ranked_results = []


        for document, bm25_score in zip(
            self.documents,
            scores
        ):

            title = str(
                document["title"] or ""
            )

            content = str(
                document["content"] or ""
            )


            title_lower = title.lower()

            content_lower = content.lower()


            # ------------------------------------------
            # CHECK MATCHING WORDS
            # ------------------------------------------

            matching_words = 0


            for token in query_tokens:

                if (
                    token in title_lower
                    or
                    token in content_lower
                ):

                    matching_words += 1


            # No query words found
            if matching_words == 0:

                continue


            # ------------------------------------------
            # TITLE BOOST
            # ------------------------------------------

            title_boost = 0


            for token in query_tokens:

                if token in title_lower:

                    title_boost += 8


            # Extra boost when complete query appears
            # in the title
            if query.lower() in title_lower:

                title_boost += 12


            # ------------------------------------------
            # EXACT PHRASE BOOST
            # ------------------------------------------

            phrase_boost = 0

            normalized_query = query.lower()


            # Exact phrase in title
            if normalized_query in title_lower:

                phrase_boost += 20


            # Exact phrase in content
            elif normalized_query in content_lower:
                phrase_boost += 2


            # ------------------------------------------
            # MATCHING WORD BONUS
            # ------------------------------------------

            # Reward documents containing all
            # query words
            all_words_bonus = 0


            if matching_words == len(query_tokens):

                all_words_bonus = 15


            word_match_bonus = (
                matching_words * 2
            )

            # ------------------------------------------
            # FINAL SCORE
            # ------------------------------------------

            final_score = (

                float(bm25_score)
                + title_boost
                + phrase_boost
                + word_match_bonus
                + all_words_bonus
            )

            ranked_results.append(
                (
                    document,
                    final_score
                )
            )

        # ----------------------------------------------
        # SORT
        # ----------------------------------------------

        ranked_results.sort(
            key=lambda item: item[1],
            reverse=True
        )

        # ----------------------------------------------
        # CREATE RESULTS
        # ----------------------------------------------

        results = []

        for document, score in ranked_results:

            content = str(
                document["content"] or ""
            )

            snippet = self.create_snippet(
                content,
                query_tokens
            )

            highlighted_snippet = (
                self.highlight_text(
                    snippet,
                    query_tokens
                )
            )

            results.append({
                "title": document["title"],
                "url": document["url"],
                "snippet": snippet,
                "highlighted_snippet":
                    highlighted_snippet,
                "score": round(score, 2),
                "document_type":
                    document["document_type"]
            })

            if len(results) >= limit:
                break

        return results

    # --------------------------------------------------
    # CREATE SNIPPET
    # --------------------------------------------------

    def create_snippet(
        self,
        content,
        query_tokens,
        length=320
    ):

        content = content.strip()

        if not content:
            return ""

        lower_content = content.lower()

        # ------------------------------------------
        # Try the complete query phrase first
        # ------------------------------------------

        query_phrase = " ".join(query_tokens)

        best_position = -1

        if query_phrase:

            position = lower_content.find(
                query_phrase
            )

            if position != -1:
                best_position = position

        # ------------------------------------------
        # If full phrase is not found,
        # find the first matching word
        # ------------------------------------------

        if best_position == -1:

            for token in query_tokens:

                position = lower_content.find(
                    token
                )

                if position != -1:

                    best_position = position

                    break

        # ------------------------------------------
        # No match
        # ------------------------------------------

        if best_position == -1:

            return content[:length]

        # ------------------------------------------
        # Start before matched text
        # ------------------------------------------

        start = max(
            0,
            best_position - 120
        )

        # ------------------------------------------
        # End after matched text
        # ------------------------------------------

        end = min(
            len(content),
            best_position + length
        )

        snippet = content[start:end]

        if start > 0:
            snippet = "..." + snippet

        if end < len(content):
            snippet += "..."

        return snippet

        content = content.strip()

        if not content:

            return ""

        lower_content = (
            content.lower()
        )

        # Find the first matching word
        best_position = -1


        for token in query_tokens:

            position = (
                lower_content.find(token)
            )

            if position != -1:
                best_position = position
                break


        # No match
        if best_position == -1:

            return content[:length]


        # Start before matched word
        start = max(
            0,
            best_position - 120
        )


        # End after matched word
        end = min(
            len(content),
            best_position + length
        )


        snippet = content[start:end]


        if start > 0:

            snippet = "..." + snippet


        if end < len(content):

            snippet += "..."


        return snippet


    # --------------------------------------------------
    # HIGHLIGHT SEARCH TERMS
    # --------------------------------------------------

    def highlight_text(
        self,
        text,
        query_tokens
    ):

        if not text:

            return ""


        highlighted = text


        # Remove duplicate words
        unique_tokens = list(
            dict.fromkeys(
                query_tokens
            )
        )


        # Longest words first
        unique_tokens.sort(
            key=len,
            reverse=True
        )

        for token in unique_tokens:

            pattern = re.compile(
                rf"\b({re.escape(token)})\b",
                re.IGNORECASE
            )

            highlighted = pattern.sub(
                r"<mark>\1</mark>",
                highlighted
            )

        return highlighted