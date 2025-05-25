import os
import sys
from pathlib import Path
from typing import Any
from dataclasses import dataclass

import yaml

__DEFAULT_CONFIG = {
    'tracks_dir': 'tracks',
    'downloads_dir': '~/Downloads/',
    'print_table': True,
    'write_best_gpx_file': True,
    'write_all_gpx_file': True,
    'write_png_files': True,
    'min_distance': 10,
    'min_speed': 7,
    'min_max_speed': 12,
    'min_duration': 3,
    'max_step_duration': 10,
}

__CONFIG_FILES = [
    'pump-tracker.yml',
    'pump-tracker.yaml',
    '~/.config/pump-tracker.yml',
    '~/.config/pump-tracker.yaml',
]


@dataclass(frozen=True)
class Config:
    tracks_dir: str
    downloads_dir: str
    print_table: bool
    write_best_gpx_file: bool
    write_all_gpx_file: bool
    write_png_files: bool
    min_distance: int
    min_speed: int
    min_max_speed: int
    min_duration: int
    max_step_duration: int


def load_config(args: list[str]) -> Config:
    """
    Load config from different sources if available:
    ./pump-tracker.y(a)ml
    ~/.config/pump-tracker.y(a)ml
    """
    config = __DEFAULT_CONFIG
    for f in __CONFIG_FILES:
        if (p := Path(os.path.expanduser(f))).exists():
            with open(p) as fp:
                c = yaml.safe_load(fp)
                config |= c

    for i, k in enumerate(sys.argv):
        if k.startswith('--') and (key := k[2:].replace('-', '_')) in __DEFAULT_CONFIG.keys():
            if len(sys.argv) >= i + 2 and not sys.argv[i + 1].startswith('--'):
                v = sys.argv[i + 1]
            else:
                v = True

            if isinstance(__DEFAULT_CONFIG[key], bool):
                v = v == True or str(v).lower() in ['true', 'yes']
            elif isinstance(__DEFAULT_CONFIG[key], int):
                v = int(v)
            else:
                v = str(v)

            config[key] = v

    return Config(**config)
