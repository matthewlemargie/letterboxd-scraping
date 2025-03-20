from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import csv
import regex as re
import os
import pandas as pd

users_set = set()

if not os.path.exists("users.csv"):
    with open("users.csv", "w", newline="") as f:
        writer = csv.writer(f)

for i in tqdm(range(20, 501)):
    driver = webdriver.Firefox()
    driver.get(f"https://www.letterboxd.com/films/popular/page/{i}/")

    # first check for reviews else skip 
    time.sleep(1)
    elements,links = None, None
    i = 0
    while not elements or not links:
        if i == 5:
            break
        elements = driver.find_elements(By.CLASS_NAME, "frame")
        links = [x.get_attribute("href") for x in elements]
        time.sleep(1)
        i += 1
    if i == 5:
        continue
    links = [x for x in links if x is not None]
    driver.close()

    for link in links:
        driver = webdriver.Firefox()
        driver.get(f"{link}/reviews/by/activity")
        users_set = set()

        with open("users.csv", "r") as f:
            for line in f:
                users_set.add(line.strip())

        while True:
            success = False
            while not success:
                try:
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    section = soup.find("section", "viewings-list")
                    success = True
                except:
                    pass

            reviews = section.find_all("li", "film-detail")

            users = [r.find("a").get("href").split("/")[1] for r in reviews]

            with open("users.csv", "a", newline="") as f:
                writer = csv.writer(f)
                for user in users:
                    if user not in users_set:
                        writer.writerow([user])

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                driver.find_element(By.CSS_SELECTOR, "a[class=next]").click()
            except:
                break

        driver.close()


# first compile list of users

# then for each user go through all the movies they have rated
# and collect dictionary of movies(keys)/ratings(values) 


