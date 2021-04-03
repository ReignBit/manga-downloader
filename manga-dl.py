"""
                            Manga Downloader from Manganelo
                                        By Bit
    HOW TO USE:
        Run `manga-dl -h` for help.

    ERRORS:
        If the program fails to download all chapers/images then ensure the following:
            -   The URL parameter is set correctly.
            -   Check if Manganelo's CDN has changed.
            -   Ensure the program has read/write access to the folder/cwd it is in.
"""

# TODO: Add Total Left To Download by collecting all Content-Lengths of the images before download


import argparse
import curses
import math
import threading
import os
import requests
import re

# ********* OPTIONS **************
ANIME_NAME = "Unnamed Manga"
MAX_VOLUME = 200  # Volume to search up to
WORKER_COUNT = 10  # How many workers to use
REGEX = r"https:\/\/cm.blazefast.co\/[a-z0-9]{2}\/[a-z0-9]{2}\/[a-z0-9]{32}.jpg"  # CDN link
URL = ""  # Manganelo link
# ********************************

pattern = re.compile(REGEX, re.IGNORECASE)
scr = curses.initscr()
total_downloaded = []


def get_url_friendly_number(num):
    """Return string formatted to match chapters on Manganelo"""
    new = str(round(num, 1))
    if ".0" in new:
        return str(int(num))
    return new


def wprint(worker, msg):
    """Print to the screen via curses"""
    scr.addstr(worker+5, 0, "[WORKER {}] {}".format(worker, msg))

    total = 0
    for t in total_downloaded:
        total += t

    # scr.addstr(WORKER_COUNT+6, 59, f"Total Downloaded: {(total / 1.049e+6):,.2f} MB")
    scr.refresh()


def create_workers(batch):
    """Create worker threads with correct start,stop and batch args"""
    threads = []
    start_volume = 1
    for x in range(0, WORKER_COUNT):
        end = start_volume + batch - 1
        print(f"Created worker for (START: {start_volume}, END: {end}, BATCH: {batch})")
        threads.append(threading.Thread(target=worker, args=(start_volume, batch, x)))
        start_volume = end + 1

        total_downloaded.append(0)
    return threads


def pre_download_size_calc(url):
    data = requests.head(url)
    if data.status_code == 200:
        return int(data.headers['Content-Length'])
    return 0


def pre_download_images(imgs):
    size = 0
    for img in imgs:
        size += pre_download_size_calc(img)
    return size


def pre_download_chapter(chapter):
    """Collect chapter size information"""
    url_friendly = get_url_friendly_number(chapter)
    resp = requests.get(URL + "{}".format(url_friendly))
    total_bytes = len(resp.content)
    if resp.status_code == 200:
        imgs = pattern.findall(resp.content.decode("utf-8"))
        total_bytes += pre_download_images(imgs)
    return total_bytes


def get_img(URL):
    """Download and return image from url"""
    data = requests.get(URL)
    if data.status_code == 200:
        return data.content
    return None


def download_images(location, imgs):
    """Bulk download images and store to disk"""
    img_count = 0
    total_bytes = 0.0
    for img in imgs:
        data = get_img(img)
        if data:
            total_bytes += len(data)
            try:
                os.mkdir(location)
            except FileExistsError:
                pass

            with open(f"{location}/{img_count}.jpg", "wb") as f:
                f.write(data)
            img_count += 1
        else:
            scr.addstr(0, 20, "Failed to download all images!")
    return total_bytes


def download_chapter(chapter):
    """Attempt to download a chapter's worth of images"""
    url_friendly = get_url_friendly_number(chapter)
    resp = requests.get(URL + "{}".format(url_friendly))
    total_bytes = len(resp.content)
    if resp.status_code == 200:
        imgs = pattern.findall(resp.content.decode("utf-8"))
        total_bytes += download_images(f"{ANIME_NAME}/chapter_{url_friendly}", imgs)
    return total_bytes


def worker(start, batch: int, name):
    """Worker thread function"""
    global total_downloaded

    to_download = 0.0
    for x in range(start, start + batch * 10):
        wprint(name, "Starting worker" + "."*(int(x/2) % 10))
        to_download += pre_download_chapter(start + (x / 10))

    count = 0
    while count <= batch * 10:
        wprint(name, "{}/{} ({:.2f}%) Chapters completed".format(
            count, batch * 10, count / (batch * 10) * 100)
        )
        scr.addstr(name+5, 65, f"{(total_downloaded[name] / 1.049e+6):,.2f} MB / {to_download / 1.049e+6:,.2f} MB")

        total_downloaded[name] += download_chapter(start + (count/10))
        count += 1
    scr.addstr(name+5, 55, "Done!")


def partition(A, lo, hi):
    pivot = A[hi]
    i = lo
    for j in range(lo, hi):
        if A[j] < pivot:
            tmp = A[j]
            A[j] = A[i]
            A[i] = tmp
    tmp = A[hi]
    A[hi] = A[i]
    A[i] = tmp
    return i


def quicksort(A, lo, hi):
    if lo < hi:
        p = partition(A, lo, hi)
        quicksort(A, lo, p - 1)
        quicksort(A, p + 1, hi)


def sort_chapters():
    """Sort chapter folder names with Quicksort"""
    nums = []
    for item in os.listdir(ANIME_NAME):
        nums.append(float(item[8:]))
    quicksort(nums, 0, len(nums) - 1)

    sorted_list = []
    for item in nums:
        sorted_list.append(f"chapter_{get_url_friendly_number(item)}")
    return sorted_list


def generate_webpages():
    """Generate chapter htmls for easy viewing"""
    chapters = os.listdir(ANIME_NAME)
    chapters = sort_chapters()
    for chapter in chapters:
        next_chapter = (chapters.index(chapter) + 1) % len(chapters)

        with open(f"{ANIME_NAME}/{chapter}/chapter.html", "w") as f:
            f.write("""<style>
html, body {
    height: 100%;
    margin: 0;
    padding: 0;
    background-color:black;
}

img {
    padding: 0;
    display: block;
    margin: 0 auto;
    max-height: 100%;
    max-width: 100%;
}</style>""")
            num_of_imgs = len(os.listdir(f"{ANIME_NAME}/{chapter}")) - 1

            for x in range(num_of_imgs):
                f.write(f"<img src='{x}.jpg'></br>\n")

            if len(chapters)-1 == chapters.index(chapter):
                f.write("<h1>End of manga!</h1><h3>To download more, run the following command: `manga-dl <MANGA URL>`</h3")
                return

            f.write(f"<a href='../{chapters[next_chapter]}/chapter.html'>Next Chapter</a>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mangaurl", help="Manganelo url of the manga to download.")
    parser.add_argument("--workers", "-w", type=int, default=10, help="Amount of workers to create.")
    parser.add_argument("--chapters", "-c", type=int, default=100, help="Amount of chapters/volumes to attempt to download.")
    parser.add_argument("--cdnregex", "-r", type=str, help="Change the CDN regex used to match image urls.")
    parser.add_argument("--manganame", "-m", default="Unnamed Manga", help="Name of the folder to store downloaded chapters.")
    args = parser.parse_args()

    URL = args.mangaurl
    WORKER_COUNT = args.workers if args.workers else 5
    MAX_VOLUME = args.chapters if args.chapters else 200
    REGEX = args.cdnregex if args.cdnregex else r"https:\/\/cm.blazefast.co\/[a-z0-9]{2}\/[a-z0-9]{2}\/[a-z0-9]{32}.jpg"
    ANIME_NAME = args.manganame if args.manganame else "Unnamed Manga"

    scr.addstr(0, 0, "============Manga-Downloader===========")
    scr.addstr(1, 0, "    Saving as  : {}".format(ANIME_NAME))
    scr.addstr(4, 0, "============Worker Progress=============")

    try:
        os.mkdir(ANIME_NAME)
    except FileExistsError:
        pass

    threads = create_workers(math.ceil(MAX_VOLUME / WORKER_COUNT))
    for w in threads:
        w.start()

    for w in threads:
        w.join()

    curses.endwin()  # pylint: disable=no-member
    print("Finished downloading.")
    print("Creating view pages...")
    generate_webpages()
    print(f"Finished! Goto {os.getcwd()}/{ANIME_NAME}/chapter_1/chapter.html to view!")
    print("\n\nPress any button to exit...")
    input()
