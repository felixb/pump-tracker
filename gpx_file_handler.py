from pathlib import Path
from typing import Optional

import gpxpy
import gpxpy.gpx


def load_gpx(fn: Path | str) -> gpxpy.gpx:
    """
    Load a gpx file as gpxpy.gpx.
    """
    with open(fn, 'r') as fp:
        return gpxpy.parse(fp)


def save_gpx(fn: Path | str, gpx: gpxpy.gpx):
    """
    Save a gpxpy.gpx as gpx file.
    """
    with open(fn, 'w') as fp:
        fp.write(gpx.to_xml())


def new_gpx_file(base_gpx: Optional[gpxpy.gpx] = None, time=None):
    gpx = gpxpy.gpx.GPX()
    gpx.nsmap = base_gpx.nsmap
    gpx.schema_locations = gpx.schema_locations
    gpx.waypoints = base_gpx.waypoints
    gpx.description = "pump foiling ftw"
    if time:
        gpx.time = time
    else:
        gpx.time = base_gpx.time
    gpx.creator = "pump tracker - https://github.com/felixb/pump-tracker"
    return gpx
