'''
Monitors a Twitter account and returns any tweets made to the callback.
@author: Tobias Carryer
'''

from json import loads
from Queue import Empty, Queue
from threading import Thread, Event
import tweepy
from tweepy import Stream, StreamListener

# The maximum time in seconds that a worker will wait for a new task on the queue.
QUEUE_TIMEOUT_S = 1

# The number of retries to attempt when an error occurs.
API_RETRY_COUNT = 60

# The number of seconds to wait between retries.
API_RETRY_DELAY_S = 1

# The HTTP status codes for which to retry.
API_RETRY_ERRORS = [400, 401, 500, 502, 503, 504]
                
class TwitterListener(StreamListener):
    """A listener class for handling streaming Twitter data."""

    def __init__(self, user_id, callback):
        self.user_id = user_id
        self.callback = callback
        self.error_status = None
        self.start_queue()

    def start_queue(self):
        """Creates a queue and starts the worker threads."""

        self.queue = Queue()
        self.stop_event = Event()
        self.worker = Thread(target=self.process_queue)
        self.worker.daemon = True
        self.worker.start()

    def stop_queue(self):
        """Shuts down the queue and worker threads."""

        # Stop the queue.
        if self.queue:
            print("Stopping queue.")
            self.queue.join()
        else:
            print("No queue to stop.")

        # Stop the worker thread
        print("Stopping worker thread.")
        self.stop_event.set()
        self.worker.join()

    def process_queue(self):
        """Continuously processes tasks on the queue."""

        while not self.stop_event.is_set():
            try:
                data = self.queue.get(block=True, timeout=QUEUE_TIMEOUT_S)
                self.handle_data(data)
                self.queue.task_done()
            except Empty:
                # Timed out on an empty queue.
                continue
            except Exception, e:
                # The main loop doesn't catch and report exceptions from
                # background threads, so do that here.
                print(e)
        print("Stopped worker thread.")

    def on_error(self, status):
        """Handles any API errors."""
        
        print("Twitter error: %s" % status)
        self.error_status = status
        self.stop_queue()
        return False

    def get_error_status(self):
        """Returns the API error status, if there was one."""
        return self.error_status

    def on_data(self, data):
        """Puts a task to process the new data on the queue."""

        # Stop streaming if requested.
        if self.stop_event.is_set():
            return False

        # Put the task on the queue and keep streaming.
        self.queue.put(data)
        return True

    def handle_data(self, data):
        """
        Sanity-checks and extracts the data before sending it to the callback.
        """

        try:
            tweet = loads(data)
        except ValueError:
            print("Failed to decode JSON data: %s" % data)
            return

        try:
            user_id_str = tweet["user"]["id_str"]
            screen_name = tweet["user"]["screen_name"]
        except KeyError:
            print("Malformed tweet: %s" % tweet)
            return

        # Skip tweets not from the user being tracked.
        if user_id_str != self.user_id:
            print("Skipping tweet from user: %s (%s)" %
                       (screen_name, user_id_str))
            return

        print("Examining tweet: %s" % tweet)

        # Call the callback.
        self.callback(tweet["text"])
        
class Twitter:
    def __init__(self, consumer_key, consumer_secret, access_token, access_secret):
        self._auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self._auth.set_access_token(access_token, access_secret)
        
    def start_streaming(self, user_id, callback):
        """
        :param user_id: String
        :param callback: method that takes Tweet text (String) as a parameter. 
        Starts streaming tweets and returning data to the callback.
        """

        self.twitter_listener = TwitterListener(user_id, callback=callback)
        twitter_stream = Stream(self._auth, self.twitter_listener)

        print("Starting Twitter stream for account: %s" % user_id)
        twitter_stream.filter(follow=[user_id])

        # If we got here because of an API error, raise it.
        if self.twitter_listener and self.twitter_listener.get_error_status():
            raise Exception("Twitter API error: %s" %
                            self.twitter_listener.get_error_status())

    def stop_streaming(self):
        """Stops the current stream."""

        if not self.twitter_listener:
            print("No stream to stop.")
            return

        print("Stopping stream.")
        self.twitter_listener.stop_queue()
        self.twitter_listener = None