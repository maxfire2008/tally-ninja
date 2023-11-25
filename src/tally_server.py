import sys
import pathlib
import flask
import waitress

import raceml
import simple_tally

app = flask.Flask(__name__)


@app.route("/results")
def html_results():
    database_lock = raceml.DatabaseLock(app.config["DATABASE_FOLDER"])
    database_lock.acquire()
    try:
        return simple_tally.results_to_html(
            simple_tally.tally_data(app.config["DATABASE_FOLDER"], database_lock),
            open_database=True,
            data_folder=app.config["DATABASE_FOLDER"],
            database_lock=database_lock,
        )
    finally:
        database_lock.release()


if __name__ == "__main__":
    app.config["DATABASE_FOLDER"] = pathlib.Path(sys.argv[1])

    waitress.serve(app, listen=sys.argv[2])
