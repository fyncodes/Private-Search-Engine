import queue
import time
import requests
import fitz

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree
from database import save_document

# Identify our crawler
HEADERS = {
    "User-Agent": "PrivateSearchEngine/1.0"
}

def normalize_url(url):
    parsed = urlparse(url)

    # Remove fragment (#section)
    clean_url = parsed._replace(
        fragment=""
    ).geturl()

    # Remove trailing slash
    # This makes:
    # https://example.com/
    # and
    # https://example.com
    # the same URL.
    if clean_url.endswith("/"):
        clean_url = clean_url.rstrip("/")

    return clean_url

def create_robot_parser(start_url):
    parsed_url = urlparse(start_url)

    robots_url = (
        f"{parsed_url.scheme}://"
        f"{parsed_url.netloc}/robots.txt"
    )

    robot_parser = RobotFileParser()
    robot_parser.set_url(robots_url)

    try:
        robot_parser.read()
        print(f"Loaded robots.txt: {robots_url}")

    except Exception:
        print(
            "Could not load robots.txt. "
            "Continuing without robots restrictions."
        )

        # If robots.txt cannot be reached,
        # allow crawling instead of blocking everything.
        robot_parser.parse([
            "User-agent: *",
            "Disallow:"
        ])

    return robot_parser

def get_sitemap_urls(start_url):
    parsed_url = urlparse(start_url)

    sitemap_url = (
        f"{parsed_url.scheme}://"
        f"{parsed_url.netloc}/sitemap.xml"
    )

    try:
        response = requests.get(
            sitemap_url,
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:
            print("No sitemap found.")
            return []

        root = ElementTree.fromstring(response.content)

        urls = []

        for element in root.iter():
            if element.tag.endswith("loc"):
                url = element.text.strip()

                if url:
                    urls.append(normalize_url(url))

        print(f"Sitemap found: {len(urls)} URLs")

        return urls

    except Exception as error:
        print(f"Sitemap error: {error}")
        return []

def extract_text(soup):
    for element in soup([
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav",
        "aside",
        "form"
    ]):
        element.decompose()

    text = soup.get_text(" ", strip=True)

    # Remove excessive whitespace
    text = " ".join(text.split())

    return text

def extract_pdf_text(pdf_data):
    text = ""

    try:
        pdf = fitz.open(
            stream=pdf_data,
            filetype="pdf"
        )

        for page in pdf:
            text += page.get_text()

        pdf.close()

    except Exception as error:
        print(f"PDF extraction error: {error}")

    return " ".join(text.split())

def crawl(start_url, max_pages=10):
    start_url = normalize_url(start_url)
    robot_parser = create_robot_parser(start_url)
    """
    Crawl a website and save pages
    into our database.
    """

    # Pages we have already visited
    visited = set()

    start_domain = urlparse(start_url).netloc
    # Pages waiting to be crawled
    queue = deque()

    # Always start with the original URL
    queue.append(start_url)

    # Add URLs from sitemap if available
    sitemap_urls = get_sitemap_urls(start_url)

    for sitemap_url in sitemap_urls:

        if urlparse(sitemap_url).netloc == start_domain:

            queue.append(sitemap_url)

    pages_crawled = 0

    # Find the domain we started with
    start_domain = urlparse(
        start_url
    ).netloc

    pages_crawled = 0

    while queue and pages_crawled < max_pages:

        # Get next URL
        url = queue.popleft()

        # Don't visit the same page twice
        if url in visited:
            continue

        if not robot_parser.can_fetch(
            HEADERS["User-Agent"],
            url
        ):
            print(f"Blocked by robots.txt: {url}")
            visited.add(url)
            continue

        visited.add(url)

        print(f"Crawling: {url}")

        try:

            # Download webpage
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=10
            )
            time.sleep(1)

            # Ignore unsuccessful requests
            if response.status_code != 200:
                print(
                    f"Skipped: HTTP {response.status_code}"
                )

                continue

            # Make sure it is HTML
            content_type = response.headers.get(
                "content-type",
                ""
            ).lower()

            # Handle PDF files
            if (
                "application/pdf" in content_type
                or url.lower().endswith(".pdf")
            ):
                text = extract_pdf_text(
                    response.content
                )

                print(f"PDF text length: {len(text)}")
                print(f"PDF text: {text}")

                title = url.split("/")[-1]

                if len(text) > 0:
                    save_result = save_document(
                        url,
                        title,
                        text,
                        "pdf"
                    )

                    if save_result == "new":
                        pages_crawled += 1
                        print(f"New PDF: {title}")

                    elif save_result == "updated":
                        pages_crawled += 1
                        print(f"Updated PDF: {title}")

                    elif save_result == "unchanged":
                        print(f"Unchanged PDF: {title}")

                continue

            # Handle normal HTML pages
            if "text/html" not in content_type:
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            # Extract title
            if soup.title and soup.title.string:

                title = soup.title.string.strip()

            else:

                title = url

            # Extract readable text
            text = extract_text(soup)

            # Save useful pages
            if len(text) > 100:
                save_result = save_document(
                    url,
                    title,
                    text
                )

                if save_result == "new":
                    pages_crawled += 1
                    print(f"New page: {title}")

                elif save_result == "updated":
                    pages_crawled += 1
                    print(f"Updated page: {title}")

                elif save_result == "unchanged":
                    print(f"Unchanged: {title}")

            # Find links
            for link in soup.find_all(
                "a",
                href=True
            ):

                next_url = urljoin(
                    url,
                    link["href"]
                )

                next_url = normalize_url(next_url)

                parsed_url = urlparse(
                    next_url
                )

                # Only crawl the same website
                if parsed_url.netloc == start_domain:

                    # Remove #section
                    next_url = next_url.split(
                        "#"
                    )[0]

                    if next_url not in visited:

                        queue.append(
                            next_url
                        )

        except requests.RequestException as error:

            print(
                f"Request error: {error}"
            )

        except Exception as error:

            print(
                f"Unexpected error: {error}"
            )

    print()
    print(
        f"Crawling finished. "
        f"Pages saved: {pages_crawled}"
    )

    return pages_crawled