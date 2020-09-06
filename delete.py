import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from time import sleep
import tweepy

from secrets import *


def confirm_ready(end_date):
    confirm = input("Delete tweets older than {}? [y/n] ".format(
        end_date.strftime("%B %-d, %Y")
    ))
    if confirm.lower() != 'y':
        return False
    keys = [API_KEY, API_KEY_SECRET, ACCESS_TOKEN_KEY, ACCESS_TOKEN_KEY]
    if any([len(k) == 0 for k in keys]):
        print("Missing key in secrets.py file. Did you copy your API keys and access"
              "tokens to this file?")
        return False
    if not os.path.isfile("tweet.js"):
        print("Missing tweet.js file. Did you copy it over from"
              " [unzipped_twitter_archive_folder]/data/tweet.js?")
        return False
    return True


def get_tweets():
    with open("tweet.js", "r", encoding="utf-8") as tweet_file:
        tweets = tweet_file.read()
    array_start = tweets.find("[")
    try:
        return json.loads(tweets[array_start:])
    except json.JSONDecodeError as e:
        print("Couldn't read tweets. Something may be wrong with the tweet.js file.")
        return None


def delete_tweets(tweets, end_date):
    auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
    auth.set_access_token(ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    last_deleted = None
    localized_end_date = end_date.replace(tzinfo=timezone.utc)
    for tweet in tweets:
        tweet_date = datetime.strptime(
            tweet['tweet']['created_at'],
            "%a %b %d %H:%M:%S %z %Y"
        )
        if tweet_date < localized_end_date:
            if last_deleted and \
                    datetime.now(timezone.utc) - last_deleted < timedelta(seconds=1):
                sleep(1)
            print("Deleting tweet from {}: {}".format(
                tweet_date.strftime("%Y-%m-%d"), tweet['tweet']['full_text'])
            )
            try:
                api.destroy_status(tweet['tweet']['id'])
                last_deleted = datetime.now(timezone.utc)
            except tweepy.TweepError as e:
                if e.api_code == 144 or e.api_code == 179:
                    pass
                else:
                    raise e


def main(end_date):
    if not confirm_ready(end_date):
        print("Exiting")
        return
    tweets = get_tweets()
    if not tweets:
        return
    delete_tweets(tweets, end_date)


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Delete tweets older than a specified date.')
    parser.add_argument('-d', dest="date", required=True,
                        help="Delete tweets older than this date (YYYY-MM-DD)",
                        type=parse_date)
    args = parser.parse_args()
    main(args.date)
