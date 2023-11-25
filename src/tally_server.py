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
    if len(sys.argv) < 3:
        print("Usage: py tally_server.py <database_folder> <listen_address>")
        sys.exit(1)

    database_folder = pathlib.Path(sys.argv[1]).absolute()
    if not database_folder.exists():
        print(f"Database folder {database_folder} does not exist")
        sys.exit(1)

    listen_address = sys.argv[2]

    print(f"Starting tally server on {listen_address} with database {database_folder}")

    app.config["DATABASE_FOLDER"] = database_folder
    waitress.serve(app, listen=listen_address)
