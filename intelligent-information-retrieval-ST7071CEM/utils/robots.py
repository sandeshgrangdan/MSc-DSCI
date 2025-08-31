import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from utils.config import config


# Global driver instance to avoid recreating (major optimization)
_driver = None
_crawl_delay = 5
_disallow_patterns = []  # Store disallow patterns from robots.txt


def is_url_allowed(url):
    """Check if URL is allowed based on robots.txt disallow rules."""
    global _disallow_patterns

    for pattern in _disallow_patterns:
        # Convert robots.txt pattern to regex
        # /*?*format=rss becomes .*\?.*format=rss
        # /*?*export=xls becomes .*\?.*export=xls
        regex_pattern = pattern.replace("/*?*", r".*\?.*").replace("*", ".*")
        if re.search(regex_pattern, url):
            print(f"URL blocked by robots.txt rule '{pattern}': {url}")
            return False
    return True


def parse_robots_txt(driver):
    """Fetches robots.txt using Selenium to handle Cloudflare and parses disallow rules."""
    global _crawl_delay, _disallow_patterns

    print("Fetching robots.txt with Selenium...")

    ROBOTS_URL = config.robots_txt_url

    try:
        print(f"Loading robots.txt with Selenium...{ROBOTS_URL}")
        driver.get(ROBOTS_URL)
        time.sleep(10)

        content = driver.page_source

        # Extract text content (remove HTML tags if any)
        soup = BeautifulSoup(content, "html.parser")
        text_content = soup.get_text()

        print("Successfully fetched robots.txt with Selenium!")
        print("Content preview:", text_content[:200])

        # Parse sitemaps, crawl delay, and disallow rules
        sitemaps = []
        crawl_delay = 5
        disallow_patterns = []

        for line in text_content.splitlines():
            line = line.strip()
            if re.match(r"^sitemap:", line, re.IGNORECASE):
                sitemap_url = line.split(":", 1)[1].strip()
                sitemaps.append(sitemap_url)
                print(f"Found sitemap: {sitemap_url}")
            elif re.match(r"^crawl-delay:", line, re.IGNORECASE):
                crawl_delay = int(line.split(":", 1)[1].strip())
                print(f"Found crawl delay: {crawl_delay}")
            elif re.match(r"^disallow:", line, re.IGNORECASE):
                disallow_path = line.split(":", 1)[1].strip()
                disallow_patterns.append(disallow_path)
                print(f"Found disallow rule: {disallow_path}")

        _crawl_delay = crawl_delay
        _disallow_patterns = disallow_patterns
        print(f"Loaded {len(disallow_patterns)} disallow rules from robots.txt")

        return crawl_delay, sitemaps[0] if sitemaps else None

    except Exception as e:
        print(f"Selenium failed: {e}")
        return 5, None


def parse_sitemap_urls(sitemap_url, regex_url_filter, driver):
    """Fetches a sitemap using existing driver and returns a list of all URLs within it."""
    # Check if sitemap URL is allowed by robots.txt
    if not is_url_allowed(sitemap_url):
        print(f"Sitemap URL blocked by robots.txt: {sitemap_url}")
        return []

    try:
        driver.get(sitemap_url)
        time.sleep(3)  # Reduced from 5 seconds

        content = driver.page_source
        soup = BeautifulSoup(content, "html.parser")
        text_content = soup.get_text()

        print(f"Extracting URLs with regex pattern: {regex_url_filter}")
        urls = re.findall(regex_url_filter, text_content)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        print(f"Extracted {len(unique_urls)} unique sitemap URLs")
        return unique_urls

    except Exception as e:
        print(f"Error: {e}")
        return []


def find_org_sitemap_entry(all_urls, target_org_path, fragment, driver):
    """
    Finds a specific URL from a list of URLs based on a fragment,
    then checks if the target organization exists in the organizations sitemap.
    Args:
        all_urls: List of sitemap URLs
        target_org_path: The organization path to look for (e.g., "/organisations/fbl-school-of-economics-finance-and-accounting")
        fragment: Fragment to search for in URLs (e.g., "organisations"). If empty, returns all URLs from target_org_path
    Returns:
        tuple: (organizations_sitemap_url, target_organization_url) or (None, None)
        If fragment is empty, returns all URLs from the target organization
    """
    # Step 1: Find the organizations sitemap URL
    organizations_sitemap_url = None
    for url in all_urls:
        if target_org_path in url and url.endswith(f"{target_org_path}.xml"):
            organizations_sitemap_url = url
            break

    if not organizations_sitemap_url:
        print(f"No organizations sitemap found containing '{target_org_path}'")
        return None, None

    print(f"Found organizations sitemap: {organizations_sitemap_url}")

    # Step 2: Fetch and parse the organizations sitemap
    try:
        if fragment == "":
            # If fragment is empty, get all URLs from target_org_path
            org_urls = parse_sitemap_urls(
                organizations_sitemap_url,
                r"https://pureportal\.coventry\.ac\.uk/en/organisations/.*?(?=https://|$)",
                driver,
            )
            if not org_urls:
                print("Failed to extract URLs from organizations sitemap")
                return organizations_sitemap_url, None

            print(f"Found {len(org_urls)} organization URLs (all)")
            return org_urls  # Return all URLs instead of single target

        else:
            # Original logic for specific fragment
            org_urls = parse_sitemap_urls(
                organizations_sitemap_url,
                rf"https://pureportal\.coventry\.ac\.uk/en/{target_org_path}/{fragment}",
                driver,
            )
            if not org_urls:
                print("Failed to extract URLs from organizations sitemap")
                return organizations_sitemap_url, None

            print(f"Found {len(org_urls)} organization URLs")

            # Step 3: Look for the target organization URL
            target_full_url: str = ""
            for url in org_urls:
                if target_org_path in url:
                    target_full_url = url
                    print(f"Found target organization: {target_full_url}")
                    break

            if not target_full_url:
                print(
                    f"Target organization '{target_org_path}' not found in organizations sitemap"
                )
                # Print some sample URLs for debugging
                print("Sample organization URLs found:")
                for url in org_urls[:5]:
                    print(f" - {url}")

            return target_full_url

    except Exception as e:
        print(f"Error processing organizations sitemap: {e}")
        return None
