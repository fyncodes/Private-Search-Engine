import { useState } from "react";

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  score: number;
  document_type: string;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  count: number;
  search_time_ms: number;
}

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem("private-search-theme");
    // Dark mode is the default
    return savedTheme !== "light";
  });
  const [documentType, setDocumentType] = useState("all");
  const [page, setPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);

  async function performSearch(type = documentType) {
    const searchQuery = query.trim();

    if (!searchQuery) {
      setResults([]);
      setStatus("Enter something to search.");
      return;
    }

    setLoading(true);
    setStatus("");
    setResults([]);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/search-hybrid?q=${encodeURIComponent(
          searchQuery
        )}&limit=10&document_type=${type}&page=${page}`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: SearchResponse = await response.json();

      setResults(data.results);
      setHasNextPage(data.count === 10);

      if (data.count === 0) {
        setStatus(`No results for "${data.query}"`);
      } else {
        setStatus(
          `${data.count} result(s) for "${data.query}" · ${data.search_time_ms} ms`
        );
      }
    } catch (error) {
      console.error("Search error:", error);

      setStatus(
        "Could not connect to the search server."
      );
    } finally {
      setLoading(false);
    }
  }

  function changeDocumentType(type: string) {
    setDocumentType(type);

    if (query.trim()) {
      performSearch(type);
    }
  }

  function clearSearch() {
    setQuery("");
    setResults([]);
    setStatus("");
  }

  function startNewSearch(type = documentType) {
    setPage(1);

    if (query.trim()) {
      setTimeout(() => performSearch(type), 0);
    }
  }

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLInputElement>
  ) {
    if (event.key === "Enter") {
      startNewSearch(documentType);
    }
  }

  function highlightText(
    text: string,
    searchQuery: string
  ) {
    if (!searchQuery) {
      return text;
    }

    const stopWords = new Set([
      "a",
      "an",
      "the",
      "to",
      "of",
      "in",
      "on",
      "for",
      "and",
      "or",
      "how",
      "is",
      "are",
      "was",
      "were",
      "with",
      "from",
      "by"
    ]);

    const words = searchQuery
      .toLowerCase()
      .split(/\s+/)
      .filter(
        (word) =>
          word &&
          !stopWords.has(word)
      );

    const pattern = new RegExp(
      `(${words
        .map((word) =>
          word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
        )
        .join("|")})`,
      "gi"
    );

    const parts = text.split(pattern);

    return parts.map((part, index) => {
      const isMatch = words.some(
        (word) => part.toLowerCase() === word
      );

      if (isMatch) {
        return <mark key={index}>{part}</mark>;
      }

      return part;
    });
  }

  return (
    <div className={darkMode ? "app dark" : "app"}>

      <header className="header">
        <div className="brand">
          🔎 Private Search
        </div>

        <button
          className="theme-button"
          onClick={() => {
            const newDarkMode = !darkMode;

            setDarkMode(newDarkMode);

            localStorage.setItem(
              "private-search-theme",
              newDarkMode ? "dark" : "light"
            );
          }}
          title="Toggle dark mode"
        >
          {darkMode ? "☀️" : "🌙"}
        </button>

      </header>

      <main className="container">

        <section className="hero">
          <h1>Search privately.</h1>

          <p>
            Search your own indexed web.
          </p>

          <div className="search-box">

            <input
              type="text"
              value={query}
              onChange={(event) =>
                setQuery(event.target.value)
              }

              onKeyDown={handleKeyDown}
              placeholder="Search the private index..."
              autoFocus
            />

            {query && (
              <button
                className="clear-button"
                onClick={clearSearch}
                title="Clear search"
              >
                ✕
              </button>
          )}

          <button
            className="search-button"
            onClick={() => startNewSearch()}
          >
            🔍
          </button>

          </div>

          <div className="filters">
            <button
              className={documentType === "all" ? "filter active" : "filter"}
              onClick={() => changeDocumentType("all")}
            >
              All
            </button>

            <button
              className={documentType === "html" ? "filter active" : "filter"}
              onClick={() => changeDocumentType("html")}
            >
              🌐 Web
            </button>

            <button
              className={documentType === "pdf" ? "filter active" : "filter"}
              onClick={() => changeDocumentType("pdf")}
            >
              📄 PDF
            </button>
          </div>

          <div className="shortcut">
            Press <kbd>Enter</kbd> to search
          </div>

        </section>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <span>Searching...</span>
          </div>
        )}

        {status && !loading && (
          <div className="status">
            {status}
          </div>
        )}

        <section className="results">

          {results.length === 0 && status && !loading && (
            <div className="empty">
              <div className="empty-icon">🔍</div>

              <h2>No matching pages found</h2>

              <p>
                Try searching with different keywords.
              </p>
            </div>
          )}

          {results.map((result, index) => (
            <article
              className="result"
              key={`${result.url}-${index}`}
            >
              <div className="document-type">
                {result.document_type === "pdf" ? "📄 PDF" : "🌐 WEB"}
              </div>

              <h2 className="result-title">
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {result.title || result.url}
                </a>
              </h2>

              <div className="result-url">
                {result.url}
              </div>

              <p className="result-snippet">
                {highlightText(
                  result.snippet,
                  query
                )}
              </p>

            </article>
          ))}

        </section>

        {results.length > 0 && (
          <div className="pagination">
            <button
              onClick={() => {
                if (page > 1) {
                  setPage(page - 1);
                  setTimeout(() => performSearch(documentType), 0);
                }
              }}
              disabled={page === 1}
            >
              ← Previous
            </button>
            <span>
              Page {page} · Showing {(page - 1) * 10 + 1}–
              {(page - 1) * 10 + results.length}
            </span>
            <button
              onClick={() => {
                setPage(page + 1);
                setTimeout(() => performSearch(documentType), 0);
              }}
              disabled={!hasNextPage}
            >
              Next →
            </button>
          </div>
        )}

      </main>

      <footer className="footer">
        <span>Private Search Engine</span>
        <span>Running locally on your machine</span>
      </footer>

    </div>
  );
}

export default App;