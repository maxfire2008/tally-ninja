import raceml
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


def lookup_athlete(athlete_id, athletes_folder: pathlib.Path):
    athlete_filenames = list(athletes_folder.glob("**/" + athlete_id + ".yaml"))
    if len(athlete_filenames) < 1:
        raise ValueError("Athlete not found: " + athlete_id)
    if len(athlete_filenames) > 1:
        raise ValueError("Multiple athletes found: " + athlete_id)
    athlete_filename = athlete_filenames[0]
    return raceml.load(athlete_filename)


def get_eligible_leagues(athlete, results, leagues_folder: pathlib.Path):
    eligible_leagues = []

    for league_filename in leagues_folder.glob("**/*.yaml"):
        try:
            league = raceml.load(league_filename)
        except raceml.TemplateFileError:
            continue

        ATHLETE_ELIGIBLE = True

        env = {
            "event_distance": results["distance"],
            "athlete_age": calculate_age(athlete["dob"], results["date"]),
            "athlete_gender": athlete["gender"],
        }
        interpreter = safeeval.SafeEval()

        for criterion in league.get("eligibility", []):
            ast = interpreter.compile(criterion)
            result = interpreter.execute(ast, env)
            # print(">>", athlete, criterion, result)
            if not result:
                ATHLETE_ELIGIBLE = False
                break

        if ATHLETE_ELIGIBLE:
            eligible_leagues.append(league)

    league_types = set([l["league_type"] for l in eligible_leagues])
    for league_type in league_types:
        leagues_of_type = [
            l for l in eligible_leagues if l.get("league_type", None) == league_type
        ]
        if len(leagues_of_type) > 1:
            raise ValueError(
                "Athlete eligible for multiple leagues of type "
                + league_type
                + ": "
                + athlete["_filename"]
                + " "
                + str([l["_filepath"] for l in leagues_of_type])
            )

    return eligible_leagues


def main():
    tally_board = {}

    data_folder = pathlib.Path("sample_data")
    results_folder = data_folder / "results"

    for results_filename in results_folder.glob("**/*.yaml"):
        results = raceml.load(results_filename)

        for athlete_id in [r["id"] for r in results["results"]]:
            try:
                athlete = lookup_athlete(athlete_id, data_folder / "athletes")
            except raceml.TemplateFileError:
                continue

            eligible_leagues = get_eligible_leagues(
                athlete, results, data_folder / "leagues"
            )

            for chosen_league in eligible_leagues:
                chosen_league_id = chosen_league["_filename"]

                if chosen_league["scoring"]["contributes_to"] == "individual":
                    contributes_to = athlete_id
                elif chosen_league["scoring"]["contributes_to"] == "team":
                    contributes_to = athlete["team"]
                else:
                    raise ValueError(
                        "No contributes_to method found for league: " + chosen_league_id
                    )

                if chosen_league_id not in tally_board:
                    tally_board[chosen_league_id] = {}
                if contributes_to not in tally_board[chosen_league_id]:
                    tally_board[chosen_league_id][contributes_to] = None

                competitors = []

                for potential_competitor_result in results["results"]:
                    potential_competitor_id = potential_competitor_result["id"]
                    try:
                        potential_competitor = lookup_athlete(
                            potential_competitor_id, data_folder / "athletes"
                        )
                    except raceml.TemplateFileError:
                        continue
                    if chosen_league in get_eligible_leagues(
                        potential_competitor, results, data_folder / "leagues"
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
                        if not tally_board[chosen_league_id][contributes_to]:
                            tally_board[chosen_league_id][contributes_to] = 0
                        tally_board[chosen_league_id][contributes_to] += max(
                            scoring_settings["method_value"] - place, 0
                        )

                if not tally_board[chosen_league_id][contributes_to]:
                    raise ValueError("No method found for league: " + chosen_league_id)
    pprint(tally_board)


if __name__ == "__main__":
    main()
