const API_URL = "http://127.0.0.1:8000";


const searchInput =
    document.getElementById("searchInput");


const searchButton =
    document.getElementById("searchButton");


const clearButton =
    document.getElementById("clearButton");


const resultsContainer =
    document.getElementById("results");


const statusElement =
    document.getElementById("status");


const loadingElement =
    document.getElementById("loading");


const themeButton =
    document.getElementById("themeButton");



/* ==========================================
   SEARCH
========================================== */

async function performSearch() {

    const query =
        searchInput.value.trim();


    if (!query) {

        resultsContainer.innerHTML = "";

        statusElement.textContent =
            "Enter something to search.";

        return;
    }


    // Show loading
    loadingElement.classList.remove(
        "hidden"
    );


    statusElement.textContent = "";


    resultsContainer.innerHTML = "";


    try {

        const url =
            `${API_URL}/search?q=` +
            `${encodeURIComponent(query)}` +
            `&limit=10`;


        const response =
            await fetch(url);


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        displayResults(data);


    } catch (error) {

        console.error(
            "Search error:",
            error
        );


        statusElement.textContent =
            "Could not connect to the search server.";


        resultsContainer.innerHTML = `

            <div class="empty">

                <div class="empty-icon">
                    ⚠️
                </div>

                <div>
                    Make sure FastAPI is running.
                </div>

            </div>

        `;

    } finally {

        loadingElement.classList.add(
            "hidden"
        );

    }

}



/* ==========================================
   DISPLAY RESULTS
========================================== */

function displayResults(data) {

    resultsContainer.innerHTML = "";


    if (data.count === 0) {

        statusElement.textContent =
            `No results for "${data.query}"`;


        resultsContainer.innerHTML = `

            <div class="empty">

                <div class="empty-icon">
                    🔍
                </div>

                <div>
                    No matching pages were found.
                </div>

            </div>

        `;

        return;
    }


    statusElement.textContent =
        `${data.count} result(s) for ` +
        `"${data.query}" · ` +
        `${data.search_time_ms} ms`;


    data.results.forEach(
        (result, index) => {

            const resultElement =
                document.createElement(
                    "article"
                );


            resultElement.className =
                "result";


            /*
             * We create the result elements
             * individually rather than inserting
             * the crawled URL as raw HTML.
             */

            const title =
                document.createElement("h2");

            title.className =
                "result-title";


            const link =
                document.createElement("a");

            link.href =
                result.url;

            link.target =
                "_blank";

            link.rel =
                "noopener noreferrer";

            link.textContent =
                result.title || result.url;


            title.appendChild(link);


            const url =
                document.createElement("div");

            url.className =
                "result-url";

            url.textContent =
                result.url;


            const snippet =
                document.createElement("p");

            snippet.className =
                "result-snippet";


            /*
             * Highlight search terms safely.
             */

            snippet.innerHTML =
                highlightTextSafely(
                    result.snippet,
                    data.query
                );


            resultElement.appendChild(
                title
            );


            resultElement.appendChild(
                url
            );


            resultElement.appendChild(
                snippet
            );


            resultsContainer.appendChild(
                resultElement
            );

        }
    );

}



/* ==========================================
   SAFE HIGHLIGHTING
========================================== */

function highlightTextSafely(
    text,
    query
) {

    if (!text) {

        return "";

    }


    const escapedText =
        escapeHTML(text);


    const tokens =
        query
            .toLowerCase()
            .split(/\s+/)
            .filter(
                token => token.length > 0
            );


    let result =
        escapedText;


    /*
     * Longest words first prevents
     * partial replacement problems.
     */

    tokens.sort(
        (a, b) => b.length - a.length
    );


    for (const token of tokens) {

        const escapedToken =
            escapeRegExp(
                escapeHTML(token)
            );


        const regex =
            new RegExp(
                `\\b(${escapedToken})\\b`,
                "gi"
            );


        result =
            result.replace(
                regex,
                "<mark>$1</mark>"
            );

    }


    return result;

}



/* ==========================================
   HTML ESCAPING
========================================== */

function escapeHTML(value) {

    const div =
        document.createElement("div");


    div.textContent =
        value ?? "";


    return div.innerHTML;

}



/* ==========================================
   REGEX ESCAPING
========================================== */

function escapeRegExp(value) {

    return value.replace(
        /[.*+?^${}()|[\]\\]/g,
        "\\$&"
    );

}



/* ==========================================
   CLEAR SEARCH
========================================== */

function clearSearch() {

    searchInput.value = "";

    clearButton.classList.add(
        "hidden"
    );

    statusElement.textContent = "";

    resultsContainer.innerHTML = "";

    searchInput.focus();

}



/* ==========================================
   INPUT CHANGE
========================================== */

searchInput.addEventListener(
    "input",
    function() {

        if (
            searchInput.value.trim()
        ) {

            clearButton.classList.remove(
                "hidden"
            );

        } else {

            clearButton.classList.add(
                "hidden"
            );

        }

    }
);



/* ==========================================
   BUTTON EVENTS
========================================== */

searchButton.addEventListener(
    "click",
    performSearch
);


clearButton.addEventListener(
    "click",
    clearSearch
);



/* ==========================================
   KEYBOARD EVENTS
========================================== */

searchInput.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter"
        ) {

            performSearch();

        }


        if (
            event.key === "Escape"
        ) {

            clearSearch();

        }

    }
);



/* ==========================================
   DARK MODE
========================================== */

function toggleTheme() {

    document.body.classList.toggle(
        "dark"
    );


    const darkMode =
        document.body.classList.contains(
            "dark"
        );


    if (darkMode) {

        themeButton.textContent = "☀️";

        localStorage.setItem(
            "theme",
            "dark"
        );

    } else {

        themeButton.textContent = "🌙";

        localStorage.setItem(
            "theme",
            "light"
        );

    }

}


themeButton.addEventListener(
    "click",
    toggleTheme
);



/* ==========================================
   LOAD SAVED THEME
========================================== */

const savedTheme =
    localStorage.getItem(
        "theme"
    );


if (savedTheme === "dark") {

    document.body.classList.add(
        "dark"
    );

    themeButton.textContent = "☀️";

}