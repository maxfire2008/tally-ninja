import flask
import sys
import pathlib
import datetime
import pytz

import os
import waitress
import requests
import yaml
import ruamel.yaml
import ruamel.yaml.error

app = flask.Flask(__name__)
app.jinja_env.autoescape = True


def get_config():
    with open(
        app.config["RACEML_DATABASE"] / "config.yaml", "r", encoding="utf-8"
    ) as file:
        return yaml.safe_load(file.read())


@app.route("/")
def index():
    # list files in app.config["RACEML_DATABASE"]/events
    events = list((app.config["RACEML_DATABASE"] / "events").iterdir())
    print(events)

    return "hello"


def update_dictionary(dictionary, new_data):
    for key, value in new_data.items():
        if isinstance(value, dict):
            if key not in dictionary:
                dictionary[key] = {}
            update_dictionary(dictionary[key], new_data[key])
        else:
            dictionary[key] = new_data[key]
    for key, value in list(dictionary.items()):
        if key not in new_data:
            del dictionary[key]


@app.route("/athlete_photo/<string:athlete_id>")
def athlete_photo(athlete_id):
    try:
        response = flask.make_response(
            (
                app.config["RACEML_DATABASE"] / "athlete_photos" / (athlete_id + ".jpg")
            ).read_bytes()
        )
    except FileNotFoundError:
        response = flask.make_response(
            "Not Found", 200
        )  # 200 OK is a bit of a lie, but it allows the browser to cache the response
    response.headers["Content-Type"] = "image/jpeg"
    # set a cache timeout of 1 day
    response.headers["Cache-Control"] = "max-age=86400"
    return response


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app.config["RACEML_DATABASE"] = pathlib.Path(sys.argv[1])
    else:
        quit("Usage: python3 browser_editor.py <path-to-raceml-database>")

    if sys.argv[-1] == "dev":
        app.run(debug=True, port=5000, threaded=True)
    else:
        # serve with waitress with as many threads as there are CPUs, logs of level INFO
        waitress.serve(app, port=5000, threads=os.cpu_count())
