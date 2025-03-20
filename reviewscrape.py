from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import csv
import regex as re
import os
import pandas as pd

if not os.path.exists("reviews.csv"):
    user_start = 0
    with open("reviews.csv", "w") as f:
        pass
else:
    with open("reviews.csv", "rb") as file:  # Open in binary mode
        file.seek(-2, 2)  # Move 2 bytes before end of file
        while file.read(1) != b"\n":  # Read backward until newline
            file.seek(-2, 1)  # Move back again
        last_line = file.readline().decode().strip()  # Read last line
        user_start = int(last_line.split(",")[0])

i = user_start

with open("users.csv", "r") as f:
    count = 0
    for user in f:
        if count < user_start:
            count += 1
            continue
        driver = webdriver.Firefox()
        driver.get(f"https://letterboxd.com/{user}/films/reviews/")
        for _ in range(100):
            success = False
            while not success:
                try:
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    section = soup.find("section", "section col-main overflow col-17")
                    success = True
                except:
                    pass

            reviews = section.find_all("div", "film-detail-content")

            movies = [r.find("a").get("href").split("/")[3] for r in reviews]
            stars = [r.find("span").get("class")[-1].split("-")[-1] for r in reviews]

            try:
                review_text_div = section.find_all("div", class_="body-text -prose js-review-body js-collapsible-text")
                review_text = [r.find("p").text for r in review_text_div]
            except:
                review_text = ["" for x in movies]

            reviewsdict = dict(zip(movies, list(zip(stars, review_text))))

            with open("reviews.csv", "a", newline="") as f:
                for k, v in reviewsdict.items():
                    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                    data = [i] + [k.strip()] + [v[0].strip()] + [v[1].strip()]
                    writer.writerow(data)
                
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                driver.find_element(By.CSS_SELECTOR, "a[class=next]").click()
            except:
                break

        driver.close()
        i += 1

