import tweepy
import json
from datetime import datetime
from calendar import monthrange
import time
import schedule


class TweepyController:
    def __init__(self):
        self.user_keys_file = 'user_keys.txt'
        self.app_keys_file = 'app_keys.txt'
        with open(self.user_keys_file) as json_file:
            user_data = json.load(json_file)
        with open(self.app_keys_file) as json_file2:
            app_data = json.load(json_file2)
        self.api_key = app_data["api_key"]
        self.api_key_secret = app_data["api_key_secret"]
        self.bearer_token = app_data["bearer_token"]
        self.access_token = [user["access_token"] for user in user_data]
        self.access_token_secret = [user["access_token_secret"] for user in user_data]
        self.api = self.initialize_api()
        self.auth = None

    def initialize_api(self, account_number=0):
        self.auth = tweepy.OAuthHandler(self.api_key, self.api_key_secret)
        self.auth.set_access_token(self.access_token[account_number], self.access_token_secret[account_number])
        api = tweepy.API(self.auth)
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

    def get_auth_url(self):
        # This function needs to be executed manually, because requires human interaction
        # Running it will give you a link that must be used on a browser with the twitter account whose tokens you want
        # to obtain, then after accepting authorization, it will give you a serial number which must be typed in the
        # console, after that if no error is found, you will get on the console the access and the secret access tokens
        try:
            redirect_url = self.auth.get_authorization_url()
            print(redirect_url)
            verifier = input('Verifier:')
            try:
                self.auth.get_access_token(verifier)
                api = tweepy.API(self.auth)
                self.validate_api(api)
                user_info = api.get_settings()
                new_user_keys = {
                    "access_token": self.auth.access_token,
                    "access_token_secret": self.auth.access_token_secret,
                    "name_account": user_info["screen_name"]
                }

                with open(self.user_keys_file) as json_file:
                    user_data = json.load(json_file)

                user_in_txt_already = False
                for user in user_data:
                    if user == new_user_keys:
                        user_in_txt_already = True
                if not user_in_txt_already:
                    user_data.append(new_user_keys)
                    json_object = json.dumps(user_data, indent=4)
                    with open(self.user_keys_file, 'w') as outfile:
                        outfile.write(json_object)

            except tweepy.TweepError:
                print("Error! Failed to get access token.")
        except tweepy.TweepError:
            print("Error! Failed to get request token.")


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


tweeterbot_object = TweepyController()
tweeterbot_object.get_auth_url()
