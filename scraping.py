from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import requests

file = open("data.csv", "w")
file.close()

for i in range(1,1001):
    driver = webdriver.Firefox()
    driver.get(f"https://www.letterboxd.com/films/popular/page/{i}/")
    time.sleep(2)
    try:
        elements = None
        elements = driver.find_elements(By.CLASS_NAME, "frame")
        links = None
        links = [x.get_attribute("href") for x in elements]
        links = [x for x in links if x is not None]
    except:
        driver.quit()
        continue
    driver.quit()


    driver = webdriver.Firefox()
    for link in links:
        driver.get(link)
        time.sleep(0.7)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        title = soup.find("div", class_="col-17").find("h1").text
        year = soup.find("div", class_="col-17").find("a").text
        try:
            stars = None
            stars = soup.find("div", class_="rating-histogram clear rating-histogram-exploded").find_all("a")
            stars = [" ".join([star.text.split(" ")[-1], star.text.split(" ")[0]]) for star in stars]
            with open("data.csv", "a") as f:
                f.write(f"{title}, {year}, {stars[0]}, {stars[1]}, {stars[2]}, {stars[3]}, {stars[4]}, {stars[5]}, {stars[6]}, {stars[7]}, {stars[8]}, {stars[9]}\n")
        except:
            pass
    driver.quit()

