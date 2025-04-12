#! /usr/bin/env python3
'''
analyse your gpx file for pump foiling, split runs, show best run and averages

Example:
        
        ---- Activity Report ----
        
        Total Runs: 1
        
        Average Duration: 5.0 seconds
        Average Distance: 13.01 meters
        
        Best Run:
        Start Time: 2025-04-12 13:43:41
        End Time: 2025-04-12 13:43:46
        Distance: 13.01 meters
        Duration: 5.0 seconds
        Speed: 9.36 km/h

        ...
'''
import pytz
import os
import sys

import gpxpy
import gpxpy.gpx
import staticmap

from datetime import datetime
from geopy.distance import geodesic


# Colors
SPEED_BUCKET_COLORS = [
    '#fffafa', '#ffebeb', '#ffdbdb', '#ffcccc', '#ffbdbd', '#ffadad',
    '#ff9e9e', '#ff8f8f', '#ff8080', '#ff7070', '#ff6161', '#ff5252',
    '#ff4242', '#ff3333', '#ff2424', '#ff1414', '#ff0f0f', '#ff0a0a'
]
SPEED_BUCKETS = [10 + i for i in range(len(SPEED_BUCKET_COLORS))]


class UNIT:
    METRIC = 'm'


class Run:

    def __init__(self, units=UNIT.METRIC):
        # properties
        self.max_speed = 0
        self.distance = 0

        # calc
        self.first_point = None
        self.last_point = None
        self.last_speed = None
        self.gpx_segment = gpxpy.gpx.GPXTrackSegment()

    def update_speed_and_dist(self, speed, dist):
        ''' update speed and dist '''
        self.last_speed = speed
        self.max_speed = max(self.max_speed, speed)
        self.distance += dist

    def append_segment(self, run):
        self.last_point = run.last_point
        self.last_speed = run.last_speed
        self.max_speed = max(self.max_speed, run.max_speed)
        self.gpx_segment.points += run.gpx_segment.points
        self.distance = self.gpx_segment.length_2d()

    @property
    def duration(self):
        return self.gpx_segment.get_duration()

    @property
    def speed(self):
        return self.distance / self.duration

    @property
    def start(self):
        return self.first_point.time

    @property
    def end(self):
        return self.last_point.time

    @property
    def __dict__(self):
        return {
            'start': self.start,
            'end': self.end,
            'distance': self.distance,
            'duration': self.duration,
            'speed': self.speed  # m/s
        }


class Activity:
    '''
    analyse GPX file of an Activity
    params:
        filepath: filepath and name, e.g. tracks/Lunch_Ride.gpx
        kwargs:
            speed_start_threshold:
                minimum to consider starting a run, default 7 km/h
            speed_min_for_valid_run:
                must reach this during the run, default 10 km/h
            distance_min_for_valid_run:
                total run distance, default 10 meters
            duration_min_for_valid_run:
                minimum run time, default 3 seconds
            max_time_between_points:
                max time gap between GPS points, default 10 seconds
    '''
    def __init__(self, filepath, **kwargs):
        self.filepath = filepath
        self.gpx = self.load_gpx(filepath)
        self.runs = []
        self.statistics = {}

        # Create GPX split files
        self.create_split_gpx = kwargs.pop('create_split_gpx', False)
        self.create_split_png = kwargs.pop('create_split_png', False)

        # Thresholds for run detection
        self.speed_start_threshold = kwargs.pop(
            'speed_start_threshold', 7)
        self.distance_min_for_valid_run = kwargs.pop(
            'distance_min_for_valid_run', 10)
        self.speed_min_for_valid_run = kwargs.pop(
            'speed_min_for_valid_run', 10)
        self.duration_min_for_valid_run = kwargs.pop(
            'duration_min_for_valid_run', 3)
        self.max_time_between_points = kwargs.pop(
            'max_time_between_points', 10)

        # units
        self.units = kwargs.pop('units', UNIT.METRIC)
        self.precision = kwargs.pop('precision', '.1f')
        self.timezone = pytz.timezone(kwargs.pop('timezone', 'Europe/Zurich'))

    # helpers
    def format_duration(self, seconds):
        """Format duration in seconds to a human-readable string."""
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes)}m {int(seconds)}s"

    def format_speed(self, speed_mps):
        if self.units == UNIT.METRIC:
            # Convert speed from meters per second (m/s) to kilometers per hour (km/h).
            return speed_mps * 3.6
        return ValueError('No output format given')

    def format_date_time(self, utc_time):
        """
        Convert UTC time to local time in Europe/Zurich timezone and return the formatted string.
        """
        # Ensure the input time is in UTC, if it's naive we assume it's UTC
        utc_time = utc_time.astimezone(pytz.utc)

        # Convert to Zurich time
        local_time = utc_time.astimezone(self.timezone)

        # Return formatted time
        return local_time.strftime('%H:%M:%S')

    def generate_report(stats):
        """Generate a formatted report from the provided stats."""

    def new_gpx(self, time=None):
        gpx = gpxpy.gpx.GPX()
        gpx.nsmap = gpx.nsmap
        gpx.schema_locations = gpx.schema_locations
        gpx.waypoints = self.gpx.waypoints
        gpx.description = "pump foiling ftw"
        if time:
            gpx.time = time
        else:
            gpx.time = base_gpx.time
        gpx.creator = "pump tracker - https://github.com/felixb/pump-tracker"
        return gpx


    def all_runs_to_gpx(self):
        gpx = self.new_gpx(self.runs[0].first_point.time)
        for r in self.runs:
            t = gpxpy.gpx.GPXTrack()
            t.segments.append(r.gpx_segment)
            gpx.tracks.append(t)
        return gpx

    def get_best_run(self):
        return sorted(
            self.runs, key=lambda run: (run.duration, run.distance),
            reverse=True
        )[0]

    def best_run_to_gpx(self, run):
        gpx = self.new_gpx(run.first_point.time)
        t = gpxpy.gpx.GPXTrack()
        t.segments.append(run.gpx_segment)
        gpx.tracks.append(t)
        return gpx

    @staticmethod
    def load_gpx(filepath):
        ''' laod gpx class '''
        with open(filepath, 'r') as file:
            return gpxpy.parse(file)

    @staticmethod
    def save_gpx(filepath, gpx):
        with open(filepath, 'w') as fp:
            fp.write(gpx.to_xml())

    @staticmethod
    def save_png(filepath, run):
        m = staticmap.StaticMap(1024, 1024, 1, 1)
        for i in range(len(run.gpx_segment.points) - 1):
            first = run.gpx_segment.points[i]
            second = run.gpx_segment.points[i + 1]
            if second.speed > SPEED_BUCKETS[-1]:
                color = SPEED_BUCKET_COLORS[-1]
            else:
                color = None
                for i, limit in enumerate(SPEED_BUCKETS):
                    if second.speed < limit:
                        break
                    color = SPEED_BUCKET_COLORS[i]
            m.add_line(
                staticmap.Line([
                    [first.longitude, first.latitude],
                    [second.longitude, second.latitude]
                ], color, 2, True))
        m.render().save(filepath)

    @staticmethod
    def step_stats(start, end):
        dist = geodesic(
            (start.latitude, start.longitude),
            (end.latitude, end.longitude)
        ).meters
        time_spent = end.time - start.time
        speed = (dist * 60 * 60) / (time_spent.total_seconds() * 1000)
        return dist, time_spent, speed

    # comparisons
    def is_valid_step(self, speed, time):
        return (
            speed > self.speed_start_threshold
            and time.seconds < self.max_time_between_points
        )

    def is_valid_run(self, run):
        if (run.first_point
                and run.distance > self.distance_min_for_valid_run
                and run.max_speed > self.speed_min_for_valid_run
                and run.duration > self.duration_min_for_valid_run):
            return True
        return False

    def is_new_segment(self, run):
        if self.runs:
            time_diff = (
                run.first_point.time - self.runs[-1].last_point.time).seconds
            if time_diff < self.max_time_between_points:
                return True
        return False

    def analyse(self):
        """
        Analyse .gpx file.

        example output: {
            'runs': [{
                'start': datetime.datetime(2025, 4, 12, 11, 43, 41, tzinfo=SimpleTZ('Z')),
                'end': datetime.datetime(2025, 4, 12, 11, 43, 46, tzinfo=SimpleTZ('Z')),
                'distance': 13.006821209424572,
                'duration': 5.0,
                'speed': 9.364911270785694
            }],
            'best_run': {
                'start': datetime.datetime(2025, 4, 12, 11, 43, 41, tzinfo=SimpleTZ('Z')),
                'end': datetime.datetime(2025, 4, 12, 11, 43, 46, tzinfo=SimpleTZ('Z')),
                'distance': 13.006821209424572,
                'duration': 5.0,
                'speed': 9.364911270785694},
                'avg_duration': 5.0,
                'avg_distance': 13.006821209424572
            }]

        """
        # Make runs
        run = Run(self.units)
        for track in self.gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if run.last_point:
                        dist, time_spent, speed = self.step_stats(
                            run.last_point, point)
                        point.speed = speed
                        if self.is_valid_step(speed, time_spent):
                            if not run.last_speed:
                                run.first_point = run.last_point
                                run.gpx_segment.points.append(run.last_point)
                            run.update_speed_and_dist(speed, dist)
                            run.gpx_segment.points.append(point)
                        else:
                            if run.first_point:
                                if self.is_valid_run(run):
                                    if self.is_new_segment(run):
                                        self.runs[-1].append_segment(run)
                                    else:
                                        self.runs.append(run)
                            run = Run(self.units)  # new run
                    run.last_point = point

        # Make statistics
        best_run = self.get_best_run()
        avg_duration = sum(run.duration for run in self.runs) / len(self.runs)
        avg_distance = sum(run.distance for run in self.runs) / len(self.runs)

        # Update record
        self.statistics.update({
            'runs': [run.__dict__ for run in self.runs],
            'best_run': best_run.__dict__,
            'avg_duration': avg_duration,
            'avg_distance': avg_distance
        })

        if self.create_split_gpx: 
            # Save GPX all
            all_gpx = self.all_runs_to_gpx()
            filepath = self.filepath.replace('.gpx', '-all.gpx').replace('-raw-', '-')
            self.save_gpx(filepath, all_gpx)

            # Save GPX best
            best_gpx = self.best_run_to_gpx(best_run)
            filepath = self.filepath.replace('.gpx', '-best.gpx').replace('-raw-', '-')
            self.save_gpx(filepath, best_gpx)

        if self.create_split_png:
            # Save picture for each run
            for i, run in enumerate(self.runs):
                filepath = self.filepath.replace('.gpx', f'-{(i + 1):02}.png').replace('-raw-', '-')
                self.save_png(filepath, run)

        return self.statistics

    def generate_report(self):
        '''Generate a formatted report from the provided stats.
        '''
        stats = self.statistics if self.statistics else self.analyse()
        report = []

        # Total successful runs section
        report.append("---- Run Analysis Report ----")
        report.append("\nTotal Successful Runs: {}".format(len(stats['runs'])))

        # Best run section
        best_run = stats['best_run']
        start_time = self.format_date_time(best_run['start'])
        end_time = self.format_date_time(best_run['end'])
        distance = best_run['distance']
        duration = self.format_duration(best_run['duration'])
        speed_kph = self.format_speed(best_run['speed'])

        report.append("\nBest Run:")
        report.append("---------------------------")
        report.append(f"Start Time: {start_time}")
        report.append(f"End Time: {end_time}")
        report.append(f"Distance: {distance:{self.precision}} meters")
        report.append(f"Duration: {duration}")
        report.append(f"Speed: {speed_kph:{self.precision}} km/h")
        report.append("")

        # Overall statistics section
        avg_duration = self.format_duration(stats['avg_duration'])
        avg_distance = stats['avg_distance']

        report.append("\nOverall Statistics:")
        report.append("---------------------------")
        report.append(f"Average Duration of Successful Runs: {avg_duration}")
        report.append(f"Average Distance of Successful Runs: {avg_distance:{self.precision}} meters")
        report.append("")

        # Detail each run
        report.append("\nRuns:")
        report.append("---------------------------")
        for idx, run in enumerate(stats['runs']):
            start_time = self.format_date_time(run['start'])
            end_time = self.format_date_time(run['end'])
            distance = run['distance']
            duration = self.format_duration(run['duration'])
            speed_kph = self.format_speed(run['speed'])

            report.append(f"{idx + 1}. Start Time: {start_time}")
            report.append(f"   End Time: {end_time}")
            report.append(f"   Distance: {distance:{self.precision}} meters")
            report.append(f"   Duration: {duration}")
            report.append(f"   Speed: {speed_kph:{self.precision}} km/h")
            report.append("")

        # End of report
        report.append("---------------------------")

        return "\n".join(report)


if __name__ == '__main__':
    # e.g. main.py tracks/Lunch_Ride.gpx
    if len(sys.argv) > 1:
        _, filepath, *ignore = sys.argv
        activity = Activity(
            filepath,
            create_split_gpx=False,
            create_split_png=False,
            speed_start_threshold=7,
            distance_min_for_valid_run=10,
            speed_min_for_valid_run=10,
            duration_min_for_valid_run=3,
            max_time_between_points=10,
        )
        _stats = activity.analyse()
        report = activity.generate_report()
        print(report)
    else:
        raise ValueError('No file given')
