#! /usr/bin/env python3

import os
import sys
from dataclasses import dataclass

import gpxpy
import gpxpy.gpx
from geopy.distance import geodesic


def __load(fn):
    with open(fn, 'r') as fp:
        return gpxpy.parse(fp)


def __save(fn, gpx):
    with open(fn, 'w') as fp:
        fp.write(gpx.to_xml())


def import_files(path):
    """
    Import all .gpx files from given directory into ./tracks/ directory.
    """
    for f in os.listdir(path):
        if f.endswith('.gpx'):
            fn = os.path.join(path, f)
            print('importing', fn)
            gpx = __load(fn)
            dt = gpx.tracks[0].segments[0].points[0].time
            new_fn = os.path.join('tracks', dt.strftime('%Y-%m-%d-%H-%M-raw.gpx'))
            os.rename(fn, new_fn)


@dataclass(frozen=False)
class Run:
    first_point = None
    last_point = None
    last_speed = None
    max_speed = 0
    cum_dist = 0
    gpx_segment = gpxpy.gpx.GPXTrackSegment()

    def update_stats(self, speed, dist):
        self.last_speed = speed
        self.max_speed = max(self.max_speed, speed)
        self.cum_dist += dist

    def duration(self):
        return (self.last_point.time - self.first_point.time).total_seconds()


def __step_stats(p0, p1):
    dist = geodesic((p0.latitude, p0.longitude), (p1.latitude, p1.longitude)).meters
    time_spent = p1.time - p0.time
    speed = (dist * 60 * 60) / (time_spent.total_seconds() * 1000)
    return dist, time_spent, speed


def __all_runs_to_gpx(runs):
    gpx = gpxpy.gpx.GPX()
    for r in runs:
        t = gpxpy.gpx.GPXTrack()
        t.segments.append(r.gpx_segment)
        gpx.tracks.append(t)
    return gpx


def __get_best_run(runs):
    return sorted(runs, key=lambda r: r.duration(), reverse=True)[0]


def __best_run_to_gpx(run):
    gpx = gpxpy.gpx.GPX()
    t = gpxpy.gpx.GPXTrack()
    t.segments.append(run.gpx_segment)
    gpx.tracks.append(t)
    return gpx


def analyse(fn):
    """
    Analyse .gpx file.
    """
    gpx = __load(fn)
    runs = []

    for track in gpx.tracks:
        for segment in track.segments:
            run = Run()

            for point in segment.points:
                if run.last_point:
                    dist, time_spent, speed = __step_stats(run.last_point, point)

                    if speed > 5:
                        if not run.last_speed:
                            run.first_point = point
                        run.update_stats(speed, dist)
                        run.gpx_segment.points.append(point)
                    else:
                        if run.first_point:
                            if run.cum_dist > 10 and run.max_speed > 10:
                                runs.append(run)
                        run = Run()
                run.last_point = point

    all_gpx = __all_runs_to_gpx(runs)
    best_run = __get_best_run(runs)
    avg_duration = round(sum(r.duration() for r in runs) / len(runs))
    avg_distance = round(sum(r.cum_dist for r in runs) / len(runs))
    for i, run in enumerate(runs):
        print(f'{(i + 1):02}: {run.duration()}s {round(run.cum_dist)}m')
    print(f'best run: {best_run.duration()}s {round(best_run.cum_dist)}m')
    print(f'avg duration: {avg_duration}s')
    print(f'avg distance: {avg_distance}m')
    best_gpx = __best_run_to_gpx(best_run)
    __save(fn.replace('.gpx', '-all.gpx').replace('-raw-', '-'), all_gpx)
    __save(fn.replace('.gpx', '-best.gpx').replace('-raw-', '-'), best_gpx)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--import':
            if len(sys.argv) > 2:
                import_files(os.path.expanduser(sys.argv[2]))
            else:
                import_files(os.path.expanduser('~/Downloads/'))
        else:
            analyse(sys.argv[1])
    else:
        analyse('track.gpx')
