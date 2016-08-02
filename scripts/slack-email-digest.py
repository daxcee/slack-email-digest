#!/usr/bin/env python3
"""
Usage: slack-email-digest.py [options]

Options:
    -t --token=<token>       Slack API token to use (required)
    -c --channel=<name>      Channel to export. [default: general]
    -s --start-ts=<ts>       UTC timestamp of the first message to include.
                             Defaults to the start of yesterday in the local timezone.
    -e --end-ts=<ts>         UTC timestamp of the last message to include.
                             Defaults to 1 day after --start-ts.
    -o --out-file=<file>     Filename to output. [default: digest.html]
    -v --verbose             Whether to provide verbose output
"""

import datetime
import sys
import time

from docopt import docopt
import pytz
import tzlocal

from slack_email_digest import SlackScraper, HTMLRenderer


def from_timestamp(ts):
    return datetime.datetime.utcfromtimestamp(ts).replace(tzinfo=pytz.utc).astimezone(tzlocal.get_localzone())


def main():
    args = docopt(__doc__)

    # process args

    if args['--start-ts']:
        start_ts = args['--start-ts']
    else:
        yest = (from_timestamp(time.time()) - datetime.timedelta(days=1))
        yest = yest.replace(hour=0, minute=0, second=0, microsecond=0)
        start_ts = yest.timestamp()

    if args['--end-ts']:
        end_ts = args['--end-ts']
    else:
        end_ts = (from_timestamp(start_ts) + datetime.timedelta(days=1)).timestamp()

    token = args['--token']
    if not token:
        sys.exit("Must provide --token")

    verbose = args['--verbose']
    out_file = args['--out-file']

    # scrape

    print("Getting messages from %s to %s " % (
        from_timestamp(start_ts),
        from_timestamp(end_ts),
    ), file=sys.stderr)

    scraper = SlackScraper(token, verbose=verbose)
    hist = scraper.get_channel_history(
        args['--channel'],
        oldest=start_ts, latest=end_ts)

    hist.sort(key=lambda msg: float(msg['ts']))

    # render

    renderer = HTMLRenderer(scraper)
    # render as ascii with xmlcharrefreplace, so don't have to deal with encoding
    with open(out_file, 'wb') as f:
        f.write(renderer.render_messages(hist).encode('ascii', errors='xmlcharrefreplace'))


if __name__ == '__main__':
    main()