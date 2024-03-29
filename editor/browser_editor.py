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
    filepath = app.config["RACEML_DATABASE"] / "competitions"
    return flask.render_template(
        "index.html.j2",
        files=sorted(
            [
                {
                    "name": str(path.relative_to(filepath)),
                    "link": flask.url_for(
                        "competition", filepath=str(path.relative_to(filepath))
                    ),
                }
                for path in filepath.glob("**/*.yaml")
            ],
            key=lambda x: x["name"],
        ),
    )


@app.route("/new_competition", methods=["POST"])
def new_competition():
    filename = flask.request.form.get("filename", None)
    if filename is None:
        return "No filename specified", 400
    competition_type = flask.request.form.get("competition_type", None)
    if competition_type is None:
        return "No competition type specified", 400
    competitor_type = flask.request.form.get("competitor_type", None)
    if competitor_type is None:
        return "No competitor type specified", 400
    filepath = app.config["RACEML_DATABASE"] / "competitions" / (filename + ".yaml")
    if filepath.exists():
        return "File already exists", 400

    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(
            yaml.dump(
                {
                    "type": competition_type,
                    "competitor_type": competitor_type,
                    "results": {},
                },
            )
        )

    return flask.redirect(flask.url_for("competition", filename=filename + ".yaml"))


@app.route("/competition/<path:filepath>")
def competition(filepath):
    filepath = app.config["RACEML_DATABASE"] / "competitions" / filepath
    data = yaml.safe_load(filepath.read_text(encoding="utf-8"))
    if data["type"] in ["race", "bonus_points", "high_jump"]:
        if "date" in data and data["date"] is not None:
            data["date"] = data["date"].isoformat()
        return flask.render_template(
            "competition_editor.html.j2",
            data=data,
            config=get_config(),
        )
    else:
        return "Competition type not supported", 501


@app.route("/competition/<path:filepath>", methods=["PUT"])
def PUT_competition(filepath):
    # get JSON data from request
    data = flask.request.json

    # open the existing file
    reader = ruamel.yaml.YAML()
    with open(
        app.config["RACEML_DATABASE"] / "competitions" / filepath,
        "r",
        encoding="utf-8",
    ) as file:
        doc = reader.load(file)

    if data.get("date") is not None:
        data["date"] = datetime.datetime.fromisoformat(data["date"])

    # update the doc to be identical to data
    update_dictionary(doc, data)

    # write the file
    with open(
        app.config["RACEML_DATABASE"] / "competitions" / filepath,
        "w",
        encoding="utf-8",
    ) as file:
        reader.dump(doc, file)

    return "OK"


@app.route("/selection_preview")
def selection_preview():
    return flask.render_template(
        "selection_preview.html.j2",
        config=get_config(),
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
