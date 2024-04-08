.PHONY: import
raw_tracks = $(wildcard tracks/*-raw.gpx)
best_tracks = $(raw_tracks:%-raw.gpx=%-best.gpx)

tracks/%-best.gpx: tracks/%-raw.gpx
	pipenv run ./main.py $?

all: $(best_tracks)

import:
	pipenv run ./main.py --import

clean:
	rm -rf tracks/*-best.gpx tracks/*-all.gpx