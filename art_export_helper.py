import csv
import pathlib
import re
import shutil
import time


def extract_race_name(input: pathlib.Path):
    # read the input file as a dict with headers
    with open(input, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    race_name = rows[0]["Race Name"]
    for row in rows:
        if race_name != row["Race Name"]:
            raise ValueError(
                f"race_name {race_name!r} doesn't match {row['Race Name']!r}"
            )
    return race_name


def art_watch(input, export_folder):
    # register watch on the files in the input folder
    # when a file is created, read it and process it, then delete it

    watch_folder = pathlib.Path(input)
    export_folder = pathlib.Path(export_folder)

    # create the input folder if it doesn't exist
    watch_folder.mkdir(parents=True, exist_ok=True)

    while True:
        for file in watch_folder.iterdir():
            if (
                file.is_file()
                and file.stem == "sport-scorer-temp"
                and file.suffix == ".csv"
            ):
                # process the file
                print(f"Processing {file}")

                for i in range(10):
                    try:
                        n = None
                        while True:
                            proposed_filename = export_folder / (
                                re.sub(r"[^a-zA-Z0-9]", "_", extract_race_name(file))
                                + (f"_{n}" if n else "")
                                + ".csv"
                            )
                            print(proposed_filename)
                            proposed_filename.parent.mkdir(parents=True, exist_ok=True)

                            if proposed_filename.exists():
                                if proposed_filename.read_bytes() == file.read_bytes():
                                    print(f"File {file} already processed")
                                    break
                                else:
                                    if n:
                                        n += 1
                                    else:
                                        n = 1
                            else:
                                break

                        shutil.move(file, proposed_filename)
                        break
                    except PermissionError:
                        sleep_time = min(0.1 * 2**i, 15)
                        print(f"Waiting {sleep_time}s to use {file}")
                        time.sleep(sleep_time)
                print(f"Processed {file}")
        time.sleep(2)


if __name__ == "__main__":
    art_watch(
        pathlib.Path.home() / "Desktop" / "ART-Sport-Scorer-Watch",
        "../sport-scorer-sample-data/trisouth_art_exports/",
    )
