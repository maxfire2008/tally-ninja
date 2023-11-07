"""Imports data from Sports Tracker.
"""
import csv
import datetime
import math
import pathlib
import re
import sys
import yaml
import pandas
import raceml


def import_students(file, output, year, database_lock):
    if not isinstance(file, pathlib.Path):
        file = pathlib.Path(file).resolve()
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file}")
    if not isinstance(output, pathlib.Path):
        output = pathlib.Path(output).resolve()
        output.mkdir(parents=True, exist_ok=True)
    with open(file, encoding="utf-8") as f:
        reader = csv.DictReader(
            f,
            fieldnames=[
                "firstname",
                "lastname",
                "email",
                "dob",
                "gender",
                "team",
                "year_group",
            ],
        )

        for student in reader:
            for required_field in [
                "firstname",
                "lastname",
                "dob",
                "gender",
                "team",
                "year_group",
            ]:
                if not student[required_field]:
                    print(
                        f"Missing required field \"{required_field}\" for student {student['firstname']} {student['lastname']}"
                    )

            student_raceml = {}
            student_raceml["name"] = " ".join(
                [student["firstname"], student["lastname"]]
            )
            student_raceml["email"] = student["email"]
            # convert from DD-MM-YYYY to ISO 8601
            student_raceml["dob"] = datetime.datetime.strptime(
                student["dob"], "%d-%m-%Y"
            ).date()

            student_raceml["gender"] = student["gender"]
            student_raceml["team"] = student["team"]
            if re.match(r"^Year ([7-9]|10)$", student["year_group"]):
                student_raceml["ystart"] = year - int(student["year_group"][5:])

            student_file = (
                output
                / f"{student['firstname'].lower().replace(' ', '-')}-{student['lastname'].lower().replace(' ', '-')}-{student_raceml['ystart']}.yaml"
            )
            while True:
                if student_file.exists():
                    # check if identical
                    with open(student_file, encoding="utf-8") as f:
                        existing_student = yaml.safe_load(f)
                        if existing_student == student_raceml:
                            break
                        print(
                            f"Student {student['firstname']} {student['lastname']} already exists but is different"
                        )
                        # add a number to the end of the filename
                        stem = student_file.stem
                        # if the filename already has a number, increment it
                        if re.match(r".*-([0-9]+)-([0-9]+)$", stem):
                            stem = re.sub(
                                r"([0-9]+)$",
                                lambda x: str(int(x.group(1)) + 1),
                                stem,
                            )
                        else:
                            stem += "-1"
                        student_file = student_file.with_stem(stem)
                else:
                    with open(student_file, "w", encoding="utf-8") as f:
                        yaml.dump(student_raceml, f)
                    break


def import_results(file, athletes_directory, output, year, database_lock):
    if not isinstance(athletes_directory, pathlib.Path):
        athletes_directory = pathlib.Path(athletes_directory).resolve()
    if not athletes_directory.exists():
        raise FileNotFoundError(f"Directory not found: {athletes_directory}")
    if not isinstance(output, pathlib.Path):
        output = pathlib.Path(output).resolve()
        output.mkdir(parents=True, exist_ok=True)
    with open(file, "rb") as spreadsheet:
        results = pandas.read_excel(spreadsheet, sheet_name=None)

        # iterate through each sheet
        for _, sheet in results.items():
            event_json = None
            # D4 is the cell containing the event name
            event_name = sheet.iloc[2, 3]
            if re.match(
                r"^#[0-9]+ [0-9]+ metres Year ([7-9]|10) (fe)?male$", event_name
            ):
                event_name_split = event_name.split(" ")
                event_number = event_name_split[0][1:]
                event_distance = event_name_split[1]
                event_year = event_name_split[4]
                event_gender = event_name_split[5]
                date_start = datetime.datetime(2023, 9, 2, 9, 0, 0)
                date_start += datetime.timedelta(minutes=(int(event_number) - 1) * 10)
                event_json = {
                    "type": "race",
                    "name": f"{event_distance}m Track Year {event_year} {event_gender}",
                    "distance": event_distance + "m",
                    "gender": event_gender,
                    "ystart": year - int(event_year),
                    "date": date_start,
                    "results": {},
                }

                # iterate through rows B7:F(INFINITY)
                for row in range(5, sheet.shape[0]):
                    # C: Name, E: Result
                    # John Doe, 14s 600ms
                    name = sheet.iloc[row, 2]
                    name_split = name.split(" ")
                    result = sheet.iloc[row, 4]
                    points = sheet.iloc[row, 5]
                    filename = (
                        "-".join(name_split[0:2]).lower()
                        + "-"
                        + str(event_json["ystart"])
                        # + "*"
                    )

                    # ensure that the athlete exists
                    raceml.lookup_athlete(filename, athletes_directory, database_lock)

                    result_in_milliseconds = None
                    if re.match(r"^[0-9]+m [0-9]+s [0-9]+ms$", result):
                        result_split = result.split(" ")
                        result_in_milliseconds = (
                            int(result_split[0][:-1]) * 60 * 1000
                            + int(result_split[1][:-1]) * 1000
                            + int(result_split[2][:-2])
                        )
                    elif re.match(r"^[0-9]+s [0-9]+ms$", result):
                        result_split = result.split(" ")
                        result_in_milliseconds = int(result_split[0][:-1]) * 1000 + int(
                            result_split[1][:-2]
                        )
                    else:
                        print(f"Invalid result: {result}")

                    current_result_json = {
                        "finish_time": result_in_milliseconds,
                        "_debug_points": points,
                    }
                    try:
                        int(points)
                    except ValueError:
                        if points in ["DQ", "DNF"]:
                            current_result_json[points] = True
                        else:
                            raise ValueError(f"Invalid points: {points}")
                    event_json["results"][filename] = current_result_json
            elif re.match(
                r"^#[0-9]+ [0-9]+ ?m (freestyle|backstroke|breaststroke|butterfly) Year ([7-9]|10) (fe)?male$",
                event_name,
            ):
                event_name = event_name.replace(" m ", "m ")
                event_name_split = event_name.split(" ")
                event_number = event_name_split[0][1:]
                event_distance = event_name_split[1][:-1]
                event_type = event_name_split[2]
                event_year = event_name_split[4]
                event_gender = event_name_split[5]
                date_start = datetime.datetime(2023, 9, 2, 9, 0, 0)
                date_start += datetime.timedelta(minutes=(int(event_number) - 1) * 10)
                event_json = {
                    "type": "race",
                    "name": f"{event_distance}m {event_type} Year {event_year} {event_gender}",
                    "distance": event_distance + "m",
                    "gender": event_gender,
                    "ystart": year - int(event_year),
                    "date": date_start,
                    "results": {},
                }

                # iterate through rows B7:F(INFINITY)
                for row in range(5, sheet.shape[0]):
                    # C: Name, E: Result
                    # John Doe, 14s 600ms
                    name = sheet.iloc[row, 2]
                    name_split = name.split(" ")
                    result = sheet.iloc[row, 4]
                    points = sheet.iloc[row, 5]
                    filename = (
                        "-".join(name_split[0:2]).lower()
                        + "-"
                        + str(event_json["ystart"])
                        # + "*"
                    )

                    # ensure that the athlete exists
                    raceml.lookup_athlete(filename, athletes_directory, database_lock)

                    result_in_milliseconds = None
                    if isinstance(result, float) and math.isnan(result):
                        result = ""
                    if re.match(r"^[0-9]+m [0-9]+s [0-9]+ms$", result):
                        result_split = result.split(" ")
                        result_in_milliseconds = (
                            int(result_split[0][:-1]) * 60 * 1000
                            + int(result_split[1][:-1]) * 1000
                            + int(result_split[2][:-2])
                        )
                    elif re.match(r"^[0-9]+s [0-9]+ms$", result):
                        result_split = result.split(" ")
                        result_in_milliseconds = int(result_split[0][:-1]) * 1000 + int(
                            result_split[1][:-2]
                        )
                    else:
                        print(
                            f"Invalid result: {result!r} for {name!r} in {event_name!r} ({event_number!r})"
                        )

                    current_result_json = {
                        "finish_time": result_in_milliseconds,
                        "_debug_points": points,
                    }

                    try:
                        int(points)
                    except ValueError:
                        if points in ["DQ", "DNF"]:
                            current_result_json[points] = True
                        else:
                            raise ValueError(f"Invalid points: {points}")

                    event_json["results"][filename] = current_result_json
            elif re.match(
                r"^#[0-9]+ (Long jump|Javelin throw|Triple jump|Shot put|Discus throw) Year ([7-9]|10) (fe)?male$",
                event_name,
            ):
                event_name_split = event_name.split(" ")
                if len(event_name_split) == 6:
                    event_number = event_name_split[0][1:]
                    event_year = event_name_split[4]
                    event_gender = event_name_split[5]
                    event_type = event_name_split[1:3]
                else:
                    raise ValueError(f"Invalid event name: {event_name}")
                date_start = datetime.datetime(2023, 9, 2, 9, 0, 0)
                date_start += datetime.timedelta(minutes=(int(event_number) - 1) * 10)
                event_json = {
                    "type": "_".join(event_type).lower(),
                    "name": " ".join(event_type).title()
                    + f" Year {event_year} {event_gender}",
                    "gender": event_gender,
                    "ystart": year - int(event_year),
                    "date": date_start,
                    "results": {},
                }

                # iterate through rows B7:F(INFINITY)
                for row in range(5, sheet.shape[0]):
                    name = sheet.iloc[row, 2]
                    name_split = name.split(" ")
                    result = sheet.iloc[row, 4]
                    points = sheet.iloc[row, 5]

                    filename = (
                        "-".join(name_split[0:2]).lower()
                        + "-"
                        + str(event_json["ystart"])
                        # + "*"
                    )
                    raceml.lookup_athlete(filename, athletes_directory, database_lock)

                    # 1 4m 60cm2 metersm centimeterscm3 metersm centimeterscm
                    # 1: 4600
                    # 1 4m 30cm2 4m 12cm3 metersm centimeterscm
                    # 1: 4300, 2: 4120
                    # 1 4m 22cm2 metersm centimeterscm3 metersm centimeterscm
                    # 1: 4220

                    current_result = None

                    if re.match(
                        r"^1 ([0-9]*|meters)m ([0-9]*|centimeters)cm2 ([0-9]*|meters)m ([0-9]*|centimeters)cm3 ([0-9]*|meters)m ([0-9]*|centimeters)cm$",
                        result,
                    ):
                        current_result = []
                        results_split = result.split("cm")
                        # ['1 4m 30', '2 4m 12', '3 metersm centimeters', '']
                        for result_split in results_split:
                            if not result_split:
                                continue
                            result_split_split = result_split.split(" ")
                            # ['1', '4m', '30']
                            try:
                                r = (
                                    int(result_split_split[1][:-1]) * 1000
                                    + int(result_split_split[2]) * 10
                                )
                                if r:
                                    current_result.append(r)
                            except ValueError:
                                pass
                    else:
                        print(f"Invalid result: {result}")

                    current_result_json = {
                        "distances": current_result,
                        "_debug_points": points,
                    }
                    try:
                        int(points)
                    except ValueError as error:
                        if points in ["DQ", "DNF"]:
                            current_result_json[points] = True
                        else:
                            raise ValueError(f"Invalid points: {points}") from error
                    event_json["results"][filename] = current_result_json
            elif re.match(
                r"^#[0-9]+ High jump Year ([7-9]|10) (fe)?male$",
                event_name,
            ):
                event_name_split = event_name.split(" ")
                event_number = event_name_split[0][1:]
                event_year = event_name_split[4]
                event_gender = event_name_split[5]

                date_start = datetime.datetime(2023, 9, 2, 9, 0, 0)
                date_start += datetime.timedelta(minutes=(int(event_number) - 1) * 10)
                event_json = {
                    "type": "high_jump",
                    "name": f"High jump Year {event_year} {event_gender}",
                    "gender": event_gender,
                    "ystart": year - int(event_year),
                    "date": date_start,
                    "results": {},
                }

                # iterate through rows B7:F(INFINITY)
                for row in range(5, sheet.shape[0]):
                    name = sheet.iloc[row, 2]
                    name_split = name.split(" ")
                    result = sheet.iloc[row, 4]
                    points = sheet.iloc[row, 5]

                    filename = (
                        "-".join(name_split[0:2]).lower()
                        + "-"
                        + str(event_json["ystart"])
                        # + "*"
                    )
                    athlete = raceml.lookup_athlete(
                        filename, athletes_directory, database_lock
                    )

                    current_result = {}

                    # 1m 20cm1m 25cm1m 35cm1m 40cm1m 45cm1m 50cm1m 55cm1m 60cm
                    results_split = result.split("cm")
                    # ['1m 20', '1m 25', '1m 35', '1m 40', '1m 45', '1m 50', '1m 55', '1m 60', '']

                    for result_split in results_split:
                        if not result_split:
                            continue
                        result_split_split = result_split.split(" ")
                        # ['1m', '20']
                        try:
                            r = (
                                int(result_split_split[0][:-1]) * 1000
                                + int(result_split_split[1]) * 10
                            )
                            if r:
                                current_result[r] = []
                        except ValueError:
                            pass

                    current_result_json = {
                        "heights": current_result,
                        "_debug_points": points,
                    }
                    try:
                        int(points)
                    except ValueError as error:
                        if points in ["DQ", "DNF"]:
                            current_result_json[points] = True
                        else:
                            raise ValueError(f"Invalid points: {points}") from error
                    event_json["results"][filename] = current_result_json
            elif re.match(
                r"^#[0-9]+ 4x100 metres relay Year ([7-9]|10) (fe)?male$",
                event_name,
            ):
                event_name_split = event_name.split(" ")
                event_number = event_name_split[0][1:]
                event_year = event_name_split[5]
                event_gender = event_name_split[6]

                date_start = datetime.datetime(2023, 9, 2, 9, 0, 0)
                date_start += datetime.timedelta(minutes=(int(event_number) - 1) * 10)
                event_json = {
                    "type": "race",
                    "scoring_type": "relay",
                    "competitor_type": "team",
                    "name": f"4x100m Track Relay Year {event_year} {event_gender}",
                    "distance": event_distance + "m",
                    "gender": event_gender,
                    "ystart": year - int(event_year),
                    "date": date_start,
                    "results": {},
                }

                # iterate through rows B7:F(INFINITY)
                for row in range(5, sheet.shape[0]):
                    # C: Name, F: Points
                    # Crayfish, 40

                    name = sheet.iloc[row, 2]
                    points = sheet.iloc[row, 5]

                    try:
                        points = int(points)
                    except ValueError:
                        points = 0

                    current_result_json = {
                        "points": points,
                        "_debug_points": points,
                    }
                    try:
                        int(points)
                    except ValueError:
                        if points in ["DQ", "DNF"]:
                            current_result_json[points] = True
                        else:
                            raise ValueError(f"Invalid points: {points}")
                    event_json["results"][name] = current_result_json

            elif re.match(
                r"^#[0-9]+ 4x25 m freestyle relay Year ([7-9]|10) (fe)?male$",
                event_name,
            ):
                event_name_split = event_name.split(" ")
                event_number = event_name_split[0][1:]
                event_year = event_name_split[6]
                event_gender = event_name_split[7]

                date_start = datetime.datetime(2023, 9, 2, 9, 0, 0)
                date_start += datetime.timedelta(minutes=(int(event_number) - 1) * 10)
                event_json = {
                    "type": "race",
                    "scoring_type": "relay",
                    "competitor_type": "team",
                    "name": f"4x25m Freestyle Relay Year {event_year} {event_gender}",
                    "distance": event_distance + "m",
                    "gender": event_gender,
                    "ystart": year - int(event_year),
                    "date": date_start,
                    "results": {},
                }

                # iterate through rows B7:F(INFINITY)
                for row in range(5, sheet.shape[0]):
                    # C: Name, F: Points
                    # Crayfish, 40

                    name = sheet.iloc[row, 2]
                    points = sheet.iloc[row, 5]

                    try:
                        points = int(points)
                    except ValueError:
                        points = 0

                    current_result_json = {
                        "points": points,
                        "_debug_points": points,
                    }
                    try:
                        int(points)
                    except ValueError:
                        if points in ["DQ", "DNF"]:
                            current_result_json[points] = True
                        else:
                            raise ValueError(f"Invalid points: {points}")
                    event_json["results"][name] = current_result_json

            if event_json:
                # write file to output directory
                event_file = (
                    output / f"{event_json['name'].lower().replace(' ', '-')}.yaml"
                )

                while True:
                    if event_file.exists():
                        # check if identical
                        with open(event_file, encoding="utf-8") as f:
                            existing_event = yaml.safe_load(f)
                            if existing_event == event_json:
                                break
                            if event_json.get("type") == "high_jump":
                                print(
                                    f"Event {event_json['name']} already exists but is different, not duplicating because high jump is not supported"
                                )
                                break
                            print(
                                f"Event {event_json['name']} already exists but is different"
                            )
                            # add a number to the end of the filename
                            stem = event_file.stem
                            # if the filename already has a number, increment it
                            if re.match(r".*-([0-9]+)$", stem):
                                stem = re.sub(
                                    r"([0-9]+)$",
                                    lambda x: str(int(x.group(1)) + 1),
                                    stem,
                                )
                            else:
                                stem += "-1"
                            event_file = event_file.with_stem(stem)
                    else:
                        with open(event_file, "w", encoding="utf-8") as f:
                            yaml.dump(event_json, f, sort_keys=False)
                        if event_json.get("type") == "high_jump":
                            print(
                                f"Event {event_json['name']} was created but does not have any results, because high jump is not supported"
                            )
                        break
            else:
                print(
                    f"Unknown event type with {sheet.shape[0]-5} results: {event_name}"
                )


if __name__ == "__main__":
    STUDENTS_CSV = pathlib.Path(sys.argv[1])
    RESULTS_XLSX = pathlib.Path(sys.argv[2])
    DATABASE_FOLDER = pathlib.Path(sys.argv[3])

    database_lock = raceml.DatabaseLock(DATABASE_FOLDER)
    database_lock.acquire()

    try:
        import_students(
            STUDENTS_CSV,
            DATABASE_FOLDER / "athletes/",
            2023,
            database_lock,
        )

        import_results(
            RESULTS_XLSX,
            DATABASE_FOLDER / "athletes/",
            DATABASE_FOLDER / "results/",
            2023,
            database_lock,
        )
    finally:
        database_lock.release()
