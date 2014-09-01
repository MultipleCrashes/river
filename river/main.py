import os
import time
import arrow
import logging
import argparse
from .utils import seconds_until, seconds_since, format_timestamp
from .feed import FeedList, Feed

logger = logging.getLogger('river')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument('--min-interval', default=15, type=int)
    parser.add_argument('-c', '--max-interval', default=60, type=int)
    parser.add_argument('-r', '--refresh', default=15, type=int)
    parser.add_argument('-o', '--output', default='output')
    parser.add_argument('--skip-initial', action='store_true', default=False)
    parser.add_argument('feeds')
    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.INFO)

    if not os.path.isdir(args.output):
        os.makedirs(args.output)

    Feed.min_update_interval = args.min_interval * 60
    Feed.max_update_interval = args.max_interval * 60

    feeds = FeedList(args.feeds)
    active_feed = None

    json_exists = os.path.isfile(Feed.json_path(args.output))
    if json_exists:
        logger.debug('Found existing JSON file for today, skipping initial updates')

    try:
        while True:
            if active_feed is not None:
                logger.info('Checking feed: %s' % active_feed.url)
                active_feed.check(args.output, args.skip_initial, json_exists)

            if feeds.need_update(args.refresh * 60):
                feeds.update()

            active_feed = feeds.active()

            if not active_feed.initial_check:
                logger.info('Next feed to be checked: %s at %s (%s)' % (
                    active_feed.url, format_timestamp(active_feed.next_check),
                    seconds_until(active_feed.next_check, readable=True),
                ))

                delay = seconds_until(active_feed.next_check)
                if delay:
                    time.sleep(delay)

    except KeyboardInterrupt:
        print '\nQuitting...'
