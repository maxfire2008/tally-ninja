import flask
import sys
import pathlib

import requests

import raceml

app = flask.Flask(__name__)
app.jinja_env.autoescape = True


def get_athlete_list():
    for athlete in app.config["RACEML_DATABASE"].glob("athletes/**/*.yaml"):
        yield raceml.load(athlete)


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
        return flask.render_template(
            "result_editor.html.j2",
            data=data,
            athlete_list=sorted(
                get_athlete_list(), key=lambda x: x.get("name", repr(x))
            ),
        )
    else:
        return "Result type not supported", 501


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
