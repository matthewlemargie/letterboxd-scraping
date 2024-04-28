from selenium import webdriver
from bs4 import BeautifulSoup
import time

driver = webdriver.Firefox()

driver.get("https://www.letterboxd.com/films/popular/page/1/")

elements = driver.find_elements("class_name", "frame")

print(elements)

time.sleep(5)

driver.quit()
