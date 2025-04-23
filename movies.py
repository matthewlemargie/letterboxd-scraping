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

max_attempts = 10

header = ["film_popularity",
          "movie",
          "year",
          "Watched by x members",
          "Appears in x lists",
          "Liked by x members",
          "No in Top 250",
          "half stars",
          "one stars",
          "onehalf stars",
          "two stars",
          "twohalf stars",
          "three stars",
          "threehalf stars",
          "four stars",
          "fourhalf stars",
          "five stars",
          "tagline",
          "description",
          "cast",
          "crew",
          "details",
          "genres",
          "themes",
          "url"]

if not os.path.exists("movies.csv"):
    with open("movies.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

df = pd.read_csv("movies.csv")
df = df.drop_duplicates()

df.to_csv("movies.csv", index=False)

completed_movie_set = set(df.url)

del df

# start_page = line_count // 72 + 1

def thread(page_idx, link, link_idx):
    total_attempts = 0
    film_popularity = (page_idx - 1) * 72 + link_idx + 1
    driver = webdriver.Firefox()
    driver.get(link)
    while total_attempts < max_attempts:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Ensure elements exist before accessing them
        title_div = soup.find("div", class_="col-17")
        if title_div is None:
            total_attempts += 1
            time.sleep(1)
            continue
        
        title_tag = title_div.find("h1")
        year_tag = title_div.find("a")

        if not title_tag or not year_tag:
            total_attempts += 1
            time.sleep(1)
            continue
        
        title = title_tag.text.strip()
        year = year_tag.text.strip()

        # Extract star ratings
        stars_section = soup.find("div", class_="rating-histogram clear rating-histogram-exploded")
        if stars_section is None:
            total_attempts += 1
            time.sleep(1)
            continue

        stars = stars_section.find_all("a")
        stars = [re.findall(r'\d+', str(star.text.replace(",", "")))[0] for star in stars]

        stats_div = soup.find("ul", class_="film-stats")
        if stats_div is None:
            total_attempts += 1
            time.sleep(1)
            continue

        try:
            stats = stats_div.find_all("a")
            stats = [re.findall(r'\d+', str(stat.get("data-original-title")).replace(",", ""))[0] for stat in stats]
        except:
            total_attempts += 1
            time.sleep(1)
            continue

        if len(stats) == 3:
            stats = stats + [""]

        try:
            desc_div = soup.find("div", class_="review body-text -prose -hero prettify")
            tagline = desc_div.find("h4", class_="tagline")
            tagline = tagline.text
        except:
            tagline = ""

        try:
            desc = desc_div.find("p")
            desc = desc.text
        except:
            desc = ""

        try:
            cast_div = soup.find("div", class_="cast-list text-sluglist")
            cast = cast_div.find_all("a", class_="text-slug tooltip")
            cast = [x.text for x in cast]
        except:
            cast = []

        try:
            button = driver.find_element(By.CSS_SELECTOR, f"a[href='/film/{link.split("/")[-2]}/crew/']")
            driver.execute_script("arguments[0].scrollIntoView();", button)
            button.click()

            soup = BeautifulSoup(driver.page_source, "html.parser")
            crew_div = soup.find("div", class_="tabbed-content-block column-block -crewroles")
            keys = crew_div.find_all("span", class_="crewrole -short")
            keys = [k.text for k in keys]
            lists = crew_div.find_all("div", class_="text-sluglist")
            valuelists = [l.find_all("a", class_="text-slug") for l in lists]
            valuelists = [[y.text for y in x] for x in valuelists]
            crew = dict(zip(keys, valuelists))
        except:
            crew = dict()

        try:
            button = driver.find_element(By.CSS_SELECTOR, f"a[href='/film/{link.split("/")[-2]}/details/']")
            driver.execute_script("arguments[0].scrollIntoView();", button)
            button.click()

            soup = BeautifulSoup(driver.page_source, "html.parser")
            details_div = soup.find("div", class_="tabbed-content-block column-block")
            keys = details_div.find_all("span")
            keys = [k.text for k in keys]
            lists = details_div.find_all("div", class_="text-sluglist")
            valuelists = [l.find_all("a", class_="text-slug") for l in lists]
            valuelists = [[y.text for y in x] for x in valuelists]
            details = dict(zip(keys, valuelists))
        except:
            details = dict()

        try:
            button = driver.find_element(By.CSS_SELECTOR, f"a[href='/film/{link.split("/")[-2]}/genres/']")
            driver.execute_script("arguments[0].scrollIntoView();", button)
            button.click()

            soup = BeautifulSoup(driver.page_source, "html.parser")
            genre_div = soup.find_all("div", class_="text-sluglist capitalize")
            genres = genre_div[0].find_all("a", class_="text-slug")
            genres = [genre.text for genre in genres]
            themes = genre_div[1].find_all("a", class_="text-slug")
            themes = [t.text for t in themes[:-1]]
        except:
            genres = []
            themes = []

        data = [film_popularity] + [title] + [year] + stats + stars + [tagline] + [desc] + [str(cast)] + [str(crew)] + [str(details)] + [str(genres)]  + [str(themes)] + [link]

        with csv_lock:
            with open("movies.csv", "a", newline="") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                writer.writerow(data)

        break
    driver.quit()


num_threads = 3

# num_pages_finished = len(completed_movies_set) // 72
# start_page = num_pages_finished + 1

for page_idx in tqdm(range(1, 501)):
    driver = webdriver.Firefox()
    driver.get(f"https://www.letterboxd.com/films/popular/page/{page_idx}/")

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

    active_threads = []

    for link_idx, link in enumerate(links):
        if link in completed_movie_set:
            continue
        while len(active_threads) >= num_threads:
            for t in active_threads:
                if not t.is_alive():  # Check if the thread is done
                    t.join()  # Ensure it's fully terminated
                    active_threads.remove(t)  # Remove from active list
        
        # Start a new thread
        t = threading.Thread(target=thread, args=(page_idx, link, link_idx))
        t.start()
        active_threads.append(t)

    # Ensure all threads finish before exiting
    for t in active_threads:
        t.join()


