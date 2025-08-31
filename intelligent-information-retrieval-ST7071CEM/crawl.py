from crawler.selenium import Crawler
from apscheduler.schedulers.background import BackgroundScheduler


def crawl():
    Crawler()


if __name__ == "__main__":
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        crawl,
        trigger="cron",
        day_of_week="sun",
        hour=3,
        minute=0,
        id="weekly_crawl_reindex",
        replace_existing=True,
    )
    scheduler.start()
    print("Background scheduler started (weekly crawl @ Sun 03:00).")
    crawl()
