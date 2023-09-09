import csv
import datetime
import pathlib
from pprint import pprint
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
        if race_name != row["Race Name"]:
            raise ValueError(
                f"race_name {race_name!r} doesn't match {row['Race Name']!r}"
            )
        if race_start_time > row["Race Start Date/Time"]:
            race_start_time = row["Race Start Date/Time"]

        athlete_data = {
            "name": (row["First Name"] + " " + row["Last Name"]).title(),
            "gender": row["Sex"].lower(),
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
                yaml.dump(athlete_data, f, sort_keys=False)

        athlete_result = {}

        if row["Finishing Time (in seconds)"]:
            athlete_result["finish_time"] = simple_tally.number(
                row["Finishing Time (in seconds)"]
            )

        if sanitized_name in race_results.values():
            raise ValueError(f"Duplicate athlete name: {sanitized_name}")
        else:
            if not row["Finishing Time (in seconds)"]:
                if row["Finishing Time"] in ["DNS", "DNF"]:
                    athlete_result[row["Finishing Time"]] = True
                else:
                    raise ValueError(f"Missing finish time for {sanitized_name}, {row}")
            elif row["Laps Remaining"] != "0":
                raise ValueError(f"Missing finish time for {sanitized_name}, {row}")

            race_results[sanitized_name] = athlete_result

        for k, v in athlete_data.items():
            if not v:
                print(f"Missing value for {k}, filename {sanitized_name}.yaml")

    if "Duathlon Short Course" in race_name:
        race_distance = "duathlon_short_course"
    elif "Duathlon Sprint" in race_name:
        race_distance = "duathlon_sprint"
    elif "Duathlon Olympic" in race_name:
        race_distance = "duathlon_olympic"
    else:
        raise ValueError(
            f"Race name {race_name} does not match any specified distances."
        )

    # create the results file
    results_file_json = {
        "type": "race",
        "name": race_name,
        "distance": race_distance,
        "date": race_start_time,
        "results": race_results,
    }

    # write the results file
    race_name_sanitized = re.sub(r"[^a-zA-Z0-9]", "_", race_name).lower()
    race_filename = results_folder / f"{race_name_sanitized}.yaml"

    if race_filename.exists():
        # check if the race data matches
        with race_filename.open() as f:
            existing_data = yaml.safe_load(f)
        if existing_data != results_file_json:
            raise ValueError(
                f"Existing race data {existing_data} doesn't match {results_file_json}"
            )
    else:
        with race_filename.open("w") as f:
            yaml.dump(results_file_json, f, sort_keys=False)


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
