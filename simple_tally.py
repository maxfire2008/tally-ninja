import sportsml
import pathlib
import safeeval
import datetime
from pprint import pprint


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


def get_eligible_leagues(athlete, results, data_folder: pathlib.Path):
    eligible_leagues = []

    for league_filename in data_folder.glob("leagues/**/*.yaml"):
        try:
            league = sportsml.load(league_filename)
        except sportsml.TemplateFileError:
            continue

        ATHLETE_ELIGIBLE = True

        env = {
            "event_distance": results["distance"],
            "athlete_age": calculate_age(athlete["dob"], results["date"]),
            "athlete_gender": athlete["gender"],
        }
        interpreter = safeeval.SafeEval()

        for criterion in league["eligibility"]:
            ast = interpreter.compile(criterion)
            result = interpreter.execute(ast, env)
            # print(">>", athlete, criterion, result)
            if not result:
                ATHLETE_ELIGIBLE = False
                break

        if ATHLETE_ELIGIBLE:
            eligible_leagues.append(league)

    if len(eligible_leagues) > 1:
        raise ValueError(
            "Athlete eligible for multiple leagues: "
            + athlete["_filename"]
            + " "
            + str([l["_filepath"] for l in eligible_leagues])
        )

    return eligible_leagues


def main():
    tally_board = {}

    data_folder = pathlib.Path("sample_data")

    for results_filename in data_folder.glob("results/**/*.yaml"):
        results = sportsml.load(results_filename)

        for athlete_id in [r["id"] for r in results["results"]]:
            try:
                athlete = lookup_athlete(athlete_id, data_folder)
            except sportsml.TemplateFileError:
                continue

            eligible_leagues = get_eligible_leagues(athlete, results, data_folder)

            if len(eligible_leagues) == 1:
                chosen_league = eligible_leagues[0]
                chosen_league_id = chosen_league["_filename"]
                if chosen_league_id not in tally_board:
                    tally_board[chosen_league_id] = {}
                if athlete_id not in tally_board[chosen_league_id]:
                    tally_board[chosen_league_id][athlete_id] = None

                competitors = []

                for potential_competitor_result in results["results"]:
                    potential_competitor_id = potential_competitor_result["id"]
                    try:
                        potential_competitor = lookup_athlete(
                            potential_competitor_id, data_folder
                        )
                    except sportsml.TemplateFileError:
                        continue
                    if chosen_league in get_eligible_leagues(
                        potential_competitor, results, data_folder
                    ):
                        competitors.append(potential_competitor_result)

                # get finish time
                for result in results["results"]:
                    if result["id"] == athlete_id:
                        athlete_result = result
                        break

                scoring_settings = chosen_league["scoring"]
                sort_by = scoring_settings["sort_by"]

                if scoring_settings["method"] in ["minus_place"]:
                    # get place among competitors
                    place = 1
                    for competitor in competitors:
                        if competitor[sort_by] < athlete_result[sort_by]:
                            place += 1

                    if scoring_settings["method"] == "minus_place":
                        tally_board[chosen_league_id][athlete_id] = abs(
                            scoring_settings["method_value"] - place
                        )

                if not tally_board[chosen_league_id][athlete_id]:
                    raise ValueError("No method found for league: " + chosen_league_id)
    pprint(tally_board)


if __name__ == "__main__":
    main()
