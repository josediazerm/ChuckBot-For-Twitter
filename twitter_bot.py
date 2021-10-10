import tweepy
import json
from datetime import datetime
from calendar import monthrange
import time
import schedule


class TweepyController:
    def __init__(self):
        with open('keys.txt') as json_file:
            data = json.load(json_file)
        self.api_key = data["api_key"]
        self.api_key_secret = data["api_key_secret"]
        self.bearer_token = data["bearer_token"]
        self.access_token = data["access_token"]
        self.access_token_secret = data["access_token_secret"]
        self.api = self.initialize_api()

    def initialize_api(self):
        auth = tweepy.OAuthHandler(self.api_key, self.api_key_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        api = tweepy.API(auth)
        self.validate_api(api)
        return api

    @staticmethod
    def validate_api(api):
        try:
            api.verify_credentials()
        except Exception as error:
            assert str(error)

    def tweet_message(self, message):
        self.api.update_status(str(message))


class TweeterBot:
    def __init__(self):
        self.tweepy_object = TweepyController()
        self.sentence_indicator = 0
        self.sentences = None
        self.text_file = 'frases.txt'

    @staticmethod
    def get_seconds_between_dates(future_date):
        # TODO asumo que siempre es el mismo año por mi salud mental actual
        # TODO Cuando esto funcione bien arreglar
        actual_date = datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M:%S")
        future_date_dict = datetime.strptime(future_date, "%d/%m/%Y %H:%M:%S")
        actual_date_dict = datetime.strptime(actual_date, "%d/%m/%Y %H:%M:%S")
        months = future_date_dict.month - actual_date_dict.month
        if months == 0:
            days = future_date_dict.day - actual_date_dict.day
        else:
            days = 0
            month = actual_date_dict.month
            while months > 1:
                month += 1
                days += monthrange(actual_date_dict.year, month)[1]
                months -= 1
            days += future_date_dict.day + \
                    (monthrange(actual_date_dict.year, actual_date_dict.month)[1] - actual_date_dict.day)

        hour = future_date_dict.hour - actual_date_dict.hour
        minute = future_date_dict.minute - actual_date_dict.minute
        second = future_date_dict.second - actual_date_dict.second
        seconds_difference = days * 24 * 3600 + hour * 3600 + minute * 60 + second

        return seconds_difference

    @staticmethod
    def get_date_format_from_sentence(sentence):
        return f"{sentence['date']} {sentence['hour']}:{sentence['minute']}:{sentence['second']}"

    def add_tweets_to_queue(self):
        self.tweepy_object.tweet_message(self.sentences[self.sentence_indicator]["message"])
        self.sentence_indicator += 1
        return schedule.CancelJob

    def main(self):
        with open(self.text_file) as json_file:
            self.sentences = json.load(json_file)

        for sentence in self.sentences:
            date_time = self.get_date_format_from_sentence(sentence)
            schedule.every(
                self.get_seconds_between_dates(date_time)).seconds.do(
                self.add_tweets_to_queue)

        while len(schedule.get_jobs()) > 0:
            schedule.run_pending()
            time.sleep(1)


tweeterbot_object = TweeterBot()
tweeterbot_object.main()
