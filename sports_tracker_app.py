"""Imports data from Sports Tracker.
"""
import csv
import datetime
import pathlib
import re
import yaml
import pandas
import simple_tally


def import_students(file, output, year):
    if not isinstance(file, pathlib.Path):
        file = pathlib.Path(file).resolve()
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file}")
    if not isinstance(output, pathlib.Path):
        output = pathlib.Path(output).resolve()
        output.mkdir(parents=True, exist_ok=True)
    with open(file) as f:
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
            student_raceml["dob"] = (
                datetime.datetime.strptime(student["dob"], "%d-%m-%Y")
                .date()
                .isoformat()
            )

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
                    with open(student_file) as f:
                        existing_student = yaml.safe_load(f)
                        if existing_student == student_raceml:
                            break
                        else:
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
                    with open(student_file, "w") as f:
                        yaml.dump(student_raceml, f)
                    break


def import_results(file, athletes_directory, output, year):
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
        for sheet_name, sheet in results.items():
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
                    "date": date_start.isoformat(),
                    "results": [],
                }

                # iterate through rows B7:F(INFINITY)
                for row in range(6, sheet.shape[0]):
                    # C: Name, E: Result
                    # ***REMOVED***, 14s 600ms
                    name = sheet.iloc[row, 2]
                    name_split = name.split(" ")
                    result = sheet.iloc[row, 4]
                    filename = (
                        "-".join(name_split[0:2]).lower()
                        + "-"
                        + str(event_json["ystart"])
                        # + "*"
                    )

                    # ensure that the athlete exists
                    simple_tally.lookup_athlete(filename, athletes_directory)

                    result_in_seconds = None
                    if re.match(r"^[0-9]+m [0-9]+s [0-9]+ms$", result):
                        result_split = result.split(" ")
                        result_in_seconds = (
                            int(result_split[0][:-1]) * 60
                            + int(result_split[1][:-1])
                            + int(result_split[2][:-2]) / 1000
                        )
                    elif re.match(r"^[0-9]+s [0-9]+ms$", result):
                        result_split = result.split(" ")
                        result_in_seconds = (
                            int(result_split[0][:-1]) + int(result_split[1][:-2]) / 1000
                        )
                    else:
                        print(f"Invalid result: {result}")

                    event_json["results"].append(
                        {
                            "id": filename,
                            "finish_time": result_in_seconds,
                        }
                    )
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
                    continue
                date_start = datetime.datetime(2023, 9, 2, 9, 0, 0)
                date_start += datetime.timedelta(minutes=(int(event_number) - 1) * 10)
                event_json = {
                    "type": "_".join(event_type).lower(),
                    "name": " ".join(event_type).title()
                    + f" Year {event_year} {event_gender}",
                    "gender": event_gender,
                    "ystart": year - int(event_year),
                    "date": date_start.isoformat(),
                    "results": [],
                }

                # iterate through rows B7:F(INFINITY)
                for row in range(6, sheet.shape[0]):
                    name = sheet.iloc[row, 2]
                    name_split = name.split(" ")
                    result = sheet.iloc[row, 4]
                    filename = (
                        "-".join(name_split[0:2]).lower()
                        + "-"
                        + str(event_json["ystart"])
                        # + "*"
                    )
                    athlete = simple_tally.lookup_athlete(filename, athletes_directory)

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
                                current_result.append(
                                    [
                                        int(result_split_split[1][:-1]) * 1000
                                        + int(result_split_split[2]) * 10
                                    ]
                                )
                            except ValueError:
                                pass
                    else:
                        print(f"Invalid result: {result}")

                    event_json["results"].append(
                        {
                            "id": filename,
                            "results": current_result,
                        }
                    )
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
                    "date": date_start.isoformat(),
                    "results": [],
                }

                # iterate through rows B7:F(INFINITY)
                for row in range(6, sheet.shape[0]):
                    name = sheet.iloc[row, 2]
                    name_split = name.split(" ")
                    result = sheet.iloc[row, 4]
                    filename = (
                        "-".join(name_split[0:2]).lower()
                        + "-"
                        + str(event_json["ystart"])
                        # + "*"
                    )
                    athlete = simple_tally.lookup_athlete(filename, athletes_directory)

                    if not results_split:
                        continue

                    current_result = []

                    # 1m 20cm1m 25cm1m 35cm1m 40cm1m 45cm1m 50cm1m 55cm1m 60cm
                    results_split = result.split("cm")
                    # ['1m 20', '1m 25', '1m 35', '1m 40', '1m 45', '1m 50', '1m 55', '1m 60', '']

                    for result_split in results_split:
                        if not result_split:
                            continue
                        result_split_split = result_split.split(" ")
                        # ['1m', '20']
                        try:
                            current_result.append(
                                [
                                    int(result_split_split[0][:-1]) * 1000
                                    + int(result_split_split[1]) * 10
                                ]
                            )
                        except ValueError:
                            pass

                    event_json["results"].append(
                        {
                            "id": filename,
                            "results": current_result,
                        }
                    )
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
                            else:
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
                        break
            else:
                print(
                    f"Unknown event type with {sheet.shape[0]-5} results: {event_name}"
                )


if __name__ == "__main__":
    import_students(
        "../sport-scorer-sample-data/students.csv",
        "../sport-scorer-sample-data/***REMOVED***/athletes/sta/",
        2023,
    )

    import_results(
        "../sport-scorer-sample-data/***REMOVED*** Athletics Carnival 2023-results.xlsx",
        "../sport-scorer-sample-data/***REMOVED***/athletes/",
        "../sport-scorer-sample-data/***REMOVED***/results/",
        2023,
    )
