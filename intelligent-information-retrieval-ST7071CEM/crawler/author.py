import time
from utils.config import config
from utils.files import FileHandler
from utils.logger import pretty_logger
from selenium.webdriver.common.by import By


def get_author(driver, last_page_number=0):
    pagination_elements = driver.find_elements(
        By.XPATH, "//nav[@class='pages']//a[@class='step']"
    )

    if pagination_elements:
        last_page_number = int(pagination_elements[-1].text)

        text = f"Last pagination page number for publication: {last_page_number}"

        pretty_logger(text)

    file_handler = FileHandler()

    all_cu_auths = []

    for i in range(1 if last_page_number == 0 else last_page_number):
        cu_auth_url = f"{config.cu_auth_url}?page={i}"

        pretty_logger(f"Scraping auth page {i} publication", cu_auth_url)

        driver.get(cu_auth_url)

        auth_divs = driver.find_elements(By.CLASS_NAME, "result-container")

        for auth_div in auth_divs:
            h3_tag = auth_div.find_element(By.CLASS_NAME, "title")
            link_tag = h3_tag.find_element(By.TAG_NAME, "a")

            title = link_tag.text.strip()
            link = link_tag.get_attribute("href")

            all_cu_auths.append({"title": title, "link": link})

            pretty_logger(all_cu_auths)

        file_handler.write_file(all_cu_auths, "author.json")
