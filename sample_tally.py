import sportsml
import pathlib
import safeeval
import datetime


class AttrDict:
    """Dictionary with attribute access to keys."""

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)

    def __getattr__(self, key):
        try:
            return self._d[key]
        except KeyError:
            raise AttributeError(key)


def calculate_age(born: datetime.date | str, today: datetime.date | str) -> int:
    """
    Calculate age in years.

    Args:
        born (datetime.date | str): Date of birth.
        today (datetime.date | str): Date to calculate age from.

    Returns:
        int: Age in years.
    """
    if isinstance(born, str):
        born = datetime.date.fromisoformat(born).date()
    if isinstance(today, str):
        today = datetime.date.fromisoformat(today).date()
    delta = today - born
    return delta.days // 365


def lookup_athlete(athlete_id, data_folder):
    athlete_filenames = list(data_folder.glob("athletes/**/" + athlete_id + ".yaml"))
    if len(athlete_filenames) < 1:
        raise ValueError("Athlete not found: " + athlete_id)
    if len(athlete_filenames) > 1:
        raise ValueError("Multiple athletes found: " + athlete_id)
    athlete_filename = athlete_filenames[0]
    return sportsml.load(athlete_filename)


def main():
    tally_board = {}

    data_folder = pathlib.Path("sample_data")

    for results_filename in data_folder.glob("results/**/*.yaml"):
        results = sportsml.load(results_filename)

        for athlete_id in [r["id"] for r in results["results"]]:
            athlete = lookup_athlete(athlete_id, data_folder)
            eligible_leagues = []

            for league_filename in data_folder.glob("leagues/**/*.yaml"):
                league = sportsml.load(league_filename)

                ATHLETE_ELIGIBLE = True

                env = {
                    "event_distance": results["distance"],
                    "athlete_age": athlete["dob"] - results["date"],
                    "athlete_gender": athlete["gender"],
                }
                interpreter = safeeval.SafeEval()

                for criterion in league["eligibility"]:
                    ast = interpreter.compile(criterion)
                    result = interpreter.execute(ast, env)
                    if not result:
                        ATHLETE_ELIGIBLE = False
                        break

                if ATHLETE_ELIGIBLE:
                    eligible_leagues.append(league)

            if len(eligible_leagues) > 1:
                raise ValueError(
                    "Athlete eligible for multiple leagues: "
                    + athlete_id
                    + " "
                    + str([l["_filename"] for l in eligible_leagues])
                )

            if len(eligible_leagues) == 1:
                chosen_league = eligible_leagues[0]
                if chosen_league not in tally_board:
                    tally_board[chosen_league] = {}
                if athlete not in tally_board[chosen_league]:
                    tally_board[chosen_league][athlete] = 0

                tally_board[chosen_league][athlete]


if __name__ == "__main__":
    main()
