from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import csv
import regex as re
import os
import pandas as pd


# also i want to multithread so it doesn't take forever

header = [
        "rating",
        "liked",
        "user",
        "date",
        "comments",
        "movie",
        "review",
        "likes",
        ]

if not os.path.exists("user_reviews.csv"):
    user_start = 0
    with open("user_reviews.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(header)

df = pd.read_csv("user_reviews.csv")
df = df.drop_duplicates()
completed_movies_set = df.movie.unique()
df.to_csv("user_reviews.csv", index=False)

if not os.path.exists("last_page_ended.txt"):
    with open("last_page_ended.txt", "w") as f:
        f.write("1")

with open("last_page_ended.txt", "r") as f:
    page_start = int(f.readline())

first_loop = True

for i in tqdm(range(page_start, 501)):
    driver = webdriver.Firefox()
    driver.get(f"https://www.letterboxd.com/films/popular/page/{i}/")

    # get list of links for movies on page
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

    # iterate through movie links for page i
    for link in links:
        # movie_name_from_url
        movie_name_from_url = link.split("/")[-2]

        if movie_name_from_url in completed_movies_set:
            continue

        driver = webdriver.Firefox()
        driver.get(f"{link}/reviews/by/activity")

        # iterate through all available pages (256) of reviews for the movie 
        for _ in range(100):
            try:
                # make sure page has loaded
                success = False
                while not success:
                    try:
                        soup = BeautifulSoup(driver.page_source, "html.parser")
                        section = soup.find("section", "viewings-list")
                        success = True
                    except:
                        pass
                
                # list of divs containing review data
                review_divs = section.find_all("div", "film-detail-content")

                attrib_blocks = [r.find("div", class_="attribution-block") for r in review_divs]

                userdata = []

                spans = [block.find_all("span") for block in attrib_blocks]

                for block in attrib_blocks:
                    spans = block.find_all("span")
                    out = [0, 0, "", "", 0]
                    for i in range(len(spans)):
                        span = spans[i]
                        if "rating" in span.get("class"):
                            try:
                                out[0] = int(span.get("class")[-1].split("-")[-1])
                            except:
                                pass
                        if "icon-liked" in span.get("class"):
                            try:
                                out[1] = 1
                            except:
                                pass
                        if "content-metadata" in span.get("class"):
                            try:
                                # user
                                out[2] = span.find("a", class_="context").get("href").split("/")[1]
                            except:
                                pass
                            try:
                                # date
                                out[3] = span.find("span", class_="_nobr").text
                            except:
                                pass
                            try:
                                # comments
                                out[4] = int(span.find("a", class_="has-icon icon-comment icon-16 comment-count").text)
                            except:
                                pass

                    userdata.append(out)

                try:
                    review_text_div = section.find_all("div", class_="body-text -prose js-review-body js-collapsible-text")
                    review_text = [r.find("p").text for r in review_text_div]
                except:
                    review_text = ["" for x in attrib_blocks]

                try:
                    likes_ps = section.find_all("p", "like-link-target react-component -monotone")
                    likes = [l.get("data-count") for l in likes_ps]
                except:
                    likes = ["" for x in attrib_blocks]

                for i in range(len(userdata)):
                    userdata[i].append(movie_name_from_url)
                    userdata[i].append(review_text[i])
                    userdata[i].append(likes[i])

                # write users from review page to file
                with open("user_reviews.csv", "a", newline="") as f:
                    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                    writer.writerows(userdata)

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                try:
                    driver.find_element(By.CSS_SELECTOR, "a[class=next]").click()
                except:
                    break
            except:
                break

        driver.close()

    if first_loop:
        df = pd.read_csv("user_reviews.csv")
        df = df.drop_duplicates()
        df.to_csv("user_reviews.csv", index=False)
        first_loop = False

    with open("last_page_ended.txt", "w") as f:
        f.write(str(i))

