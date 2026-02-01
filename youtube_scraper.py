import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


#TODO check for the security
#OAuth 
credentials= None
client_secret='client_secret.json'

#if creds are stored
if os.path.exists("token.pickle"):
    print('Getting credentials from the file...')
    with open("token.pickle", "rb") as token:
        credentials = pickle.load(token)

#pickle save 
if not credentials or not credentials.valid :
    if credentials and credentials.expired and credentials.refresh_token:
        print('Refreshing access token...')
        credentials.refresh(Request())
    else:
        print('Fetching new tokens...')
        flow = InstalledAppFlow.from_client_secrets_file(client_secret, 
                                                 scopes=['https://www.googleapis.com/auth/youtube'])
        flow.run_local_server(port=8080, prompt='consent', authorization_prompt_message='')
        credentials= flow.credentials
        with open("token.pickle", "wb") as file:
            print('save creds for later use')
            pickle.dump(credentials, file)

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

#API CALLS PART 1: go over the init playlist
vids_list=[]
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials= credentials)
def playlist_browse():
  search_response = youtube.playlistItems().list(
    part='status',
    maxResults=10,
    playlistId='xxx'
  ).execute()
  items=search_response['items']
  for r in items:
    vids_list.append(r['snippet']['resourceId']['videoId'])

  return items

#playlist_browse()

#API CALL PART 2: create the new playlists
def playlist_create():
    create_response = youtube.playlists().insert(
        part='snippet, status',
        body={'snippet':{
                'title': 'Test',
                'description': 'test the description',
                },
              'status':{
                  'privacyStatus': 'private',
              }
            }
        ).execute()
    print(create_response)
#playlist_create()

#API CALL PART 3: insert the videos in the correct playlists
def playlist_add():
    add_response = youtube.playlistItems().insert(
        part='snippet',
        body={'snippet':{
                'playlistId': 'xxx',
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': 'xxx'
                }
        }}
    ).execute()
    print(add_response)
#playlist_add()
#CLASSIFICATION PART
categories = ["litterature", "network", "cinema", "music", "philosophy",
              "commentary", "lord of the ring", "diy", "tips", "politics",
              "economy", "computer science", "physics", "mathematics", "makeup",
              "vlog", "storytime", "cooking", "programming", "conferences"]
