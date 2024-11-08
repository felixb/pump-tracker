#! /usr/bin/env python3

import os
import sys

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


def __new_gpx(base_gpx=None, time=None):
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


def __all_runs_to_gpx(base_gpx, runs):
    gpx = __new_gpx(base_gpx, runs[0].first_point.time)
    for r in runs:
        t = gpxpy.gpx.GPXTrack()
        t.segments.append(r.gpx_segment)
        gpx.tracks.append(t)
    return gpx


def __get_best_run(runs):
    return sorted(runs, key=lambda r: r.duration(), reverse=True)[0]


def __best_run_to_gpx(base_gpx, run):
    gpx = __new_gpx(base_gpx, run.first_point.time)
    t = gpxpy.gpx.GPXTrack()
    t.segments.append(run.gpx_segment)
    gpx.tracks.append(t)
    return gpx


def __printable_duration(s):
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    seconds = int(s % 60)
    parts = []
    if hours:
        parts.append(f'{hours}h')
    if minutes:
        parts.append(f'{minutes}m')
    if seconds:
        parts.append(f'{seconds}s')
    return ''.join(parts)


def __print_run(id, run):
    speed = float(run.cum_dist * 60 * 60) / 1000 / run.duration()
    print(
        f'{id} {run.first_point.time:%H:%M:%S}-{run.last_point.time:%H:%M:%S} : {__printable_duration(run.duration())} {round(run.cum_dist)}m {round(speed, 1)}km/h')


def analyse(fn):
    """
    Analyse .gpx file.
    """
    gpx = __load(fn)
    runs = []
    run = Run()

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if run.last_point:
                    dist, time_spent, speed = __step_stats(run.last_point, point)

                    if speed > 7 and time_spent.seconds < 10:
                        if not run.last_speed:
                            run.first_point = point
                        run.update_stats(speed, dist)
                        run.gpx_segment.points.append(point)
                    else:
                        if run.first_point:
                            if run.cum_dist > 10 and run.max_speed > 10 and run.duration() > 3:
                                if runs and (run.first_point.time - runs[-1].last_point.time).seconds < 10:
                                    runs[-1].append(run)
                                else:
                                    runs.append(run)
                        run = Run()
                run.last_point = point

    all_gpx = __all_runs_to_gpx(gpx, runs)
    best_run = __get_best_run(runs)
    avg_duration = round(sum(r.duration() for r in runs) / len(runs))
    avg_distance = round(sum(r.cum_dist for r in runs) / len(runs))
    for i, run in enumerate(runs):
        __print_run(f'{(i + 1):02}', run)
    __print_run('best run', best_run)
    print(f'avg duration: {__printable_duration(avg_duration)}')
    print(f'avg distance: {avg_distance}m')
    best_gpx = __best_run_to_gpx(gpx, best_run)
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
