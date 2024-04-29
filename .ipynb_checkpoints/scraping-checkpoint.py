from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import requests

with open("data.txt", "a") as f:
    for i in range(1,701):
        driver = webdriver.Firefox()
        driver.get(f"https://www.letterboxd.com/films/popular/page/{i}/")
        time.sleep(3)
        elements = driver.find_elements(By.CLASS_NAME, "frame")
        links = [x.get_attribute("href") for x in elements]
        driver.quit()
        links = [x for x in links if x is not None]

        for link in links:
            page = requests.get(link)
            soup = BeautifulSoup(page.text, "html.parser")
            title = soup.find("div", class_="col-17").find("h1").text
            year = soup.find("div", class_="col-17").find("a").text
            stars = soup.find_all("a", attrs={"class":"ir tooltip"})
            #stars = [star.text for star in stars]
            # f.write(f"{title}, {year}, {stars[0]}, {stars[1]}, {stars[2]}, {stars[3]}, {stars[4]}, {stars[5]}, {stars[6]}, {stars[7]}, {stars[8]}, {stars[9]}\n")
            # print(f"{title}, {year}, {stars[0]}, {stars[1]}, {stars[2]}, {stars[3]}, {stars[4]}, {stars[5]}, {stars[6]}, {stars[7]}, {stars[8]}, {stars[9]}")
            print(f"{title}, {year}")
            print(stars)
