"""
Dataset Expander for Fake News Detection
=========================================
Expands the base gossip-cop CSV (id, news_url, title, tweet_ids)
into a rich feature set:

  news_id, title, text, source, author, publish_date, label,
  image_url, news_url, retweet_count, user_id, tweet_id, created_at

Requirements:
    pip install pandas requests beautifulsoup4 lxml tweepy newspaper3k

Usage:
    python expand_dataset.py \
        --input  gossipcop.csv \
        --output gossipcop_expanded.csv \
        --label  fake          # or "real"
        [--bearer-token  <Twitter Bearer Token>]
"""

import argparse
import re
import time
import random
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def safe_get(url: str, timeout: int = 12) -> requests.Response | None:
    """HTTP GET with retry + polite delay."""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            log.warning("Attempt %d failed for %s: %s", attempt + 1, url, exc)
            time.sleep(2 ** attempt + random.random())
    return None


def normalize_url(raw: str) -> str:
    """Add https:// scheme if missing."""
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def extract_source(url: str) -> str:
    """Extract publisher domain from URL."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc
        # strip www. prefix
        return re.sub(r"^www\.", "", host)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Article scraping
# ---------------------------------------------------------------------------

def scrape_article(url: str) -> dict:
    """
    Try newspaper3k first; fall back to raw BeautifulSoup extraction.

    Returns dict with keys: text, author, publish_date, image_url
    """
    result = {
        "text": "",
        "author": "",
        "publish_date": "",
        "image_url": "",
    }

    # --- Option 1: newspaper3k (best quality) ---
    try:
        from newspaper import Article
        art = Article(url)
        art.download()
        art.parse()
        result["text"] = art.text or ""
        result["author"] = ", ".join(art.authors) if art.authors else ""
        if art.publish_date:
            result["publish_date"] = art.publish_date.strftime("%Y-%m-%d")
        result["image_url"] = art.top_image or ""
        if result["text"]:          # newspaper succeeded
            return result
    except Exception as exc:
        log.debug("newspaper3k failed for %s: %s", url, exc)

    # --- Option 2: raw BeautifulSoup fallback ---
    resp = safe_get(url)
    if resp is None:
        return result

    soup = BeautifulSoup(resp.text, "lxml")

    # text: grab all <p> tags inside likely article containers
    article_tag = (
        soup.find("article")
        or soup.find(attrs={"class": re.compile(r"article|post|content|story", re.I)})
        or soup.find("main")
        or soup.body
    )
    if article_tag:
        paragraphs = article_tag.find_all("p")
        result["text"] = " ".join(p.get_text(" ", strip=True) for p in paragraphs)

    # author: common meta/schema patterns
    for selector in [
        {"name": "author"},
        {"property": "article:author"},
        {"name": "byl"},
        {"class": re.compile(r"author|byline", re.I)},
    ]:
        tag = soup.find(attrs=selector)
        if tag:
            result["author"] = tag.get("content", "") or tag.get_text(strip=True)
            if result["author"]:
                break

    # publish_date
    for selector in [
        {"property": "article:published_time"},
        {"name": "pubdate"},
        {"name": "publish-date"},
        {"itemprop": "datePublished"},
    ]:
        tag = soup.find(attrs=selector)
        if tag:
            raw_date = tag.get("content", "") or tag.get("datetime", "")
            if raw_date:
                try:
                    result["publish_date"] = datetime.fromisoformat(
                        raw_date[:10]
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    result["publish_date"] = raw_date[:10]
                break

    # image_url: og:image is most reliable
    og_img = soup.find("meta", property="og:image")
    if og_img:
        result["image_url"] = og_img.get("content", "")

    return result


# ---------------------------------------------------------------------------
# Twitter / X enrichment  (optional — requires Bearer Token)
# ---------------------------------------------------------------------------

def enrich_tweets_tweepy(tweet_ids: list[str], bearer_token: str) -> list[dict]:
    """
    Use Twitter API v2 to fetch retweet_count, user_id, created_at.
    Returns a list of dicts (one per tweet_id).
    """
    try:
        import tweepy
    except ImportError:
        log.warning("tweepy not installed — skipping Twitter enrichment.")
        return _empty_tweet_rows(tweet_ids)

    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
    rows = []

    # API allows up to 100 IDs per request
    chunk_size = 100
    for i in range(0, len(tweet_ids), chunk_size):
        chunk = tweet_ids[i : i + chunk_size]
        try:
            resp = client.get_tweets(
                ids=chunk,
                tweet_fields=["created_at", "public_metrics", "author_id"],
            )
            if resp.data:
                for tw in resp.data:
                    rows.append(
                        {
                            "tweet_id": str(tw.id),
                            "user_id": str(tw.author_id) if tw.author_id else "",
                            "retweet_count": (
                                tw.public_metrics.get("retweet_count", 0)
                                if tw.public_metrics
                                else 0
                            ),
                            "created_at": (
                                tw.created_at.strftime("%Y-%m-%d %H:%M:%S")
                                if tw.created_at
                                else ""
                            ),
                        }
                    )
        except Exception as exc:
            log.warning("Tweet batch %d failed: %s", i // chunk_size, exc)
            rows.extend(_empty_tweet_rows(chunk))

    return rows


def _empty_tweet_rows(tweet_ids: list[str]) -> list[dict]:
    return [
        {"tweet_id": tid, "user_id": "", "retweet_count": 0, "created_at": ""}
        for tid in tweet_ids
    ]


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def process_row(row: pd.Series, label: str, bearer_token: str | None) -> list[dict]:
    """
    Given one row of the input CSV, return a list of output records
    (one per tweet, so the article columns are duplicated per tweet).
    """
    news_id  = row["id"]
    raw_url  = row["news_url"]
    title    = row["title"]
    url      = normalize_url(raw_url)
    source   = extract_source(url)

    log.info("Processing article: %s", news_id)
    article  = scrape_article(url)

    # Parse tweet_ids (tab-separated in the CSV)
    raw_ids  = str(row.get("tweet_ids", "")).strip()
    tweet_ids = [t.strip() for t in re.split(r"[\t,\s]+", raw_ids) if t.strip()]

    # Enrich tweets
    if bearer_token and tweet_ids:
        tweet_rows = enrich_tweets_tweepy(tweet_ids, bearer_token)
    else:
        tweet_rows = _empty_tweet_rows(tweet_ids) if tweet_ids else [
            {"tweet_id": "", "user_id": "", "retweet_count": 0, "created_at": ""}
        ]

    records = []
    for tw in tweet_rows:
        records.append(
            {
                "news_id":       news_id,
                "title":         title,
                "text":          article["text"],
                "source":        source,
                "author":        article["author"],
                "publish_date":  article["publish_date"],
                "label":         label,
                "image_url":     article["image_url"],
                "news_url":      url,
                "retweet_count": tw["retweet_count"],
                "user_id":       tw["user_id"],
                "tweet_id":      tw["tweet_id"],
                "created_at":    tw["created_at"],
            }
        )

    # Polite crawl delay
    time.sleep(random.uniform(1.5, 3.0))
    return records


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Expand gossip-cop dataset.")
    parser.add_argument("--input",        required=True, help="Input CSV path")
    parser.add_argument("--output",       required=True, help="Output CSV path")
    parser.add_argument("--label",        default="fake",
                        choices=["fake", "real"],
                        help="Label for all articles in this file (default: fake)")
    parser.add_argument("--bearer-token", default=None,
                        help="Twitter/X API v2 Bearer Token (optional)")
    parser.add_argument("--limit",        type=int, default=None,
                        help="Only process the first N rows (for testing)")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    if args.limit:
        df = df.head(args.limit)

    all_records: list[dict] = []
    for _, row in df.iterrows():
        try:
            records = process_row(row, args.label, args.bearer_token)
            all_records.extend(records)
        except Exception as exc:
            log.error("Failed on row %s: %s", row.get("id", "?"), exc)

    out_df = pd.DataFrame(all_records, columns=[
        "news_id", "title", "text", "source", "author",
        "publish_date", "label", "image_url", "news_url",
        "retweet_count", "user_id", "tweet_id", "created_at",
    ])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    log.info("Saved %d rows → %s", len(out_df), out_path)


if __name__ == "__main__":
    main()