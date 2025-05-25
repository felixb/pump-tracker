import os
from pathlib import Path

from gpx_file_handler import load_gpx


def import_files(source_path: Path | str, target_path: Path | str):
    """
    Import all .gpx files from source_path into target_path directory.
    Rename files on the go with a timestamp as file name.
    """
    for f in os.listdir(source_path):
        if f.endswith('.gpx'):
            fn = os.path.join(source_path, f)
            print('importing', fn)
            gpx = load_gpx(fn)
            dt = gpx.tracks[0].segments[0].points[0].time
            new_fn = os.path.join(target_path, dt.strftime('%Y-%m-%d-%H-%M-raw.gpx'))
            os.rename(fn, new_fn)
