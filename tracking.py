import pandas as pd
import time
import os
import platform

def clear_terminal():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

while True:
    users = pd.read_csv("user_reviews_multithread.csv", on_bad_lines='skip')
    users = users.drop_duplicates()
    df_shape = users.shape
    df_duplicated = users.duplicated().any()
    df_users_unique  = users.user.nunique()
    df_movies_unique = users.movie.nunique()
    currently_scraping = users.groupby("movie").size()[users.groupby("movie").size() < 720]
    clear_terminal()
    print("Dataframe shape:", df_shape)
    print("Duplicates:", df_duplicated)
    print("Unique users:", df_users_unique)
    print("Unique movies: ", df_movies_unique)
    print()
    print(f"Pages completed: {df_movies_unique / 72:.2f}")
    print()
    print("Currently scraping:")
    print(currently_scraping)

    del users

    time.sleep(3)
