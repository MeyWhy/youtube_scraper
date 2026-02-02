import json
import os
import pickle
import csv
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
vids_list=[]
categories_dict={}

#retrieve video ids from wl playlist
with open('Vidéos de Watch later.csv', 'r', encoding='utf-8-sig') as f:
    reader=csv.DictReader(f, delimiter=';')
    for row in reader:
        vids_list.append(row['videoId'])

#retrieve category ids
with open('categories.json', 'r', encoding='utf-8')as f:
    data=json.load(f)
for item in data["items"]:
    categories_dict[item["id"]]= item["snippet"]["title"]
    

#API CALLS PART 1: get info about all vids
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials= credentials)
def playlist_browse():      
    batch_size=50
    vids=[]
    for i in range(0, len(vids_list), batch_size):
        batch_ids=vids_list[i:i+batch_size]
        if not batch_ids:
            continue
        search_response = youtube.videos().list(
            part='snippet, topicDetails, contentDetails',
            id=','.join(batch_ids)
        ).execute()

        details=search_response.get('items', [])
       
        for d in details: 
            vid_cat=d['snippet']['categoryId']
            vid_id=d['id']
            vids.append((vid_id, vid_cat))

    return vids

def video_category_correspondance(vid_id, vid_cat):
    category_name=categories_dict.get(vid_cat)
    return (vid_id, category_name)

#API CALL PART 2: create the new playlists
def playlist_create(category_name):
    create_response = youtube.playlists().insert(
        part='snippet, status',
        body={'snippet':{
                'title': category_name, 
                'description': f'description of playlist for {category_name}', 
                },
              'status':{
                  'privacyStatus': 'private',
              }
            }
        ).execute()
    return create_response['id']


#API CALL PART 3: insert the videos in the correct playlists
def playlist_add(playlist_id, video_id):
    add_response = youtube.playlistItems().insert(
        part='snippet',
        body={'snippet':{
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id 
                }
        }}
    ).execute()
    return add_response

#Call for all the funcs
video_corresponding=[video_category_correspondance(vid_id, vid_cat)
              for vid_id, vid_cat in playlist_browse()]

playlist_ids={}
for _, cat_name in video_corresponding:
    if cat_name is None:
        print("skip. unknown category for the video")
        continue
    if cat_name not in playlist_ids:
        playlist_ids[cat_name]=playlist_create(category_name=cat_name)


with open('Vidéos de Watch later.csv', 'r', encoding='utf-8-sig') as f:
    reader= csv.DictReader(f, delimiter=';')
    rows=list(reader)

for vid_id, cat_name in video_corresponding:
    playlist_id = playlist_ids.get(cat_name)
    if playlist_id:
        playlist_add(playlist_id=playlist_id, video_id=vid_id)
        
        rows=[row for row in rows if row['videoId']!=vid_id]

        with open('Vidéos de Watch later.csv', 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(rows)

print("all videos processed and removed from csv")
