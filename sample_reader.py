"""Read YAML file and print to screen."""
from pprint import pprint
import pathlib
import argparse
import raceml

parser = argparse.ArgumentParser(description="Read YAML file and print to screen.")
parser.add_argument("filename", type=str, help="YAML file")
args = parser.parse_args()

filepath = pathlib.Path(args.filename).resolve()


data = raceml.load(filepath)

pprint(data)