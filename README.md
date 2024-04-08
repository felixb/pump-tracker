# pump tracker

This tiny piece of software analyses your pump foiling gps tracks.
It generates some useful stats and spits out your best runs.

Foil at your own risk.

## Usage

### Import .gpx files

Run the import command to move all your .gpx files from `~/Downloads/` to `./tracks/`. 

```shell
make import
# or
pipenv run ./main.py --import
```

### Analyse

Run the default command to analyse the .gpx files.
For each .gpx file a set of output files is created:

* %-best.gpx containing the best run as single .gpx file
* %-all.gpx containing all runs as separate tracks in a single .gpx file

```shell
make
# or
pipenv run ./main.py tracks/whatever-raw.gpx 
```


## Viewing .gpx files

[gpx.studio](https://gpx.studio/) is very helpful to visualise the files.
