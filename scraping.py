from selenium import webdriver
from bs4 import BeautifulSoup
import time

driver = webdriver.Firefox()

driver.get("https://www.letterboxd.com/films/popular/page/1/")

time.sleep(5)

driver.quit()
