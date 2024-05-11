import geopy
import geopy.distance
import argparse

from utils.bearings_utils import parse_bearing
from utils.file_utils import read_from_file, get_row_val, read_headers_from_file, InvalidHeaders

parser = argparse.ArgumentParser(
    prog="bearingstogps",
    description=(
        "Given a starting GPS coordinate (longitude and lattitude), convert a series of bearings and distances into a "
        "line or shape"
    ),
    formatter_class=argparse.RawTextHelpFormatter,
)

parser.add_argument(
    "--infile",
    type=str,
    required=True,
    help=(
        "File of a series of bearings and distances describing a 'line' or 'shape'.  "
        "Required headers: ['bearing', 'distance'].  All distances must be in feet.\n\nExample:\n\n"
        "\t# Comment lines begin with \"#\".  Header line required:\n"
        "\tbearing\tdistance\tcomment\n"
        "\tnorth 77° 15' 00\" east\t103.75\tcase insensitive cardinal directions allowed.  Tip: put landmarks in an "
        "extra column.\n"
        "\tS 46° 59' 26\" E\t95\tExtra columns are ignored.  Abbreviations are OK.\n"
        "\tS 33 10 3 E\t50\tNon-digit characters in the angle are ignored.  The numbers just have to be in order of "
        "degrees(°), minutes('), and seconds(\").\n"
        "\tN 22.1d E\t60\tMinutes and seconds are optional, but if seconds are supplied, degrees and minutes must be "
        "supplied.\n"
        "\tS\t5.7\tDue south/north/east/west needs no degrees.\n"
        "\t340 55 03\t5.7\tNorth is assumed if the first value is a number.\n\n"
    ),
)
parser.add_argument(
    "--lon",
    type=float,
    required=True,
    help=(
        "Longitude of the starting coordinate, associated with the source of the first bearing and distance in "
        "--infile."
    ),
)
parser.add_argument(
    "--lat",
    type=float,
    required=True,
    help=(
        "Latitude of the starting coordinate, associated with the source of the first bearing and distance in --infile."
    ),
)
parser.add_argument(
    "--distance-units",
    "--units",
    type=str,
    choices=["feet", "poles", "rods"],
    help=(
        "Distance units that distances in --infile are in, so that they will be converted to the required unit "
        "(feet).  [1 pole/rod = 16.5 feet.]"
    ),
    dest="units",
)


args = vars(parser.parse_args())

headers = read_headers_from_file(args["infile"])

if "bearing" not in headers or "distance" not in headers:
    raise InvalidHeaders(headers, expected_headers=["bearing", "distance"])

data = read_from_file(args["infile"], dtype={"bearing": str, "distance": float})

lat = args["lat"]
lon = args["lon"]
points = [geopy.Point(lat, lon)]

print("lon,lat,zero")
print(f"{lon},{lat},0")

for _, row in data.iterrows():
    distance = get_row_val(row, "distance")  # feet
    bearing_str = get_row_val(row, "bearing")  # e.g. south 88º 27' 0" east

    if args["units"] == "poles" or args["units"] == "rods":
        distance *= 16.5

    # print(f"Input: {bearing_str}")
    bearing = parse_bearing(bearing_str)
    # print(f"bearing: {bearing} type: {type(bearing).__name__}")
    start_point = points[-1]

    end_point = geopy.distance.geodesic(feet=distance).destination(start_point, bearing)

    points.append(end_point)

    print(f"{end_point.longitude},{end_point.latitude},0")
