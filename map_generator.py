import staticmap

__SPEED_BUCKET_COLORS = ['#fffafa', '#ffebeb', '#ffdbdb', '#ffcccc', '#ffbdbd', '#ffadad', '#ff9e9e',
                         '#ff8f8f', '#ff8080', '#ff7070', '#ff6161', '#ff5252', '#ff4242', '#ff3333',
                         '#ff2424', '#ff1414', '#ff0f0f', '#ff0a0a', ]
__SPEED_BUCKETS = [10 + i for i in range(len(__SPEED_BUCKET_COLORS))]


def save_png(fn, run):
    m = staticmap.StaticMap(1024, 1024, 1, 1)
    for i in range(len(run.gpx_segment.points) - 1):
        first = run.gpx_segment.points[i]
        second = run.gpx_segment.points[i + 1]
        if second.speed > __SPEED_BUCKETS[-1]:
            color = __SPEED_BUCKET_COLORS[-1]
        else:
            color = None
            for i, limit in enumerate(__SPEED_BUCKETS):
                if second.speed < limit:
                    break
                color = __SPEED_BUCKET_COLORS[i]
        m.add_line(
            staticmap.Line([[first.longitude, first.latitude], [second.longitude, second.latitude]], color, 2, True))
    m.render().save(fn)
