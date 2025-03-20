from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import csv
import regex as re
import os
import pandas as pd

driver = webdriver.Firefox()
driver.get(f"https://letterboxd.com/b1mb1m/films/reviews/")
res = dict()
i = 0
while True:
    success = False
    while not success:
        try:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            section = soup.find("section", "section col-main overflow col-17")
            success = True
        except:
            pass

    reviews = section.find_all("div", "film-detail-content")
    review = section.find("div", "film-detail-content")

    movies = [r.find("a").get("href").split("/")[3] for r in reviews]
    stars = [r.find("span").get("class")[-1].split("-")[-1] for r in reviews]

    newdict = dict(zip(movies, stars))
    res.update(newdict)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    try:
        driver.find_element(By.CSS_SELECTOR, "a[class=next]").click()
    except:
        break

    print(i)
    i += 1


print(res)

driver.close()


# first compile list of users

# then for each user go through all the movies they have rated
# and collect dictionary of movies(keys)/ratings(values) 


