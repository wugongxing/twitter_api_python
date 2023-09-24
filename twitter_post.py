import os
import sys
import time
import json
import requests
from requests_oauthlib import OAuth1
import tweepy

class TweetPost(object):
  MEDIA_ENDPOINT_URL = 'https://upload.twitter.com/1.1/media/upload.json'
  POST_TWEET_URL = 'https://api.twitter.com/1.1/statuses/update.json'

  image_filename = None
  video_filename = None
  media_id = None
  oauth = None

  def __init__(self,API_KEY,API_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET):
    self.oauth = OAuth1(API_KEY, client_secret=API_SECRET, resource_owner_key=ACCESS_TOKEN, resource_owner_secret=ACCESS_TOKEN_SECRET)

  def upload_init(self):
    '''
    Initializes Upload
    '''

    print('INIT')

    request_data = {}
    if self.image_filename != None:
      request_data = {
        'command': 'INIT',
        'media_type': 'image/jpeg',
        'total_bytes': self.total_bytes,
      }
    if self.video_filename != None:
      request_data = {
        'command': 'INIT',
        'media_type': 'video/mp4',
        'total_bytes': self.total_bytes,
        'media_category': 'tweet_video'
      }

    req = requests.post(url=self.MEDIA_ENDPOINT_URL, data=request_data, auth=self.oauth)
    print(req.json())
    media_id = req.json()['media_id']

    self.media_id = media_id

    print('Media ID: %s' % str(media_id))


  def upload_append(self):
    '''
    Uploads media in chunks and appends to chunks uploaded
    '''

    segment_id = 0
    bytes_sent = 0
    file = None
    if self.image_filename != None:
      file = open(self.image_filename, 'rb')
    if self.video_filename != None:
      file = open(self.video_filename, 'rb')

    while bytes_sent < self.total_bytes:
      chunk = file.read(4*1024*1024)
      
      print('APPEND')

      request_data = {
        'command': 'APPEND',
        'media_id': self.media_id,
        'segment_index': segment_id
      }

      files = {
        'media':chunk
      }

      req = requests.post(url=self.MEDIA_ENDPOINT_URL, data=request_data, files=files, auth=self.oauth)

      if req.status_code < 200 or req.status_code > 299:
        print(req.status_code)
        print(req.text)
        sys.exit(0)

      segment_id = segment_id + 1
      bytes_sent = file.tell()

      print('%s of %s bytes uploaded' % (str(bytes_sent), str(self.total_bytes)))

    print('Upload chunks complete.')


  def upload_finalize(self):
    '''
    Finalizes uploads and starts video processing
    '''

    print('FINALIZE')

    request_data = {
      'command': 'FINALIZE',
      'media_id': self.media_id
    }

    req = requests.post(url=self.MEDIA_ENDPOINT_URL, data=request_data, auth=self.oauth)
    print(req.json())

    self.processing_info = req.json().get('processing_info', None)

    check_count = 0
    self.check_status(check_count)


  def check_status(self,check_count):
    '''
    Checks video processing status
    '''

    check_count += 1
    if check_count > 120:
      print("Checked status over 120 times, exiting")
      return

    if self.processing_info is None:
      return

    state = self.processing_info['state']

    print('Media processing status is %s ' % state)

    if state == u'succeeded':
      return

    if state == u'failed':
      sys.exit(0)

    if 'check_after_secs' in self.processing_info:
      check_after_secs = self.processing_info['check_after_secs']
    else:
      check_after_secs = 5 
    
    print('Checking after %s seconds' % str(check_after_secs))
    time.sleep(check_after_secs)

    print('STATUS')

    request_params = {
      'command': 'STATUS',
      'media_id': self.media_id
    }

    req = requests.get(url=self.MEDIA_ENDPOINT_URL, params=request_params, auth=self.oauth)
    
    self.processing_info = req.json().get('processing_info', None)
    self.check_status(check_count)

  def tweet(self,text,pic_file_name=None,video_file_name=None):
    try:
      if pic_file_name != None:
        self.image_filename = pic_file_name #TODO
        self.total_bytes = os.path.getsize(self.image_filename)
      if video_file_name != None:
        self.video_filename = video_file_name 
        self.total_bytes = os.path.getsize(self.video_filename)
      self.media_id = None
      self.processing_info = None

      client = tweepy.Client(
          consumer_key=API_KEY, consumer_secret=API_SECRET, 
          access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
      )

      if (self.image_filename != None) or (self.video_filename != None):
        self.upload_init()
        self.upload_append()
        self.upload_finalize()
        print(self.media_id)
        # return True

      if self.media_id == None:
        response = client.create_tweet(
        text=text
        )
      else:
        response = client.create_tweet(
        text=text,
        media_ids=[self.media_id]
        )

      print(f"https://twitter.com/user/status/{response.data['id']}")
      return True
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return False


if __name__ == '__main__':
  API_KEY = 'API_KEY1111'  #tweety  CONSUMER_KEY
  API_SECRET = 'API_SECRET2222'  #tweety  CONSUMER_SECRET
  ACCESS_TOKEN = 'ACCESS_TOKEN3333'
  ACCESS_TOKEN_SECRET = 'ACCESS_TOKEN_SECRET44444'

  #only text 
  videoTweet1 = TweetPost(API_KEY,API_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET)
  videoTweet1.tweet('hello world,twitter api 2023')

  time.sleep(15)

  #image 
  IMAGE_FILENAME = '/Users/david/Twitter_API_2023/87.jpeg'
  videoTweet1 = TweetPost(API_KEY,API_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET)
  videoTweet1.tweet('Close up shot of a fishing spider S eyelashes',pic_file_name=IMAGE_FILENAME)

  time.sleep(25)

  #video 
  VIDEO_FILENAME = '/Users/david/Twitter_API_2023/7.mp4'
  videoTweet1 = TweetPost(API_KEY,API_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET)
  videoTweet1.tweet('Close encounter of a gorilla beating his chest.',video_file_name=VIDEO_FILENAME)

