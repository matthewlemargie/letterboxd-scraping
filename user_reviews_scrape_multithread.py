from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import csv
import regex as re
import os
import pandas as pd
import threading

csv_lock = threading.Lock()

header = [
        "film_popularity",
        "review_popularity",
        "rating",
        "liked",
        "user",
        "date",
        "comments",
        "movie",
        "review",
        "likes",
        ]

if not os.path.exists("user_reviews_multithread.csv"):
    user_start = 0
    with open("user_reviews_multithread.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(header)

df = pd.read_csv("user_reviews_multithread.csv")
df = df.drop_duplicates()
df.to_csv("user_reviews_multithread.csv", index=False)

keys = df.groupby("movie").size()[df.groupby("movie").size() != 1200].index
values = df.groupby("movie").size()[df.groupby("movie").size() != 1200]
incomplete_movies_dict = dict(zip(keys, values))

completed_movies_set  = set(df.groupby("movie").size()[df.groupby("movie").size() >= 1200].index)

del df

def thread(page_idx, link, link_idx):
    movie_name_from_url = link.split("/")[-2]

    film_popularity = (page_idx - 1) * 72 + link_idx + 1

    driver = webdriver.Firefox()
    if movie_name_from_url not in incomplete_movies_dict:
        driver.get(f"{link}/reviews/by/activity")
        review_page_start = 0
    else:
        driver.get(f"{link}/reviews/by/activity/page/{incomplete_movies_dict[movie_name_from_url] // 12}")
        review_page_start = incomplete_movies_dict[movie_name_from_url] // 12


    # iterate through all available pages (256) of reviews for the movie 
    for review_page_num in range(review_page_start, 100):
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

            if not review_page_num and movie_name_from_url in incomplete_movies_dict:
                attrib_blocks = attrib_blocks[(incomplete_movies_dict[movie_name_from_url] % 12):]

            userdata = []

            spans = [block.find_all("span") for block in attrib_blocks]

            for block_num, block in enumerate(attrib_blocks):
                try:
                    review_popularity = review_page_num * 12 + block_num + 1
                    spans = block.find_all("span")
                    out = [film_popularity, review_popularity, 0, 0, "", "", 0]
                    for s in range(len(spans)):
                        span = spans[s]
                        if "rating" in span.get("class"):
                            try:
                                out[2] = int(span.get("class")[-1].split("-")[-1])
                            except:
                                pass
                        if "icon-liked" in span.get("class"):
                            try:
                                out[3] = 1
                            except:
                                pass
                        if "content-metadata" in span.get("class"):
                            try:
                                # user
                                out[4] = span.find("a", class_="context").get("href").split("/")[1]
                            except:
                                pass
                            try:
                                # date
                                out[5] = span.find("span", class_="_nobr").text
                            except:
                                pass
                            try:
                                # comments
                                out[6] = int(span.find("a", class_="has-icon icon-comment icon-16 comment-count").text)
                            except:
                                pass

                    userdata.append(out)
                except:
                    continue

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
            with csv_lock:
                with open("user_reviews_multithread.csv", "a", newline="") as f:
                    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                    writer.writerows(userdata)

            while True:
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    driver.find_element(By.CSS_SELECTOR, "a[class=next]").click()
                    break
                except:
                    pass
        except:
            continue

    driver.quit()

def divide_list(lst, divisor):
    chunk_size = len(lst) // divisor
    remainder = len(lst) % divisor  # Handle cases where division isn't perfect

    result = []
    start = 0

    for i in range(divisor):
        extra = 1 if i < remainder else 0  # Distribute remaining elements
        result.append(lst[start : start + chunk_size + extra])
        start += chunk_size + extra
    
    return result

num_threads = 4

num_pages_finished = len(completed_movies_set) // 72
start_page = num_pages_finished + 1

for idx in tqdm(range(start_page, 501)):
    driver = webdriver.Firefox()
    driver.get(f"https://www.letterboxd.com/films/popular/page/{idx}/")

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
    driver.quit()

    active_threads = []

    for link_idx, link in enumerate(links):
        if link.split("/")[-2] in completed_movies_set:
            continue
        # Wait for an active thread to finish before adding a new one
        while len(active_threads) >= num_threads:
            for t in active_threads:
                if not t.is_alive():  # Check if the thread is done
                    t.join()  # Ensure it's fully terminated
                    active_threads.remove(t)  # Remove from active list
        
        # Start a new thread
        t = threading.Thread(target=thread, args=(idx, link, link_idx))
        t.start()
        active_threads.append(t)

    # Ensure all threads finish before exiting
    for t in active_threads:
        t.join()

