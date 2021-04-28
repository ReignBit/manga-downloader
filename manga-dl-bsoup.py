"""
    Manga-downloader v2 (BeautifulSoup Edition) by ReignBit

    Improved version of the manga-downloader, this time we use BS4 instead of regex to find the pages.
    I've also removed the curses implementation since that caused a few issues, we instead just print to screen
    so that introduces the issue of multiple threads writing at the sametime, but it's fine for now.

    HOW TO USE:
        python manga-dl-bsoup.py [-h] URL FOLDER_PATH MANGA_NAME
    
    TODO:
        - Introduce a lock for printing to limit multiple threads printing at once causing new line issues
        - Add download percentage / percentage complete
        - Add arguments to specify own worker and chapter counts.
        - Add arguments for page tag specification to allow use for other sites other  than Manganelo.
        - Improve generation of chapter pages by adding more styling and an "end of manga" message instead of linking to a 404 file.
    
    WISHLIST:    
        - Add arguments to omit certain chapters?
"""


import argparse
import threading
import os
import requests
import random
from typing import List
from bs4 import BeautifulSoup

import colorama


# For colors on Windows consoles.
colorama.init()

MANGA_NAME = None
THREAD_PROGRESS = {}
HTML_STYLE = """<style>
html, body {
    height: 100%;
    margin: 0;
    padding: 0;
    background-color:black;
    text-color: white;
}

img {
    padding: 0;
    display: block;
    margin: 0 auto;
    max-height: 100%;
    max-width: 100%;
}</style>"""


def download_chapter(soup) -> List[bytes]:
    """Parses the chapter page and looks for any <img> with
    attributes matching those which are the manga pages

    Returns: List of bytes
    """
    img_urls = soup.find_all("img", attrs={"class": "img-loading"})

    if len(img_urls) == 0:
        return

    img_data = []
    for url in img_urls:
        # This website is weird and sometimes has `src` for the img attrib, and sometimes `data-src`
        # so we need to check for either of these...
        img = requests.get(url.get('src', url.get('data-src', "0.0.0.0")))
        if img.status_code == 200:
            # Successful fetch of image, let's add to list.
            img_data.append(img.content)
    return img_data


def save_chapter(imgs, chapter_num) -> None:
    """Takes a list of image bytes and saves them to disk"""
    for i, img in enumerate(imgs):
        with open(os.path.join(MANGA_NAME, str(chapter_num), str(i) + ".jpg"), "wb") as f:
            f.write(img)


def worker(url, start, batch_count, id, color):
    # For each chapter and it's subchapters (hence the * 10)
    # We * 10 since we cannot increase in float intervals, so we just / 10
    # to get the chapter and subchapter.
    for x in range(start * 10, batch_count * 10):
        chapter = x / 10

        # Whole chapters must be a single int instead of chapter_1.0
        if str(chapter).endswith(".0"):
            chapter = int(chapter)
            print("%sThread-%i: Scraping chapter %s...\033[0;0m" % (color, id, chapter))

        page = requests.get(url + str(chapter))

        if page.status_code == 200:
            # Create chapter folder
            if not os.path.exists(os.path.join(MANGA_NAME, str(chapter))):
                    os.makedirs(os.path.join(MANGA_NAME, str(chapter)))

            # Scraper creation & download chapter images.
            soup = BeautifulSoup(page.text, 'html.parser')
            imgs = download_chapter(soup)
            save_chapter(imgs, chapter)
            THREAD_PROGRESS[id] = (x - start) / (batch_count * 10) * 100


def generate_chapter_links():
    with open(os.path.join(MANGA_NAME, "index.html"), "w") as f:
        f.write("<body style='background-color:#000'><a href='0/index.html'> Start Reading! </a></body>")

    chapters = os.listdir(MANGA_NAME).sort()
    for folder in os.listdir(os.path.join(MANGA_NAME)):
        path = os.path.join(MANGA_NAME, folder)
        if os.path.isdir(path):
            with open(path + "/" + "index.html", "w") as f:
                f.write(HTML_STYLE)
                for image in os.listdir(path):
                    if image.endswith(".jpg"):
                        f.write("<img src={}>".format(image))
                f.write("<a href=../{}/index.html>Next Chapter!</a>".format(int(folder) + 1))


def fetch_mangas(url, workers=1, chapters=1):
    """Create worker threads to download chapters in batches
        Defaults to 200 chapters with 5 workers.
        1 Chapter == 10 subchapters (1.1, 1.2, ..., 1.9)
    """

    threads = []
    batch_count = int(chapters / workers)
    colors = ["\033[1;30m", "\033[1;31m", "\033[1;32m", "\033[1;33m", "\033[1;34m", "\033[1;35m", "\033[1;36m", "\033[0;31m", "\033[0;35m", "\033[0;41m"]

    # Thread creation
    for x in range(workers):
        start = x * batch_count
        id = x
        color = random.choice(colors)
        print("{}Creating Thread-{} starting at chapter {} and working up to chapter {}\033[0;0m".format(color, id, start, batch_count + start + 1))
        threads.append(threading.Thread(target=worker, args=(url, start, batch_count + start + 1, id, color)))

    # Thread starting
    # I'm pretty sure we can't do these all in the same for loop since then we would launch one thread
    # at a time and block until the thread is finished
    # effectively making a single-threaded multi-threaded program, lol.
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    generate_chapter_links()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("folderpath")
    parser.add_argument("name")
    args = parser.parse_args()

    MANGA_NAME = args.folderpath

    if not os.path.exists(args.folderpath):
        os.makedirs(args.folderpath)
    
    fetch_mangas(args.url)
