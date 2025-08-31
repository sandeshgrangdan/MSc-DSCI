import time
import re
from typing import List, Dict, Any

# Third-party imports
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Local application imports (assuming structure)
from utils.config import config
from utils.files import FileHandler
from utils.logger import pretty_logger

# --- Constants for Selectors (Improves Readability and Maintenance) ---
PAGINATION_SELECTOR = "nav.pages a.step"
PUB_CONTAINER_SELECTOR = "div.result-container"
PUB_LINK_SELECTOR = "h3.title > a"
AUTHORS_P_SELECTOR = "p.relations.persons"
BIBTEX_TAB_SELECTOR = "#tab-5"
BIBTEX_CONTENT_SELECTOR = "pre.rendering_researchoutput_bibtex"
WAIT_TIMEOUT = 10  # seconds


def _parse_bibtex(bib_str: str) -> Dict[str, str]:
    """Parses a BibTeX string to extract key fields using regex."""
    details = {}
    # This regex handles fields enclosed in "..." or {...}
    fields_to_extract = ["title", "year", "month", "day", "abstract"]
    for field in fields_to_extract:
        # Matches: field = "value" OR field = {value}
        match = re.search(rf"{field}\s*=\s*[\"{{]((?:.|\n)*?)[\"\"}}],", bib_str)
        if match:
            # Remove potential nested curly braces from the value
            details[field] = match.group(1).strip().strip("{}")
    return details


def _scrape_publication_details(driver: WebDriver, pub_url: str) -> Dict[str, Any]:
    """Scrapes authors and BibTeX details from a single publication page."""
    driver.get(pub_url)
    pub_data = {}
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    try:
        # 1. Scrape authors more robustly
        authors_p = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, AUTHORS_P_SELECTOR))
        )
        author_links = authors_p.find_elements(By.TAG_NAME, "a")
        authors_list = [
            {"name": a.text.strip(), "link": a.get_attribute("href")}
            for a in author_links
        ]
        pub_data["authors"] = authors_list

        # 2. Click BibTeX tab and wait for content
        bibtex_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, BIBTEX_TAB_SELECTOR))
        )
        bibtex_tab.click()

        bibtex_pre = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, BIBTEX_CONTENT_SELECTOR))
        )
        bib_str = bibtex_pre.text

        # 3. Parse the BibTeX string
        bibtex_details = _parse_bibtex(bib_str)
        pub_data.update(bibtex_details)

    except (TimeoutException, NoSuchElementException) as e:
        pretty_logger(f"Could not scrape details for {pub_url}. Reason: {e}", "error")

    return pub_data


def get_publications(driver: WebDriver) -> None:
    """
    Scrapes all publications, optimizes for performance and robustness.
    """
    file_handler = FileHandler()
    all_publications_data = []

    # --- 1. Determine Pagination ---
    driver.get(config.pub_link)
    last_page_number = 1
    try:
        pagination_elements = driver.find_elements(By.CSS_SELECTOR, PAGINATION_SELECTOR)
        if pagination_elements:
            last_page_number = int(pagination_elements[-1].text)
            pretty_logger(f"Found {last_page_number} pages of publications.")
    except (NoSuchElementException, ValueError):
        pretty_logger(
            "Pagination not found or invalid. Scraping first page only.",
            "warning",
        )

    # --- 2. Collect all publication links first ---
    publication_links = []
    for i in range(last_page_number):
        page_url = f"{config.pub_link}?page={i}"
        pretty_logger(f"Collecting links from page {i + 1}/{last_page_number}...")
        driver.get(page_url)
        try:
            # Wait for containers to be present before scraping
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, PUB_CONTAINER_SELECTOR)
                )
            )
            pub_elements = driver.find_elements(By.CSS_SELECTOR, PUB_LINK_SELECTOR)
            for el in pub_elements:
                publication_links.append(el.get_attribute("href"))
        except TimeoutException:
            pretty_logger(
                f"No publications found on page {i + 1}. Skipping.", "warning"
            )
            continue

    pretty_logger(f"Collected a total of {len(publication_links)} publication links.")

    # --- 3. Scrape details for each publication ---
    total_links = len(publication_links)
    for i, link in enumerate(publication_links):
        pretty_logger(f"Scraping publication {i + 1}/{total_links}: {link}")

        details = _scrape_publication_details(driver, link)

        if details:
            details["id"] = i + 1
            details["link"] = link
            all_publications_data.append(details)

            file_handler.write_file(all_publications_data, "books.json")

    # --- 4. Write to file ONCE at the end ---
    if all_publications_data:
        pretty_logger(
            f"Writing {len(all_publications_data)} scraped publications to file..."
        )
        # file_handler.write_file(all_publications_data, config.pubs_file)
        pretty_logger("Scraping complete!")
    else:
        pretty_logger("No data was scraped. File not written.", "warning")
