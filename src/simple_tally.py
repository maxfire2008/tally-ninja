"""
This module provides functions to tally data for sports events.
It includes functions to calculate age, lookup athlete data,
get eligible leagues for an athlete, and cache results.

Classes:
    AttrDict: A dictionary with attribute access to keys.

Functions:
    calculate_age: Calculate age in years.
    get_eligible_leagues: Get eligible leagues for an athlete.
    tally_data: Tally data for sports events.

"""
import datetime
import hashlib
import pathlib
import sys
import jinja2
import subprocess

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

    if isinstance(born, datetime.datetime):
        born = born.date()
    if isinstance(today, datetime.datetime):
        today = today.date()

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
        return x
    elif isinstance(x, int):
        return x
    else:
        try:
            return int(x)
        except ValueError:
            return float(x)


def extract_int(x, default=None):
    # get all digits
    y = ""
    for i in x:
        if i in "0123456789":
            y += i
    if y:
        return int(y)
    return default


def rank_display(rank, unique_place=True):
    out = ""
    if not unique_place:
        out = "="

    out += str(rank)

    if 10 < rank % 100 < 20:
        out += "th"
    else:
        if rank % 10 == 1:
            out += "st"
        elif rank % 10 == 2:
            out += "nd"
        elif rank % 10 == 3:
            out += "rd"
        else:
            out += "th"

    return out


def get_keys_from_dict_list(dict_list, key):
    return [d.get(key) for d in dict_list]


def infdex(l: list, x) -> int:
    """Returns the index of x in l, if not found returns infinity.

    Keyword arguments:
    l -- the list to search
    x -- the item to find
    Returns: int
    """
    try:
        return l.index(x)
    except ValueError:
        return float("inf")


_days_events_cache = {}


def get_days_events(
    date, results_folder: pathlib.Path, database_lock: raceml.DatabaseLock
):
    database_lock.check()

    if isinstance(date, datetime.datetime):
        date = date.date()

    if date in _days_events_cache:
        return _days_events_cache[date]
    _days_events_cache[date] = []

    for results_filename in results_folder.glob("**/*.yaml"):
        results = raceml.load(results_filename, cache=True)
        results_date = results["date"]

        if isinstance(results_date, datetime.datetime):
            results_date = results_date.date()
        if results_date == date:
            _days_events_cache[date].append(results)

    return _days_events_cache[date]


_eligible_leagues_cache = {}


def get_eligible_leagues(
    athlete,
    results,
    leagues_folder: pathlib.Path,
    results_folder: pathlib.Path,
    database_lock: raceml.DatabaseLock,
    competitor_type: str = "individual",
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
    database_lock.check()

    arg_key = repr((athlete, results, leagues_folder))
    if arg_key in _eligible_leagues_cache:
        return _eligible_leagues_cache[arg_key]

    eligible_leagues = []

    for league_filename in leagues_folder.glob("**/*.yaml"):
        try:
            league = raceml.load(league_filename, cache=True)
        except raceml.TemplateFileError:
            continue

        athlete_eligible = True

        if competitor_type == "individual":
            env = {
                "event_distance": results.get("distance", None),
                "athlete_age": calculate_age(athlete["dob"], results["date"]),
                "athlete_gender": athlete["gender"],
                "athlete_ystart": athlete.get("ystart"),
                "days_events": get_days_events(
                    results["date"], results_folder, database_lock
                ),
            }
            interpreter = safeeval.SafeEval(
                {
                    "get_keys_from_dict_list": get_keys_from_dict_list,
                }
            )

            for criterion in league.get("eligibility", []):
                ast = interpreter.compile(criterion)
                result = interpreter.execute(ast, env)
                if not result:
                    athlete_eligible = False
                    break
        elif competitor_type == "team":
            if not league.get("permit_teams", False):
                athlete_eligible = False

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


_athlete_races_cache = {}


def get_races_for_athlete(
    athlete_id: str,
    data_folder: pathlib.Path,
    database_lock: raceml.DatabaseLock,
):
    database_lock.check()

    arg_key = repr((athlete_id, data_folder))
    if arg_key in _athlete_races_cache:
        return _athlete_races_cache[arg_key]

    races = {}

    for results_filename in data_folder.glob("results/**/*.yaml"):
        # open the results file
        results = raceml.load(results_filename, cache=True)

        # get the athlete's result
        athlete_result = results["results"].get(athlete_id, None)
        if athlete_result is not None:
            races[str(results_filename.relative_to(data_folder))] = results

    return races


_athlete_flags_cache = {}


def get_athlete_flags(
    athlete_id: str,
    athlete: dict,
    league: dict,
    data_folder: pathlib.Path,
    database_lock: raceml.DatabaseLock,
):
    database_lock.check()

    arg_key = repr((athlete_id, league, data_folder))
    if arg_key in _athlete_flags_cache:
        return _athlete_flags_cache[arg_key]

    flags = []
    for flag in league.get("flags", []):
        env = {
            "races_count": len(
                get_races_for_athlete(athlete_id, data_folder, database_lock)
            ),
            "races_count_in_league": len(
                list(
                    filter(
                        lambda race: league
                        in get_eligible_leagues(
                            athlete,
                            race,
                            data_folder / "leagues",
                            data_folder / "results",
                            database_lock,
                        )
                        and not race["results"].get(athlete_id, {}).get("DNS", False),
                        get_races_for_athlete(
                            athlete_id,
                            data_folder,
                            database_lock,
                        ).values(),
                    )
                )
            ),
        }

        interpreter = safeeval.SafeEval(
            {
                "get_keys_from_dict_list": get_keys_from_dict_list,
            }
        )

        ast = interpreter.compile(flag["expression"])
        result = interpreter.execute(ast, env)
        if result:
            flags.append(flag["name"])

    _athlete_flags_cache[arg_key] = flags
    return flags


def calculate_points(
    athlete_result,
    competitors,
    scoring_settings,
    chosen_league_id="Unknown",
    results_type="Unknown",
    results_name="Unknown",
    rank_output=False,
):
    place = None
    contrib_amount = None

    if scoring_settings["method"] in ["minus_place"]:
        if scoring_settings["sort_by"] in [
            "highest",
            "lowest",
        ]:
            # calculate place

            if scoring_settings.get("combine_method") == "max":
                unique_scores = [
                    max(c[scoring_settings["sort_key"]])
                    if c[scoring_settings["sort_key"]]
                    and not (
                        c.get("DNF", False) or c.get("DNS", False) or c.get("DQ", False)
                    )
                    else (
                        float("inf")
                        if scoring_settings["sort_by"] == "lowest"
                        else float("-inf")
                    )
                    for c in competitors
                ]
                my_score = (
                    max(athlete_result[scoring_settings["sort_key"]])
                    if athlete_result[scoring_settings["sort_key"]]
                    and not (
                        athlete_result.get("DNF", False)
                        or athlete_result.get("DNS", False)
                        or athlete_result.get("DQ", False)
                    )
                    else (
                        float("inf")
                        if scoring_settings["sort_by"] == "lowest"
                        else float("-inf")
                    )
                )
            else:
                unique_scores = [
                    c[scoring_settings["sort_key"]]
                    if not (
                        c.get("DNF", False) or c.get("DNS", False) or c.get("DQ", False)
                    )
                    else (
                        float("inf")
                        if scoring_settings["sort_by"] == "lowest"
                        else float("-inf")
                    )
                    for c in competitors
                ]
                my_score = (
                    athlete_result[scoring_settings["sort_key"]]
                    if not (
                        athlete_result.get("DNF", False)
                        or athlete_result.get("DNS", False)
                        or athlete_result.get("DQ", False)
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

            my_best = None
            for height, attempts in athlete_result["heights"].items():
                if True in attempts and (my_best is None or height > my_best):
                    my_best = height

            if my_best is None:
                # set DNF
                athlete_result["DNF"] = True
            else:
                for v in competitors:
                    if not (
                        v.get("DNF", False) or v.get("DNS", False) or v.get("DQ", False)
                    ):
                        their_best = None
                        for height, attempts in v["heights"].items():
                            if True in attempts and (
                                their_best is None or height > their_best
                            ):
                                their_best = height

                        if their_best is None:
                            continue

                        if their_best > my_best:
                            place += 1
                        elif their_best == my_best:
                            common_keys = sorted(
                                set(v["heights"].keys()).intersection(
                                    athlete_result["heights"].keys()
                                ),
                                reverse=True,
                            )
                            for key in common_keys:
                                if infdex(v["heights"][key], True) < infdex(
                                    athlete_result["heights"][key], True
                                ):
                                    place += 1
                                    break
                                if infdex(v["heights"][key], True) > infdex(
                                    athlete_result["heights"][key], True
                                ):
                                    break

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

    if (
        athlete_result.get("DNF", False)
        or athlete_result.get("DQ", False)
        or athlete_result.get("DNS", False)
    ):
        contrib_amount = 0

    if athlete_result.get("DNF", False):
        place = "DNF"
    elif athlete_result.get("DQ", False):
        place = "DQ"
    elif athlete_result.get("DNS", False):
        place = "DNS"

    if rank_output:
        return contrib_amount, place
    return contrib_amount


def tally_data(
    data_folder: pathlib.Path or str,
    database_lock: raceml.DatabaseLock,
    print_debug_points: bool = False,
) -> dict:
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
        if item.name in [".DS_Store", "built_results.html", "built_results.py"]:
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
        results = raceml.load(results_filename, cache=True)
        if len(results.get("results").keys()) == 0:
            print("WARNING:", results_filename, "has no results")
        # get md5 hash of results file
        results_hash = (
            "simple_tally_"
            + hashlib.sha256(
                repr(results_filename).encode() + repr(results).encode()
            ).hexdigest()
            + ".racecache"
        )

        cache_file = cache_folder / results_hash
        if cache_file.exists():
            cached_content = raceml.load(cache_file, cache=True)
            if (
                cached_content.get("athletes_folder_hash") == athletes_folder_hash
                and cached_content.get("leagues_folder_hash") == leagues_folder_hash
                and cached_content.get("code_folder_hash") == code_folder_hash
            ):
                tally_board = raceml.deep_add(tally_board, cached_content["payload"])
                continue
            # delete cache file
            if cache_file.suffix == ".racecache":
                cache_file.unlink()
                print("Deleted out of date cache file: " + str(cache_file))

        results_filename_relative_to_results_folder = str(
            results_filename.relative_to(results_folder)
        )

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
                    athlete = raceml.lookup_athlete(
                        athlete_id, data_folder / "athletes", database_lock
                    )
                except raceml.TemplateFileError:
                    continue

                try:
                    eligible_leagues = get_eligible_leagues(
                        athlete,
                        results,
                        data_folder / "leagues",
                        results_folder,
                        database_lock,
                    )
                except Exception as e:
                    raise ValueError(
                        "Error getting eligible leagues for athlete: "
                        + athlete_id
                        + " in results: "
                        + results["name"]
                    ) from e

                for chosen_league in eligible_leagues:
                    chosen_league_id = str(
                        pathlib.Path(chosen_league["_filepath"]).relative_to(
                            data_folder / "leagues"
                        )
                    )

                    flags = get_athlete_flags(
                        athlete_id,
                        athlete,
                        chosen_league,
                        data_folder,
                        database_lock,
                    )

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
                            potential_competitor = raceml.lookup_athlete(
                                potential_competitor_id,
                                data_folder / "athletes",
                                database_lock,
                            )
                        except raceml.TemplateFileError:
                            continue
                        if chosen_league in get_eligible_leagues(
                            potential_competitor,
                            results,
                            data_folder / "leagues",
                            results_folder,
                            database_lock,
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
                        cached_content["payload"][chosen_league_id][contributes_to] = {
                            "total": 0,
                            "per_event": {},
                        }

                    points, rank = calculate_points(
                        athlete_result,
                        competitors,
                        scoring_settings,
                        chosen_league_id,
                        results["type"],
                        results["name"],
                        rank_output=True,
                    )

                    if (
                        points != athlete_result.get("_debug_points")
                        and print_debug_points
                    ):
                        print(
                            results["name"],
                            athlete_id,
                            points,
                            athlete_result.get("_debug_points"),
                        )

                    cached_content["payload"][chosen_league_id][contributes_to][
                        "total"
                    ] += points

                    if chosen_league["league_type"] == "team":
                        if (
                            results_filename_relative_to_results_folder
                            not in cached_content["payload"][chosen_league_id][
                                contributes_to
                            ]["per_event"]
                        ):
                            cached_content["payload"][chosen_league_id][contributes_to][
                                "per_event"
                            ][results_filename_relative_to_results_folder] = []
                        cached_content["payload"][chosen_league_id][contributes_to][
                            "per_event"
                        ][results_filename_relative_to_results_folder].append(
                            {
                                "points": points,
                                "rank": rank,
                                "flags": [f"{f} for {athlete_id}" for f in flags],
                            }
                        )
                    else:
                        cached_content["payload"][chosen_league_id][contributes_to][
                            "per_event"
                        ][results_filename_relative_to_results_folder] = {
                            "points": points,
                            "rank": rank,
                            "flags": flags,
                        }
        elif competitor_type == "team":
            for team_name, team_result in results["results"].items():
                eligible_leagues = get_eligible_leagues(
                    team_name,
                    results,
                    data_folder / "leagues",
                    results_folder,
                    database_lock,
                    competitor_type,
                )

                for chosen_league in eligible_leagues:
                    if chosen_league["league_type"] != "team":
                        continue

                    chosen_league_id = str(
                        pathlib.Path(chosen_league["_filepath"]).relative_to(
                            data_folder / "leagues"
                        )
                    )

                    contributes_to = team_name

                    competitors = []

                    for potential_competitor_id, potential_competitor_result in results[
                        "results"
                    ].items():
                        if chosen_league in get_eligible_leagues(
                            potential_competitor_id,
                            results,
                            data_folder / "leagues",
                            results_folder,
                            database_lock,
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
                        cached_content["payload"][chosen_league_id][contributes_to] = {
                            "total": 0,
                            "per_event": {},
                        }

                    points, rank = calculate_points(
                        team_result,
                        competitors,
                        scoring_settings,
                        chosen_league_id,
                        results["type"],
                        results["name"],
                        rank_output=True,
                    )

                    if (
                        points != team_result.get("_debug_points")
                        and print_debug_points
                    ):
                        print(
                            results["name"],
                            team_name,
                            points,
                            team_result.get("_debug_points"),
                        )

                    cached_content["payload"][chosen_league_id][contributes_to][
                        "total"
                    ] += points

                    if chosen_league["league_type"] == "team":
                        if (
                            results_filename_relative_to_results_folder
                            not in cached_content["payload"][chosen_league_id][
                                contributes_to
                            ]["per_event"]
                        ):
                            cached_content["payload"][chosen_league_id][contributes_to][
                                "per_event"
                            ][results_filename_relative_to_results_folder] = []
                        cached_content["payload"][chosen_league_id][contributes_to][
                            "per_event"
                        ][results_filename_relative_to_results_folder].append(
                            {
                                "points": points,
                                "rank": rank,
                            }
                        )
                    else:
                        cached_content["payload"][chosen_league_id][contributes_to][
                            "per_event"
                        ][results_filename_relative_to_results_folder] = {
                            "points": points,
                            "rank": rank,
                        }

        else:
            raise ValueError("Unknown competitor_type: " + competitor_type)

        raceml.dump(cache_file, cached_content)
        # print(results["name"], ":", cached_content["payload"])
        tally_board = raceml.deep_add(tally_board, cached_content["payload"])

    for league_id, league_results in tally_board.items():
        for athlete_id, athlete_results in league_results.items():
            athlete_flags = set()
            for event_id, event_results in athlete_results["per_event"].items():
                if isinstance(event_results, dict):
                    athlete_flags.update(event_results.get("flags", []))
                    if "flags" in event_results:
                        del event_results["flags"]
                elif isinstance(event_results, list):
                    for event_result in event_results:
                        athlete_flags.update(event_result.get("flags", []))
                        if "flags" in event_result:
                            del event_result["flags"]
            athlete_results["flags"] = list(athlete_flags)

    return tally_board


def results_to_html(
    tally_board,
    open_database: bool = False,
    data_folder: pathlib.Path = None,
    database_lock: raceml.DatabaseLock = None,
    template: str = None,
    write_file: bool = False,
):
    if open_database:
        if database_lock is None:
            raise ValueError("database_lock must be provided if open_database is True")
        if data_folder is None:
            raise ValueError("data_folder must be provided if open_database is True")
        database_lock.check()

    leagues = {}
    league_total_points = {}

    # iterate through leagues
    for league, league_results in sorted(
        tally_board.items(), key=lambda x: (extract_int(x[0], default=0), x[0])
    ):
        league_total_points[league] = 0
        if open_database:
            league_type = raceml.load(data_folder / "leagues" / league, cache=True)[
                "league_type"
            ]
        else:
            league_type = "individual"

        league_results_filtered = {}
        for athlete_id, athlete_results in league_results.items():
            if "not_enough_races" in athlete_results["flags"]:
                continue

            league_results_filtered[athlete_id] = athlete_results

        all_events = {}
        for athlete_results in league_results_filtered.values():
            for event in athlete_results["per_event"].keys():
                if open_database:
                    event_name = raceml.load(
                        data_folder / "results" / event, cache=True
                    )["name"]
                    event_date = raceml.load(
                        data_folder / "results" / event, cache=True
                    )["date"]
                else:
                    event_name = event
                    event_date = None
                all_events[event] = {
                    "name": event_name,
                    "date": event_date,
                }

        if open_database:
            league_name = raceml.load(data_folder / "leagues" / league, cache=True)[
                "name"
            ]
        else:
            league_name = league

        current_league = {
            "name": league_name,
            "all_events": sorted(
                all_events.items(),
                key=lambda x: (
                    (
                        x[1]["date"]
                        if isinstance(x[1]["date"], datetime.datetime)
                        else (
                            datetime.datetime.combine(x[1]["date"], datetime.time.min)
                            if isinstance(x[1]["date"], datetime.date)
                            else (
                                datetime.datetime.fromisoformat(x[1]["date"])
                                if isinstance(x[1]["date"], str)
                                else None
                            )
                        )
                    ),
                    x[1]["name"],
                    x[0],
                ),
            ),
            "results": [],
            "league_type": league_type,
        }

        for athlete_id, points in sorted(
            league_results_filtered.items(), key=lambda x: x[1]["total"], reverse=True
        ):
            per_event_points = {}

            for event in all_events:
                if league_type == "individual":
                    if event in points["per_event"]:
                        mine_unique_place = True
                        for other_id, points_other in league_results_filtered.items():
                            if points_other["per_event"].get(event, {}).get(
                                "rank"
                            ) == points["per_event"].get(event, {}).get("rank") and (
                                other_id != athlete_id
                            ):
                                mine_unique_place = False
                                break
                        if isinstance(points["per_event"][event]["rank"], int):
                            rank = points["per_event"][event]["rank"] + 1
                            rank_to_display = rank_display(rank, mine_unique_place)
                        else:
                            rank_to_display = points["per_event"][event]["rank"]
                        per_event_points[event] = {
                            "points": points["per_event"][event]["points"],
                            "rank": rank_to_display,
                        }
                    else:
                        per_event_points[event] = {
                            "points": "-",
                            "rank": "-",
                        }
                elif league_type == "team":
                    if event in points["per_event"]:
                        if any(
                            isinstance(x.get("rank"), int)
                            for x in points["per_event"].get(event, [])
                        ):
                            mine_unique_place = True
                            min_rank = min(
                                [
                                    x.get("rank")
                                    for x in filter(
                                        lambda x: isinstance(x.get("rank"), int),
                                        points["per_event"].get(event, []),
                                    )
                                ]
                            )
                            for (
                                other_id,
                                points_other,
                            ) in league_results_filtered.items():
                                try:
                                    min_other = min(
                                        [
                                            x.get("rank")
                                            for x in filter(
                                                lambda x: isinstance(
                                                    x.get("rank"), int
                                                ),
                                                points_other["per_event"].get(
                                                    event, []
                                                ),
                                            )
                                        ]
                                    )
                                except ValueError:
                                    continue

                                if min_other == min_rank and other_id != athlete_id:
                                    mine_unique_place = False
                                    break
                            total_points = sum(
                                [
                                    x.get("points")
                                    for x in points["per_event"].get(event, [])
                                ]
                            )
                            if isinstance(min_rank, int):
                                rank = min_rank + 1
                                rank_to_display = rank_display(rank, mine_unique_place)
                            else:
                                rank_to_display = min_rank
                            per_event_points[event] = {
                                "points": total_points,
                                "rank": rank_to_display,
                            }
                        else:
                            per_event_points[event] = {
                                "points": 0,
                                "rank": ", ".join(
                                    [
                                        x.get("rank")
                                        for x in filter(
                                            lambda x: x.get("rank") is not None,
                                            points["per_event"].get(event, []),
                                        )
                                    ]
                                ),
                            }
                    else:
                        per_event_points[event] = {
                            "points": "-",
                            "rank": "-",
                        }

            if open_database and league_type == "individual":
                athlete_name = raceml.lookup_athlete(
                    athlete_id, data_folder / "athletes", database_lock
                )["name"]
            else:
                athlete_name = athlete_id

            # get rank for athlete
            rank = 1
            rank_unique_place = True
            for other_athlete_id, points_other in league_results_filtered.items():
                if points_other["total"] > points["total"]:
                    rank += 1
                if (
                    points_other["total"] == points["total"]
                    and other_athlete_id != athlete_id
                ):
                    rank_unique_place = False

            league_total_points[league] += points["total"]

            current_league["results"].append(
                {
                    "name": athlete_name,
                    "total": points["total"],
                    "rank": rank_display(rank, rank_unique_place),
                    "per_event": per_event_points,
                    "flags": points["flags"],
                }
            )

        leagues[league] = current_league

    if template is None:
        with open("template.html", "r", encoding="utf-8") as tf:
            template = jinja2.Template(tf.read())

    results_html = template.render(
        leagues=leagues, league_total_points=league_total_points
    )

    if write_file:
        with open("built_results.html", "w", encoding="utf-8") as f:
            f.write(results_html)

    return results_html


if __name__ == "__main__":
    start_time = datetime.datetime.now()

    if len(sys.argv) > 1:
        data_folder = pathlib.Path(sys.argv[1])
    else:
        data_folder = pathlib.Path(input("PATH:"))

    database_lock = raceml.DatabaseLock(data_folder)
    database_lock.acquire()
    try:
        tb = tally_data(data_folder, database_lock)

        with open("built_results.py", "w+", encoding="utf-8") as f:
            f.write("tb = " + repr(tb))
        subprocess.run([sys.executable, "-m", "black", "built_results.py"], check=False)

        results_to_html(
            tb,
            open_database=True,
            data_folder=data_folder,
            database_lock=database_lock,
            write_file=True,
        )
    finally:
        database_lock.release()

    print("Time taken:", datetime.datetime.now() - start_time)
