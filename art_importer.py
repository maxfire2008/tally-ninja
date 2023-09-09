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
    results_folder.mkdir(parents=True, exist_ok=True)

    # read the input file as a dict with headers
    with open(input, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    race_results = {}

    race_name = rows[0]["Race Name"]
    race_start_time = rows[0]["Race Start Date/Time"]
    for row in rows:
        print(row)
        if race_name != row["Race Name"]:
            raise ValueError(
                f"race_name {race_name!r} doesn't match {row['Race Name']!r}"
            )
        if race_start_time > row["Race Start Date/Time"]:
            race_start_time = row["Race Start Date/Time"]

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

    if "Short Course" in race_name:
        pass

    # create the results file
    results_file_json = {
        "type": "race",
        "name": race_name,
        "date": race_start_time,
    }


def process_folder(input_folder, data_folder):
    input_folder = pathlib.Path(input_folder)
    data_folder = pathlib.Path(data_folder)
    data_folder.mkdir(parents=True, exist_ok=True)

    for filename in input_folder.glob("*.csv"):
        if filename.is_file():
            import_agee_race_timing(filename, data_folder)


if __name__ == "__main__":
    process_folder(
        "../sport-scorer-sample-data/trisouth_art_exports/",
        "../sport-scorer-sample-data/art/",
    )
