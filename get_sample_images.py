import datetime
import pathlib
import sys

import requests
import bs4

import raceml


def get_image(name):
    """
    Returns the URL of the first image found.
    """

    response = requests.get("https://www.google.com/search?tbm=isch&q=" + name)
    soup = bs4.BeautifulSoup(response.content, "html.parser")

    return soup.find("img", {"class": "DS1iW"}).get("src")


def download_images(data_folder, database_lock):
    database_lock.check()

    athlete_folder = data_folder / "athletes"
    athlete_photos_folder = data_folder / "athlete_photos"

    for athlete_path in athlete_folder.glob("**/*.yaml"):
        athlete_data = raceml.load(athlete_path)
        athlete_name = athlete_data["name"]

        athlete_path_relative = athlete_path.relative_to(athlete_folder)

        if any(
            athlete_photos_folder.glob(str(athlete_path_relative.with_suffix(".*")))
        ):
            continue

        image_url = get_image(athlete_name)
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        image_extension = pathlib.Path(image_url).suffix
        if not image_extension:
            image_extension = image_response.headers["Content-Type"].split("/")[-1]

        image_filepath = athlete_photos_folder / (
            athlete_path_relative.stem + "." + image_extension
        )

        with open(image_filepath, "wb") as f:
            f.write(image_response.content)


if __name__ == "__main__":
    start_time = datetime.datetime.now()

    if len(sys.argv) > 1:
        data_folder = pathlib.Path(sys.argv[1])
    else:
        data_folder = pathlib.Path(input("PATH:"))

    database_lock = raceml.DatabaseLock(data_folder)
    database_lock.acquire()
    try:
        download_images(data_folder, database_lock)
    finally:
        database_lock.release()

    print("Time taken:", datetime.datetime.now() - start_time)
