import time

from selenium import webdriver

from crawler.author import get_author
from crawler.pubs import get_publications
from utils.config import config
from utils.logger import pretty_logger
from selenium.webdriver.common.by import By

from utils.robots import (
    is_url_allowed,
    parse_robots_txt,
    parse_sitemap_urls,
    find_org_sitemap_entry,
)


class Crawler:
    def __init__(self) -> None:
        self.driver = webdriver.Chrome()

        self._crawl_publications()
        # self._crawl_author()
        self._quit_driver()

    def _quit_driver(self):
        """Close the WebDriver instance"""
        if self.driver:
            self.driver.quit()

    def _accept_cookie(self):
        try:
            time.sleep(3)
            cookie_btn = self.driver.find_element(By.ID, "onetrust-accept-btn-handler")
            cookie_btn.click()
        except Exception as e:
            pretty_logger(e)
            raise ValueError(f"Error from clicking accept cookie '{e}'")

    def _crawl_publications(self):
        try:
            crawl_delay, sitemap_url = parse_robots_txt(self.driver)
            if not sitemap_url:
                print("Sitemap not found in robots.txt. Aborting.")
                return []

            print(f"Following robots.txt rules. Crawl delay: {crawl_delay} seconds.")

            if not is_url_allowed(config.pub_link):
                print(f"Direct access URL blocked by robots.txt: {config.pub_link}")
                target_urls = []  # Force fallback to sitemap approach
            else:
                print(f"Attempting direct access to: {config.pub_link}")
                self.driver.get(config.pub_link)
                time.sleep(crawl_delay)

                # Check if we successfully accessed the department page
                if (
                    "publications" in self.driver.current_url.lower()
                    and config.dep in self.driver.current_url
                    and config.dep != ""
                ):
                    print("✓ Direct access successful!")
                    target_urls = [config.pub_link]
                else:
                    print("Direct access failed, using sitemap approach...")
                    target_urls = []
            # Use fallback sitemap approach if direct access failed or was blocked
            if "target_urls" not in locals() or not target_urls:
                print("Using sitemap approach...")
                # Check if main sitemap URL is allowed
                if not is_url_allowed(sitemap_url):
                    print(f"Main sitemap URL blocked by robots.txt: {sitemap_url}")
                    return []

                # Fallback to original sitemap method
                all_urls = parse_sitemap_urls(
                    self.driver,
                    sitemap_url,
                    r"https://pureportal\.coventry\.ac\.uk/sitemap/[^<>\s]+\.xml(?:\?[^<>\s]*)?",
                )
                print(f"Found {len(all_urls)} URLs in the sitemap.")

                org_urls_list = find_org_sitemap_entry(
                    self.driver, all_urls, "organisations", ""
                )
                if not org_urls_list:
                    print("Could not find the target department URLs. Aborting.")
                    return []

                print(f"org_urls_list found: {org_urls_list}")
                # Filter for our specific department
                target_urls = []
                for url in org_urls_list:
                    # if TARGET_DEPT in url:
                    pub_url = f"{url}/publications"
                    # Check if URL is allowed before adding
                    if is_url_allowed(pub_url):
                        target_urls.append(pub_url)
                    else:
                        print(f"Skipping disallowed URL: {pub_url}")

            if not target_urls:
                print(f"Could not find allowed URLs for {config.dep}. Aborting.")
                return []
            self.driver.get(config.pub_link)

            self._accept_cookie()

            get_publications(self.driver)

        except Exception as e:
            raise Exception(f"Error while scraping publications: {e}")

    def _crawl_author(self):
        try:
            self.driver.get(config.auth_url)

            self._accept_cookie()

            get_author(self.driver)

        except Exception as e:
            raise Exception(f"Error while scraping author: {e}")
