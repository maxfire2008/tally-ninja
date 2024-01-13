import flask
import sys
import pathlib
import datetime
import pytz

import os
import waitress
import requests
import ruamel.yaml
import ruamel.yaml.error

import raceml

app = flask.Flask(__name__)
app.jinja_env.autoescape = True


def get_athlete_list():
    for athlete in app.config["RACEML_DATABASE"].glob("athletes/**/*.yaml"):
        yield athlete.stem, raceml.load(athlete)


@app.route("/")
def index():
    filepath = app.config["RACEML_DATABASE"] / "results"
    return flask.render_template(
        "index.html.j2",
        files=[
            {
                "name": str(path.relative_to(filepath)),
                "link": flask.url_for(
                    "result", filename=str(path.relative_to(filepath))
                ),
            }
            for path in filepath.glob("**/*.yaml")
        ],
    )


@app.route("/new_result", methods=["POST"])
def new_result():
    filename = flask.request.form.get("filename", None)
    if filename is None:
        return "No filename specified", 400
    result_type = flask.request.form.get("result_type", None)
    if result_type is None:
        return "No result result type specified", 400
    competitor_type = flask.request.form.get("competitor_type", None)
    if competitor_type is None:
        return "No competitor type specified", 400
    filepath = app.config["RACEML_DATABASE"] / "results" / (filename + ".yaml")
    if filepath.exists():
        return "File already exists", 400

    filepath.parent.mkdir(parents=True, exist_ok=True)

    raceml.dump(
        filepath,
        {
            "type": result_type,
            "competitor_type": competitor_type,
            "results": {},
        },
    )

    return flask.redirect(flask.url_for("result", filename=filename + ".yaml"))


@app.route("/result/<path:filename>")
def result(filename):
    filepath = app.config["RACEML_DATABASE"] / "results" / filename
    data = raceml.load(filepath)
    if data["type"] in ["race", "bonus_points", "high_jump"]:
        if "date" in data and data["date"] is not None:
            data["date"] = data["date"].isoformat()
        else:
            data["date"] = None
        return flask.render_template(
            "result_editor.html.j2",
            data=data,
            config=raceml.load(app.config["RACEML_DATABASE"] / "config.yaml"),
            athlete_list=dict(
                sorted(get_athlete_list(), key=lambda x: x[1].get("name", repr(x)))
            ),
        )
    else:
        return "Result type not supported", 501


@app.route("/selection_preview")
def selection_preview():
    return flask.render_template(
        "selection_preview.html.j2",
        config=raceml.load(app.config["RACEML_DATABASE"] / "config.yaml"),
        athlete_list=dict(
            sorted(get_athlete_list(), key=lambda x: x[1].get("name", repr(x)))
        ),
    )


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


@app.route("/save_result", methods=["POST"])
def save_result():
    # get JSON data from request
    data = flask.request.json
    filepath = data["_filepath"]

    # open the existing file
    reader = ruamel.yaml.YAML()
    with open(
        filepath,
        "r",
        encoding="utf-8",
    ) as file:
        doc = reader.load(file)
    if data.get("date") is not None:
        data["date"] = datetime.datetime.fromisoformat(data["date"])

    if "data" in data and data["data"] is None:
        del data["data"]

    for key, value in data["results"].items():
        if "finish_time" in value and value["finish_time"] is None:
            del data["results"][key]["finish_time"]

    for hidden_key in ["_filepath", "_filename"]:
        if hidden_key in data:
            del data[hidden_key]

    # update the doc to be identical to data
    update_dictionary(doc, data)

    # write the file
    with open(
        filepath,
        "w",
        encoding="utf-8",
    ) as file:
        reader.dump(doc, file)

    return "OK"


@app.route("/athlete_photo/<string:athlete_id>")
def athlete_photo(athlete_id):
    try:
        response = flask.make_response(
            raceml.lookup_athlete_photo(athlete_id, app.config["RACEML_DATABASE"])
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
        app.run(debug=True, port=5000)
    else:
        # serve with waitress with as many threads as there are CPUs, logs of level INFO
        waitress.serve(app, port=5000, threads=os.cpu_count())
