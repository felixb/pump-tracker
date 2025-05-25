from pathlib import Path
from typing import Tuple

import gpxpy
from geopy.distance import geodesic

from gpx_file_handler import load_gpx


class Run:
    def __init__(self):
        self.first_point = None
        self.last_point = None
        self.last_speed = None
        self.max_speed = 0
        self.cum_dist = 0
        self.gpx_segment = gpxpy.gpx.GPXTrackSegment()

    def update_stats(self, speed, dist):
        self.last_speed = speed
        self.max_speed = max(self.max_speed, speed)
        self.cum_dist += dist

    def append(self, run):
        self.last_point = run.last_point
        self.last_speed = run.last_speed
        self.max_speed = max(self.max_speed, run.max_speed)
        self.gpx_segment.points += run.gpx_segment.points
        self.cum_dist = self.gpx_segment.length_2d()

    def duration(self):
        return self.gpx_segment.get_duration()


def __step_stats(p0, p1):
    dist = geodesic((p0.latitude, p0.longitude), (p1.latitude, p1.longitude)).meters
    time_spent = p1.time - p0.time
    speed = (dist * 60 * 60) / (time_spent.total_seconds() * 1000)
    return dist, time_spent, speed


def analyse(fn: Path | str, min_distance: int, min_speed: int, min_max_speed: int, min_duration: int,
            max_step_duration: int) -> Tuple[gpxpy.gpx, list[Run]]:
    """
    Load and analyse a single .gpx file and return it with a list of runs.
    """
    gpx = load_gpx(fn)
    runs = []
    run = Run()

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if run.last_point:
                    dist, time_spent, speed = __step_stats(run.last_point, point)
                    point.speed = speed

                    if speed > min_speed and time_spent.seconds < max_step_duration:
                        if not run.last_speed:
                            run.first_point = run.last_point
                            run.gpx_segment.points.append(run.last_point)
                        run.update_stats(speed, dist)
                        run.gpx_segment.points.append(point)
                    else:
                        if run.first_point:
                            if run.cum_dist > min_distance and run.max_speed > min_max_speed and run.duration() > min_duration:
                                if runs and (run.first_point.time - runs[-1].last_point.time).seconds < min_duration:
                                    runs[-1].append(run)
                                else:
                                    runs.append(run)
                        run = Run()
                run.last_point = point

    return gpx, runs


def get_best_run(runs: list[Run]) -> Run:
    """
    Get the best run based on run duration.
    """
    return sorted(runs, key=lambda r: (r.duration(), r.cum_dist), reverse=True)[0]
