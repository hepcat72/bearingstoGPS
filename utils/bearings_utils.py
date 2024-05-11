import re

# For parsing bearings
bearing_pat = re.compile(r"([SOUTHsouthEAeaWwNRnr]*)\s*([^SOUTHsouthEAeaWwNRnr]*)\s*([SOUTHsouthEAeaWwNRnr]*)")
angle_pat = re.compile(r"([\+\-\.0-9]*)[^\+\-\.0-9]*([\+\-\.0-9]*)[^\+\-\.0-9]*([\+\-\.0-9]*)")

def parse_bearing(bearing_str) -> float:
    """Takes a string like south 37 26 50 east and converts it to a single decimal value describing degrees clockwise
    (/eastward) of north.  The numbers are degrees, munites and seconds.  All are optional (defaulting to 0), but must
    be supplied from left to right.  In other words, you cannot supply '23' to mean '0 0 23' (i.e. 23 seconds east of
    north).  Other than the (case-insensitive) words north east south west, non-numeric characters are ignored (other
    than as delimiters).  Negative signs are allowed, but will be converted to positive values by adding 360.  Seconds
    and minutes must be 0-60 and degrees (after adding seconds and minutes) must be between 0 - 360.
    Args:
        bearing_str (string): E.g. "south 22 45 0 east"
    Exceptions:
        ValueError
    Returns:
        bearing (float): Value between 0-360
    """

    init = "north"
    dir = "east"
    bearing = 0.0  # in degrees eastward of North (0 - 360 degrees)
    angle_dir = 1  # 1 or -1

    bearing_match = re.search(bearing_pat, bearing_str)

    if bearing_match:
        bearing_groups = bearing_match.groups()

        init_str = bearing_groups[0]
        angle_str = bearing_groups[1].strip()
        dir_str = bearing_groups[2]

        if init_str.startswith("E") or init_str.startswith("e"):
            init = "east"
            bearing = 90.0
        elif init_str.startswith("S") or init_str.startswith("s"):
            init = "south"
            bearing = 180.0
        elif init_str.startswith("W") or init_str.startswith("w"):
            init = "east"
            bearing = 270.0

        if dir_str.startswith("S") or dir_str.startswith("s"):
            dir = "south"
            if init == "west":
                angle_dir = -1
        elif dir_str.startswith("N") or dir_str.startswith("n"):
            dir = "north"
            if init == "east":
                bearing = 360.0
                angle_dir = -1
        elif dir_str.startswith("W") or dir_str.startswith("w"):
            dir = "west"
            if init == "north":
                angle_dir = -1
        else:  # east
            if init == "south":
                angle_dir = -1
        # print(f"Init parse: init: {init_str} -> {init} angle: [{angle_str}] -> {angle_dir} dir: {dir_str} -> {dir} init bearing: {bearing}")

        if (
            ((init == "south" or init == "north") and (dir == "south" or dir == "north"))
            or ((init == "west" or init == "east") and (dir == "west" or dir == "east"))
        ):
            raise ValueError(
                f"Invalid initial and directional cardinal directions: {init}, {dir} parsed from bearing: "
                f"{bearing_str}.  Cannot be the same or opposing."
            )

        angle_match = re.search(angle_pat, angle_str)

        if angle_match:
            angle_groups = angle_match.groups()

            degrees_str = angle_groups[0]
            minutes_str = angle_groups[1]
            seconds_str = angle_groups[2]

            degrees_diff = 0.0
            minutes_diff = 0.0
            seconds_diff = 0.0

            if degrees_str != "":
                degrees_diff = angle_dir * float(degrees_str)
                bearing += degrees_diff
            if minutes_str != "":
                minutes_diff = angle_dir * float(minutes_str) / 60
                bearing += minutes_diff
            if seconds_str != "":
                seconds_diff = angle_dir * float(seconds_str) / 3600
                bearing += seconds_diff
            # print(f"angle parse: angle str: {angle_str} degrees: {degrees_str} -> {degrees_diff} minutes: {minutes_str} -> {minutes_diff} seconds: {seconds_str} -> {seconds_diff} new bearing: {bearing}")
        else:
            raise ValueError(f"Could not parse angle: {angle_str}.")
    else:
        raise ValueError(f"Could not parse bearing: {bearing_str}.")

    if bearing < 0:
        bearing += 360.0

    if bearing < 0.0 or bearing > 360.0:
        raise ValueError(f"Invalid bearing result: {bearing}.")

    return bearing
