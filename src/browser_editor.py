import flask
import sys
import pathlib

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


@app.route("/result/<path:filename>")
def result(filename):
    filepath = app.config["RACEML_DATABASE"] / "results" / filename
    data = raceml.load(filepath)
    if data["type"] == "race":
        data["date"] = data["date"].isoformat()
        print(dict(sorted(get_athlete_list(), key=lambda x: x[1].get("name", repr(x)))))
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


@app.route("/save_result", methods=["POST"])
def save_result():
    # get JSON data from request
    data = flask.request.json

    # open the existing file
    reader = ruamel.yaml.YAML()
    with open(
        app.config["RACEML_DATABASE"] / "results" / data["filename"],
        "r",
        encoding="utf-8",
    ) as file:
        doc = reader.load(file)

    # update the file
    doc = raceml.deep_merge(doc, data["data"])

    # write the file
    with open(
        app.config["RACEML_DATABASE"] / "results" / data["filename"],
        "w",
        encoding="utf-8",
    ) as file:
        reader.dump(doc, file)


@app.route("/athlete_photo/<string:athlete_id>")
def athlete_photo(athlete_id):
    try:
        response = flask.make_response(
            raceml.lookup_athlete_photo(athlete_id, app.config["RACEML_DATABASE"])
        )
    except FileNotFoundError:
        return "404 Not Found", 404
    response.headers["Content-Type"] = "image/jpeg"
    # set a cache timeout of 1 day
    response.headers["Cache-Control"] = "max-age=86400"
    return response


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app.config["RACEML_DATABASE"] = pathlib.Path(sys.argv[1])
    else:
        quit("Usage: python3 browser_editor.py <path-to-raceml-database>")
    app.run(debug=True)
