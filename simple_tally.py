"""
This module provides functions to tally data for sports events.
It includes functions to calculate age, lookup athlete data,
get eligible leagues for an athlete, and cache results.

Classes:
    AttrDict: A dictionary with attribute access to keys.

Functions:
    calculate_age: Calculate age in years.
    lookup_athlete: Lookup athlete data by ID.
    get_eligible_leagues: Get eligible leagues for an athlete.
    tally_data: Tally data for sports events.

"""
import hashlib
import json
import sys
import pathlib
from pprint import pprint
import datetime
import safeeval
import raceml


class AttrDict:
    """Dictionary with attribute access to keys."""

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)

    def __getattr__(self, key):
        try:
            return self._d[key]
        except KeyError as error:
            raise AttributeError(key) from error


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
        born = datetime.datetime.fromisoformat(born)
    if isinstance(today, str):
        today = datetime.datetime.fromisoformat(today)
    delta = today - born
    return delta.days // 365


def number(x) -> int | float:
    """Returns an int or a float of x, if not a number raises ValueError.

    Keyword arguments:
    x -- the value to convert to a number
    Returns: int or float
    """

    if isinstance(x, float):
        if x.is_integer():
            return int(x)
        else:
            return x
    elif isinstance(x, int):
        return x
    else:
        try:
            return int(x)
        except ValueError:
            return float(x)


_athlete_cache = {}


def lookup_athlete(athlete_id, athletes_folder: pathlib.Path):
    """
    Looks up an athlete's data by their ID.

    Args:
        athlete_id (str): The ID of the athlete to look up.
        athletes_folder (pathlib.Path): The folder containing the YAML files for all athletes.

    Returns:
        dict: A dictionary containing the athlete's data.

    Raises:
        ValueError: If the athlete is not found or multiple athletes are found with the same ID.
    """
    if (athletes_folder, athlete_id) in _athlete_cache:
        return _athlete_cache[(athletes_folder, athlete_id)]
    athlete_filenames = list(athletes_folder.glob("**/" + athlete_id + ".yaml"))
    if len(athlete_filenames) < 1:
        raise ValueError("Athlete not found: " + athlete_id)
    if len(athlete_filenames) > 1:
        raise ValueError("Multiple athletes found: " + athlete_id)
    athlete_filename = athlete_filenames[0]
    athlete_data = raceml.load(athlete_filename)
    _athlete_cache[(athletes_folder, athlete_id)] = athlete_data
    return athlete_data


_eligible_leagues_cache = {}


def get_eligible_leagues(
    athlete, results, leagues_folder: pathlib.Path, competitor_type: str = "individual"
):
    """
    Returns a list of leagues that an athlete is eligible for
    based on their results and the leagues' eligibility criteria.

    Args:
        athlete (dict): the athlete, including their date of birth and gender.
        results (dict): the race results.
        leagues_folder (pathlib.Path): the folder containing the leagues.

    Returns:
        A list of leagues' dictionaries.

    Raises:
        ValueError: If the athlete is eligible for multiple leagues of the same type.

    """
    arg_key = repr((athlete, results, leagues_folder))
    if arg_key in _eligible_leagues_cache:
        return _eligible_leagues_cache[arg_key]

    eligible_leagues = []

    for league_filename in leagues_folder.glob("**/*.yaml"):
        try:
            league = raceml.load(league_filename)
        except raceml.TemplateFileError:
            continue

        athlete_eligible = True

        if competitor_type == "individual":
            env = {
                "event_distance": results.get("distance", None),
                "athlete_age": calculate_age(athlete["dob"], results["date"]),
                "athlete_gender": athlete["gender"],
                "athlete_ystart": athlete.get("ystart"),
            }
            interpreter = safeeval.SafeEval()

            for criterion in league.get("eligibility", []):
                ast = interpreter.compile(criterion)
                result = interpreter.execute(ast, env)
                # print(">>", athlete, criterion, result)
                if not result:
                    athlete_eligible = False
                    break
        elif competitor_type == "team":
            if league.get("permit_teams", False):
                athlete_eligible = True

        if athlete_eligible:
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

    _eligible_leagues_cache[arg_key] = eligible_leagues
    return eligible_leagues


def calculate_points(
    athlete_result,
    competitors,
    scoring_settings,
    chosen_league_id="Unknown",
    results_type="Unknown",
    results_name="Unknown",
):
    contrib_amount = None

    if scoring_settings["method"] in ["minus_place"]:
        # example results
        # 1. 00:20:00
        # 1. 00:20:00
        # 2. 00:20:01
        # 3. 00:20:02
        # 4. 00:20:03
        # 4. 00:20:03
        # 5. 00:20:04
        # 6. 00:20:05

        if scoring_settings["sort_by"] in [
            "highest",
            "lowest",
        ]:
            # calculate place

            if scoring_settings.get("combine_method") == "max":
                unique_scores = set(
                    [
                        max(c[scoring_settings["sort_key"]])
                        if c[scoring_settings["sort_key"]]
                        and not (c.get("DNF", False) or c.get("DNS", False))
                        else (
                            float("inf")
                            if scoring_settings["sort_by"] == "lowest"
                            else float("-inf")
                        )
                        for c in competitors
                    ]
                )
                my_score = (
                    max(athlete_result[scoring_settings["sort_key"]])
                    if athlete_result[scoring_settings["sort_key"]]
                    and not (
                        athlete_result.get("DNF", False)
                        or athlete_result.get("DNS", False)
                    )
                    else (
                        float("inf")
                        if scoring_settings["sort_by"] == "lowest"
                        else float("-inf")
                    )
                )
            else:
                unique_scores = set(
                    [
                        c[scoring_settings["sort_key"]]
                        if not (c.get("DNF", False) or c.get("DNS", False))
                        else (
                            float("inf")
                            if scoring_settings["sort_by"] == "lowest"
                            else float("-inf")
                        )
                        for c in competitors
                    ]
                )
                my_score = (
                    athlete_result[scoring_settings["sort_key"]]
                    if not (
                        athlete_result.get("DNF", False)
                        or athlete_result.get("DNS", False)
                    )
                    else (
                        float("inf")
                        if scoring_settings["sort_by"] == "lowest"
                        else float("-inf")
                    )
                )
                for unique_score in unique_scores:
                    unique_score = number(unique_score)
                my_score = number(my_score)

            if scoring_settings["sort_by"] == "lowest":
                place = 0
                for score in unique_scores:
                    if score < my_score:
                        place += 1
            elif scoring_settings["sort_by"] == "highest":
                place = 0
                for score in unique_scores:
                    if score > my_score:
                        place += 1
            else:
                raise ValueError(
                    "No sort_by method found for league: "
                    + chosen_league_id
                    + " "
                    + results_type
                    + " "
                    + scoring_settings["sort_by"]
                )
        elif scoring_settings["sort_by"] == "high_jump":
            place = 0
            unique_scores = set(
                [
                    json.dumps(
                        v if not (v.get("DNF", False) or v.get("DNS", False)) else []
                    )
                    for v in competitors
                ]
            )
            my_score = athlete_result

            my_score_best = None
            for ht, at in my_score["heights"].items():
                if my_score_best is None or (
                    ht > my_score_best["height"] and True in at
                ):
                    my_score_best = {
                        "height": ht,
                        "attempts": at,
                    }

            for score in [json.loads(s) for s in unique_scores]:
                their_score_best = None
                for ht, at in score["heights"].items():
                    if their_score_best is None or (
                        ht > their_score_best["height"] and True in at
                    ):
                        their_score_best = {
                            "height": ht,
                            "attempts": at,
                        }

                if number(their_score_best["height"]) > number(my_score_best["height"]):
                    place += 1
                elif their_score_best["height"] == my_score_best["height"]:
                    if their_score_best["attempts"].count(False) < my_score_best[
                        "attempts"
                    ].count(False):
                        place += 1
                    elif their_score_best["attempts"].count(False) == my_score_best[
                        "attempts"
                    ].count(False):
                        if their_score_best == my_score_best:
                            # count back find last height
                            for ht, at in sorted(
                                athlete_result["heights"].keys(),
                                key=lambda x: x[0],
                                reverse=True,
                            ):
                                for their_ht, their_at in score["heights"].keys():
                                    if their_ht["height"] == ht["height"]:
                                        if their_at.count(False) == at.count(False):
                                            continue
                                        elif their_at.count(False) > at.count(False):
                                            place += 1
                                            break
                                        else:
                                            break
                        else:
                            raise ValueError(
                                "Tie in high jump (known bug): "
                                + str(their_score_best)
                                + " "
                                + str(my_score_best)
                            )
        else:
            raise ValueError(
                "No sort_by method found for league: "
                + chosen_league_id
                + " "
                + results_type
                + " "
                + scoring_settings["sort_by"]
            )

        if scoring_settings["method"] == "minus_place":
            contrib_amount = max(
                scoring_settings["method_value"]
                - (place * scoring_settings.get("method_decrement", 1)),
                0,
            )
    elif scoring_settings["method"] == "bonus_points":
        # results:
        #   - id: Red
        #     awards:
        #       - name: 'ST Import'
        #         points: 1044

        contrib_amount = sum([a["points"] for a in athlete_result["awards"]])

    if contrib_amount is None:
        raise ValueError("No method found for league: " + chosen_league_id)

    if athlete_result.get("DNF", False) or athlete_result.get("DQ", False):
        contrib_amount = 0

    return contrib_amount


def tally_data(data_folder):
    """
    Tally the results of a race.

    Args:
    - data_folder: A string representing the path to the folder containing the race data.

    Returns:
    - A dictionary representing the tally board of the race results.
    """
    if not isinstance(data_folder, pathlib.Path):
        data_folder = pathlib.Path(data_folder)

    tally_board = {}

    results_folder = data_folder / "results"

    athletes_folder = data_folder / "athletes"
    leagues_folder = data_folder / "leagues"
    cache_folder = data_folder / "cache"
    cache_folder.mkdir(exist_ok=True)

    code_folder = pathlib.Path(__file__).parent

    athletes_hash_items = []
    leagues_hash_items = []
    code_hash_items = []

    for item in athletes_folder.glob("**/*.yaml"):
        athletes_hash_items.append(item)
        with open(item, "rb") as file:
            athletes_hash_items.append(file.read())
    for item in leagues_folder.glob("**/*.yaml"):
        leagues_hash_items.append(item)
        with open(item, "rb") as file:
            leagues_hash_items.append(file.read())
    for item in code_folder.glob("*"):
        if not item.is_file():
            continue
        code_hash_items.append(item)
        with open(item, "rb") as file:
            code_hash_items.append(file.read())

    athletes_folder_hash = hashlib.sha256(
        repr(athletes_hash_items).encode()
    ).hexdigest()
    leagues_folder_hash = hashlib.sha256(repr(leagues_hash_items).encode()).hexdigest()
    code_folder_hash = hashlib.sha256(repr(code_hash_items).encode()).hexdigest()

    for results_filename in results_folder.glob("**/*.yaml"):
        results = raceml.load(results_filename)
        # get md5 hash of results file
        results_hash = (
            hashlib.sha256(
                repr(results_filename).encode() + repr(results).encode()
            ).hexdigest()
            + ".racecache"
        )

        cache_file = cache_folder / results_hash
        if cache_file.exists():
            cached_content = raceml.load(cache_file)
            if (
                cached_content.get("athletes_folder_hash") == athletes_folder_hash
                and cached_content.get("leagues_folder_hash") == leagues_folder_hash
                and cached_content.get("code_folder_hash") == code_folder_hash
            ):
                tally_board = raceml.deep_add(tally_board, cached_content["payload"])
                continue
            else:
                # delete cache file
                if cache_file.suffix == ".racecache":
                    cache_file.unlink()
                    print("Deleted out of date cache file: " + str(cache_file))

        cached_content = {
            "athletes_folder_hash": athletes_folder_hash,
            "leagues_folder_hash": leagues_folder_hash,
            "code_folder_hash": code_folder_hash,
            "payload": {},
        }

        competitor_type = results.get("competitor_type", "individual")

        if competitor_type == "individual":
            for athlete_id, athlete_result in results["results"].items():
                try:
                    athlete = lookup_athlete(athlete_id, data_folder / "athletes")
                except raceml.TemplateFileError:
                    continue

                eligible_leagues = get_eligible_leagues(
                    athlete, results, data_folder / "leagues"
                )

                for chosen_league in eligible_leagues:
                    chosen_league_id = chosen_league["_filename"]

                    if chosen_league["league_type"] == "individual":
                        contributes_to = athlete_id
                    elif chosen_league["league_type"] == "team":
                        contributes_to = athlete["team"]
                    else:
                        raise ValueError(
                            "No contributes_to method found for league: "
                            + chosen_league_id
                        )

                    competitors = []

                    for potential_competitor_id, potential_competitor_result in results[
                        "results"
                    ].items():
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

                    scoring_settings = chosen_league["scoring"][
                        results.get("scoring_type", results.get("type"))
                    ]

                    if chosen_league_id not in cached_content["payload"]:
                        cached_content["payload"][chosen_league_id] = {}
                    if (
                        contributes_to
                        not in cached_content["payload"][chosen_league_id]
                    ):
                        cached_content["payload"][chosen_league_id][contributes_to] = 0

                    points = calculate_points(
                        athlete_result,
                        competitors,
                        scoring_settings,
                        chosen_league_id,
                        results["type"],
                        results["name"],
                    )

                    if points != athlete_result.get("_debug_points"):
                        print(
                            results["name"],
                            athlete_id,
                            points,
                            athlete_result.get("_debug_points"),
                        )

                    cached_content["payload"][chosen_league_id][
                        contributes_to
                    ] += points
        elif competitor_type == "team":
            for team_name, team_result in results["results"].items():
                eligible_leagues = get_eligible_leagues(
                    team_name, results, data_folder / "leagues", competitor_type
                )

                for chosen_league in eligible_leagues:
                    if chosen_league["league_type"] != "team":
                        continue

                    chosen_league_id = chosen_league["_filename"]

                    contributes_to = team_name

                    competitors = []

                    for potential_competitor_id, potential_competitor_result in results[
                        "results"
                    ].items():
                        if chosen_league in get_eligible_leagues(
                            potential_competitor_id,
                            results,
                            data_folder / "leagues",
                            competitor_type,
                        ):
                            competitors.append(potential_competitor_result)

                    scoring_settings = chosen_league["scoring"][
                        results.get("scoring_type", results.get("type"))
                    ]

                    if chosen_league_id not in cached_content["payload"]:
                        cached_content["payload"][chosen_league_id] = {}
                    if (
                        contributes_to
                        not in cached_content["payload"][chosen_league_id]
                    ):
                        cached_content["payload"][chosen_league_id][contributes_to] = 0

                    points = calculate_points(
                        team_result,
                        competitors,
                        scoring_settings,
                        chosen_league_id,
                        results["type"],
                        results["name"],
                    )

                    if points != team_result.get("_debug_points"):
                        print(
                            results["name"],
                            team_name,
                            points,
                            team_result.get("_debug_points"),
                        )

                    cached_content["payload"][chosen_league_id][
                        contributes_to
                    ] += points
        else:
            raise ValueError("Unknown competitor_type: " + competitor_type)

        raceml.dump(cache_file, cached_content)
        # print(results["name"], ":", cached_content["payload"])
        tally_board = raceml.deep_add(tally_board, cached_content["payload"])
    return tally_board


if __name__ == "__main__":
    start_time = datetime.datetime.now()
    pprint(tally_data(sys.argv[1]))
    print("Time taken:", datetime.datetime.now() - start_time)
