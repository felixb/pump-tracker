#! /usr/bin/env python3

import os
import sys

import gpxpy.gpx

from config import load_config, Config
from gpx_file_handler import *
from gpx_importer import import_files
from map_generator import save_png
from track_analyser import Run, analyse, get_best_run


def __all_runs_to_gpx(base_gpx, runs):
    gpx = new_gpx_file(base_gpx, runs[0].first_point.time)
    for r in runs:
        t = gpxpy.gpx.GPXTrack()
        t.segments.append(r.gpx_segment)
        gpx.tracks.append(t)
    return gpx


def __best_run_to_gpx(base_gpx, run):
    gpx = new_gpx_file(base_gpx, run.first_point.time)
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


def print_table(best_run: Run, runs: list[Run]):
    avg_duration = round(sum(r.duration() for r in runs) / len(runs))
    avg_distance = round(sum(r.cum_dist for r in runs) / len(runs))
    for i, run in enumerate(runs):
        __print_run(f'{(i + 1):02}', run)
    __print_run('best run', best_run)
    print(f'avg duration: {__printable_duration(avg_duration)}')
    print(f'avg distance: {avg_distance}m')


def analyse_and_print(fn: str, config: Config):
    gpx, runs = analyse(fn, config.min_distance, config.min_speed, config.min_max_speed,
                        config.min_duration, config.max_step_duration)
    best_run = get_best_run(runs)

    if config.print_table:
        print_table(best_run, runs)

    if config.write_best_gpx_file:
        best_gpx = __best_run_to_gpx(gpx, best_run)
        save_gpx(fn.replace('.gpx', '-best.gpx').replace('-raw-', '-'), best_gpx)

    if config.write_all_gpx_file:
        all_gpx = __all_runs_to_gpx(gpx, runs)
        save_gpx(fn.replace('.gpx', '-all.gpx').replace('-raw-', '-'), all_gpx)

    if config.write_png_files:
        for i, run in enumerate(runs):
            save_png(fn.replace('.gpx', f'-{(i + 1):02}.png').replace('-raw-', '-'), run)


if __name__ == '__main__':
    config = load_config(sys.argv)

    if len(sys.argv) > 1:
        if sys.argv[1] == '--import':
            if len(sys.argv) > 2:
                import_files(os.path.expanduser(sys.argv[2]), config.tracks_dir)
            else:
                import_files(os.path.expanduser(config.downloads_dir), config.tracks_dir)
        else:
            analyse_and_print(sys.argv[1], config)
    else:
        analyse_and_print('track.gpx', config)
