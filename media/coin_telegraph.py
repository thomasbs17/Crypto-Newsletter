from datetime import timedelta, datetime as dt

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class CoinTelegraph:
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date
        service = Service(ChromeDriverManager().install())
        self.home_url = "https://cointelegraph.com/"
        self.driver = webdriver.Chrome(service=service)
        self.articles_meta = {}
        self.articles = []

    @staticmethod
    def process_time(raw_time: str) -> dt:
        raw_time = raw_time.upper()
        if "AGO" in raw_time:
            time_value = int(raw_time[: raw_time.find(" ")])
            if "MINUTE" in raw_time:
                article_time = dt.now() - timedelta(minutes=time_value)
            elif "HOUR" in raw_time:
                article_time = dt.now() - timedelta(hours=time_value)
            else:
                raise "Unknown article format"
        else:
            article_time = dt.strptime(raw_time, "%b %d, %Y")
        return article_time

    def load_older_articles(self):
        x_path = '//*[@id="__layout"]/div/div[1]/main/div/div/div[2]/div/div/div/button'
        button = self.driver.find_element(By.XPATH, x_path)
        self.driver.execute_script("arguments[0].scrollIntoView();", button)
        button.click()

    def is_within_time_range(self, article) -> bool:
        article_raw_text = article.text.splitlines()
        if article_raw_text:
            article_time = self.process_time(article_raw_text[3])
            if (
                self.start_date >= article_time.strftime("%Y-%m-%d")
                and article_time.strftime("%Y-%m-%d") > self.end_date
            ):
                return True
            else:
                return False

    def get_article_meta_deta(self, article):
        article_raw_text = article.text.splitlines()
        if self.is_within_time_range(article):
            url = article.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")
            title = article_raw_text[1]
            article_time = self.process_time(article_raw_text[3])
            article_details = {
                "category": article_raw_text[0],
                "title": title,
                "author": article_raw_text[2],
                "time": article_time,
                "url": url,
            }
            if title not in self.articles_meta and title != "Latest News":
                self.articles_meta[title] = article_details

    def get_article_details(self):
        for article in self.articles_meta:
            article_details = self.articles_meta[article]
            self.driver.get(article_details["url"])
            stats = self.driver.find_elements(By.CLASS_NAME, "post-actions__item-count")
            if len(stats) > 1:
                details = {
                    "url": article_details["url"],
                    "views": int(stats[0].text),
                    "shares": int(stats[1].text),
                }
                self.articles.append(article_details | details)

    def get_all_articles(self):
        self.driver.get(self.home_url)
        is_running = True
        while is_running:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            articles_html = self.driver.find_elements(By.TAG_NAME, "article")
            for article in articles_html:
                if self.is_within_time_range(article):
                    self.get_article_meta_deta(article)
                else:
                    is_running = False
            self.load_older_articles()

    def get_daily_news(self) -> pd.DataFrame:
        self.get_all_articles()
        self.get_article_details()
        self.driver.quit()
        return pd.DataFrame(data=self.articles)

    def top_articles(self, top: int) -> tuple:
        articles_df = self.get_daily_news()
        most_viewed = articles_df.sort_values(by="views", ascending=False).head(top)
        most_shared = articles_df.sort_values(by="shares", ascending=False).head(top)
        return most_viewed, most_shared
