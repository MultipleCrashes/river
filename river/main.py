import os
import time
import arrow
import logging
import argparse
from .utils import seconds_until, seconds_since, format_timestamp
from .feed import FeedList, Feed
from .index import Index

logger = logging.getLogger('river')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument('-l', '--min-update', default=15, type=int)
    parser.add_argument('-u', '--max-update', default=60, type=int)
    parser.add_argument('-s', '--strict', action='store_true')
    parser.add_argument('--hours', default=4, type=int)
    parser.add_argument('-r', '--refresh', default=15, type=int)
    parser.add_argument('-o', '--output', default='output')
    parser.add_argument('feeds')
    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.INFO)

    if not os.path.isdir(args.output):
        os.makedirs(args.output)

    Feed.min_update_interval = args.min_update * 60
    Feed.max_update_interval = args.max_update * 60
    Feed.index = Index(args.output, args.strict, args.hours)

    feeds = FeedList(args.feeds)
    active_feed = None

    if os.path.isfile(Feed.json_path(args.output)):
        os.remove(Feed.json_path(args.output))

    try:
        while True:
            if active_feed is not None:
                logger.info('Checking feed: %s' % active_feed.url)
                active_feed.check(args.output)

            if feeds.need_update(args.refresh * 60):
                feeds.update()

            active_feed = feeds.active()

            if not active_feed.initial_check:
                logger.info('Next feed to be checked: %s at %s (%s)' % (
                    active_feed.url, format_timestamp(active_feed.next_check, web=False),
                    seconds_until(active_feed.next_check, readable=True),
                ))

                delay = seconds_until(active_feed.next_check)
                if delay:
                    time.sleep(delay)

                # Once here, all the initial checks have been completed.
                Feed.running = True

    except KeyboardInterrupt:
        print '\nQuitting...'
