import pathlib
import raceml
import simple_tally
import importlib


def run_tally(data_folder: pathlib.Path) -> dict:
    database_lock = raceml.DatabaseLock(data_folder)
    database_lock.acquire()
    try:
        return simple_tally.tally_data(data_folder, database_lock)
    finally:
        database_lock.release()


def test_simple_tally():
    data_folder = pathlib.Path(__file__).parent / "simple_tally_tests" / "test2"

    # delete folder data_folder/cache
    cache_folder = data_folder / "cache"
    if cache_folder.exists():
        for f in cache_folder.iterdir():
            f.unlink()
        cache_folder.rmdir()

    for i in range(5):
        assert (
            run_tally(data_folder)
            == importlib.import_module("simple_tally_tests.test2_expected").tb
        )
