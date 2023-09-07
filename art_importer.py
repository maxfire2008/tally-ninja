import csv
import datetime
import pathlib
import re
import yaml
import pandas
import simple_tally
import shutil
import time


def import_agee_race_timing(input: pathlib.Path, data_folder: pathlib.Path):
    athletes_folder = data_folder / "athletes"
    athletes_folder.mkdir(parents=True, exist_ok=True)

    results_folder = data_folder / "results"

    # read the input file as a dict with headers
    with open(input, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    race_results = {}

    race_name = rows[0]["Race Name"]
    for row in rows:
        if race_name != row["Race Name"]:
            raise ValueError(
                f"race_name {race_name!r} doesn't match {row['Race Name']!r}"
            )

        athlete_data = {
            "name": row["First Name"] + " " + row["Last Name"],
            "gender": row["Sex"],
            "dob": datetime.datetime.strptime(row["DOB"], "%d/%m/%Y")
            .date()
            .isoformat(),
            "email": row["Email"],
        }

        # check if the athlete already exists
        # sanitize the name

        sanitized_name = re.sub(r"[^a-zA-Z0-9]", "_", athlete_data["name"]).lower()
        athlete_filename = athletes_folder / f"{sanitized_name}.yaml"

        if athlete_filename.exists():
            # check if the athlete data matches
            with athlete_filename.open() as f:
                existing_data = yaml.safe_load(f)
            if existing_data != athlete_data:
                raise ValueError(
                    f"Existing athlete data {existing_data} doesn't match {athlete_data}"
                )
        else:
            with athlete_filename.open("w") as f:
                yaml.dump(athlete_data, f)

        finish_time = row["Finishing Time (in seconds)"]

        if sanitized_name in race_results.values():
            raise ValueError(f"Duplicate athlete name: {sanitized_name}")
        else:
            race_results[sanitized_name] = finish_time

    print(race_results)


def art_watch(input, data_folder):
    # register watch on the files in the input folder
    # when a file is created, read it and process it, then delete it

    watch_folder = pathlib.Path(input)
    data_folder = pathlib.Path(data_folder)

    # create the input folder if it doesn't exist
    watch_folder.mkdir(parents=True, exist_ok=True)

    # this file content
    code_content = open(__file__, "rb").read()

    while True:
        if open(__file__, "rb").read() != code_content:
            print("Code changed, exiting")
            return

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
                        proposed_filename = (
                            data_folder
                            / "cache"
                            / f"art_importer_{int(time.time()*1000)}.racecache"
                        )
                        proposed_filename.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(file, proposed_filename)
                        break
                    except PermissionError:
                        sleep_time = min(0.1 * 2**i, 15)
                        print(f"Waiting {sleep_time}s to use {file}")
                        time.sleep(sleep_time)

                import_agee_race_timing(proposed_filename, data_folder)
                print(f"Processed {file}")
        time.sleep(2)


if __name__ == "__main__":
    art_watch(
        pathlib.Path.home() / "Desktop" / "ART-Sport-Scorer-Watch",
        "../sport-scorer-sample-data/art/",
    )
