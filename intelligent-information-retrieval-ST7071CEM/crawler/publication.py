import time
import re

from utils.config import config
from utils.files import FileHandler
from utils.logger import pretty_logger

from selenium.webdriver.common.by import By


def get_publications(driver, last_page_number=0):
    pagination_elements = driver.find_elements(
        By.XPATH, "//nav[@class='pages']//a[@class='step']"
    )

    if pagination_elements:
        last_page_number = int(pagination_elements[-1].text)

        text = f"Last pagination page number for publication: {last_page_number}"

        pretty_logger(text)

    book_details = []

    file_handler = FileHandler()

    pub_count = 1
    for i in range(1 if last_page_number == 0 else last_page_number):
        pub_url = f"{config.pub_link}?page={i}"
        pretty_logger(f"Scraping page {i} publication", pub_url)

        driver.get(pub_url)

        publication_divs = driver.find_elements(By.CLASS_NAME, "result-container")

        if not publication_divs:
            print("Content not found")
        else:
            print("Staring Scraping")

        with_pub_details = []

        for pub_div in publication_divs:
            pub_details = {}
            h3_tag = pub_div.find_element(By.CLASS_NAME, "title")
            link_tag = h3_tag.find_element(By.TAG_NAME, "a")
            keywords_el = pub_div.find_elements(
                By.CLASS_NAME, "concept-badge-small-container"
            )

            output_el = pub_div.find_element(By.CLASS_NAME, "rendering_researchoutput")

            pub_concepts = []

            for concept in keywords_el:
                pub_concepts.append(concept.text if concept else None)

            op_text = output_el.text if output_el.text else None

            if op_text:
                split_ouptput = op_text.split("\n")
                pub_details["detail"] = split_ouptput[1]
                pub_details["output"] = split_ouptput[2]

            link = link_tag.get_attribute("href")

            pub_details["link"] = link
            pub_details["concepts"] = pub_concepts

            # pretty_logger(pub_details, "pub_details")

            # Extract required data: title and link

            with_pub_details.append(pub_details)

        for pi, d in enumerate(with_pub_details):
            my_book_details = {}

            link = d["link"]

            driver.get(link)

            time.sleep(3)

            authors_list = []

            auth_el = driver.find_element(By.CSS_SELECTOR, "p.relations.persons")

            parts = auth_el.text.split(",")

            a_links = auth_el.find_elements(By.TAG_NAME, "a")

            for i, part in enumerate(parts):
                name = part.strip()
                a_link = None

                # If there’s an <a> with the same name, grab href
                for a in a_links:
                    if a.text.strip() == name:
                        a_link = a.get_attribute("href")
                        break

                authors_list.append({"name": name, "link": a_link})

            pretty_logger(authors_list, "authors_list")

            select_bibtex = driver.find_element(By.ID, "tab-5")

            select_bibtex.click()

            time.sleep(1)
            pretty_logger(link, "link")

            select_bibtex_el = driver.find_element(
                By.CLASS_NAME, "rendering_researchoutput_bibtex"
            )

            bib_str = select_bibtex_el.text

            my_book_details["id"] = pub_count
            my_book_details["authors"] = authors_list

            for field in ["title", "year", "month", "day", "abstract"]:
                match = re.search(rf'{field}\s*=\s*"([^"]+)"', bib_str)
                if field == "month":
                    match = re.search(rf'{field}\s*=\s*([^"]+),', bib_str)

                if match:
                    my_book_details[field] = match.group(1) if match.group(1) else None

            my_book_details["detail"] = d["detail"]
            my_book_details["output"] = d["output"]
            my_book_details["link"] = link
            my_book_details["concepts"] = d["concepts"]

            book_details.append(my_book_details)

            pretty_logger(select_bibtex_el.text, "el")

            pretty_logger(my_book_details, "fetch book details")

            file_handler.write_file(book_details, "books.json")

            pretty_logger(
                pub_count,
                f"Scraping finished for publication {pub_count} for page {i} total publication of this page {pi + 1}/{len(with_pub_details)}",
            )

            pub_count += 1
    file_handler.write_file(book_details, config.pubs_file)
