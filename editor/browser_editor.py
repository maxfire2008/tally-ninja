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
    event_info = [
        f.stem for f in (app.config["RACEML_DATABASE"] / "event_info").glob("*.yaml")
    ]

    results = [
        f.stem for f in (app.config["RACEML_DATABASE"] / "results").glob("*.yaml")
    ]

    times = [f.stem for f in (app.config["RACEML_DATABASE"] / "times").glob("*.yaml")]

    all_names = set(event_info + results + times)

    events = []

    for name in all_names:
        # open the event_info file
        with open(
            app.config["RACEML_DATABASE"] / "event_info" / (name + ".yaml"),
            "r",
            encoding="utf-8",
        ) as file:
            event = yaml.safe_load(file.read())
            print(event)
            events.append(
                {
                    "id": name,
                    "name": event["name"],
                    "event_type": event["event_type"],
                    "results": (name if name in results else None),
                    "times": (name if name in times else None),
                }
            )

    events.sort(key=lambda x: str(x))

    return flask.render_template("index.html.j2", events=events)


@app.route("/editor/<string:doc_type>/<string:id>")
def editor(doc_type, id):
    if doc_type not in ["results", "times"]:
        return "Invalid doc_type", 400

    with open(
        app.config["RACEML_DATABASE"] / "event_info" / (id + ".yaml"),
        "r",
        encoding="utf-8",
    ) as file:
        event_info = yaml.safe_load(file.read())

    with open(
        app.config["RACEML_DATABASE"] / doc_type / (id + ".yaml"), "r", encoding="utf-8"
    ) as file:
        data = yaml.safe_load(file.read())

    return flask.render_template(
        "editor.html.j2",
        doc_type=doc_type,
        id=id,
        data=data,
        event_info=event_info,
        config=get_config(),
    )


@app.route("/api/save/editor/<string:doc_type>/<string:id>", methods=["POST"])
def save_editor(doc_type, id):
    request_body = flask.request.json
    # load the existing data
    with open(
        app.config["RACEML_DATABASE"] / doc_type / (id + ".yaml"), "r", encoding="utf-8"
    ) as file:
        original_data = yaml.safe_load(file.read())

    # check the data hasn't been modified since the editor was opened
    print(request_body["original"])
    print(original_data)
    if request_body["original"] != original_data:
        return "Conflict", 409

    # update the data
    with open(
        app.config["RACEML_DATABASE"] / doc_type / (id + ".yaml"), "w", encoding="utf-8"
    ) as file:
        yaml.dump(request_body["updated"], file, default_flow_style=False)

    return "OK", 200


@app.route("/create_document/<string:doc_type>/<string:id>", methods=["POST"])
def create_document(doc_type, id):
    if doc_type not in ["results", "times"]:
        return "Invalid doc_type", 400

    with open(
        app.config["RACEML_DATABASE"] / doc_type / (id + ".yaml"), "w", encoding="utf-8"
    ) as file:
        yaml.dump({doc_type: []}, file, default_flow_style=False)

    return flask.redirect(flask.url_for("editor", doc_type=doc_type, id=id))


@app.route("/api/athlete/<string:student_id>")
def api_athlete(student_id):
    try:
        with open(
            app.config["RACEML_DATABASE"] / "athletes" / (student_id + ".yaml"),
            "r",
            encoding="utf-8",
        ) as file:
            athlete = yaml.safe_load(file.read())

        return flask.jsonify(athlete)
    except FileNotFoundError:
        return "Not Found", 404


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
