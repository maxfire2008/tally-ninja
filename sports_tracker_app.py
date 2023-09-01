"""Imports data from Sports Tracker.
"""
import csv
import datetime
import pathlib
import re
import yaml
import pandas


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
                / f"{student['firstname']}-{student['lastname']}-{student_raceml['ystart']}.yaml"
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
                            student_file = (
                                output
                                / f"{student['firstname']}-{student['lastname']}-{student_raceml['ystart']}-1.yaml"
                            )
                else:
                    with open(student_file, "w") as f:
                        yaml.dump(student_raceml, f)
                    print(
                        f"Student {student['firstname']} {student['lastname']} imported"
                    )
                    break


def import_results(file, output):
    with open(file) as spreadsheet:
        results = pandas.read_excel(spreadsheet, sheet_name=None)

        # iterate through each sheet
        for sheet_name, sheet in results.items():
            pass


if __name__ == "__main__":
    import_students(
        "../sport-scorer-sample-data/students.csv",
        "../sport-scorer-sample-data/***REMOVED***/athletes/sta/",
        2023,
    )

    import_results(
        "../sport-scorer-sample-data/***REMOVED*** Athletics Carnival 2023-results.xlsx",
        "../sport-scorer-sample-data/***REMOVED***/results/",
    )
