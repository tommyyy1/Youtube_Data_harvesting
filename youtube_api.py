#first install all necessary libraries: pip install streamlit google-api-python-client pandas sqlalchemy pymysql

#create a file to handle youtube API interactions. 

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#First I created and enable API and services (youtube Data API V3-google cloud console) and most of the code able to get from https://developers.google.com/youtube/v3/docs; Reference-->channels,playlists, videos 
    

def get_youtube_client(api_key):
    return build('youtube', 'v3', developerKey=api_key)

    try:
        channel_response = youtube.channels().list(
            part='snippet,statistics,contentDetails',
            id=channel_id
        ).execute()

        if 'items' in channel_response and len(channel_response['items']) > 0:
            channel = channel_response['items'][0]
            return {
                'channel_id': channel_id,
                'channel_name': channel['snippet']['title'],
                'subscribers': channel['statistics'].get('subscriberCount', 0),
                'total_videos': channel['statistics'].get('videoCount', 0),
                'playlist_id': channel['contentDetails']['relatedPlaylists']['uploads']
            }
        else:
            print(f"No channel found for ID: {channel_id}")
            return None
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return None

def get_video_data(youtube, playlist_id):
    videos = []
    next_page_token = None

    while True:
        try:
            playlist_response = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=5,# Initally, I had a trouble in using popular channels because easily I reached daily quota not able to extract much data from 10 channels, so I kept max:5 and created multiple API keys
                pageToken=next_page_token
            ).execute()

            for item in playlist_response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                video_response = youtube.videos().list(
                    part='statistics',
                    id=video_id
                ).execute()

                if 'items' in video_response:
                    video_stats = video_response['items'][0]['statistics']
                    videos.append({
                        'video_id': video_id,
                        'likes': video_stats.get('likeCount', 0),
                        'dislikes': video_stats.get('dislikeCount', 0),#youtube doesn't have dislike anymore
                        'comments': video_stats.get('commentCount', 0)
                    })

            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token:
                break
        except HttpError as e:
            print(f"An error occurred: {e}")
            break

    return videos

 #Main function to execute the script
def main():
    # Input your YouTube API key here
    api_key = 'your_API_Key'
    # List of YouTube channel IDs
    channel_ids = []# Add up to 10 channel IDs
    

    # Get YouTube data
    youtube_data = get_youtube_data(channel_ids, api_key)

    # Store data in a CSV file
    output_file = 'youtube_channel_data.csv'
    youtube_data.to_csv(output_file, index=False)
    print(f'Data collected and saved to {output_file}')

if __name__ == '__main__':
    main()

#Above function was executed mainly for data cleaning purposes. I decided to store the data in .csv format, so I am able to see data shape, describe, info, and see if any "na" is required in collected data. AFter that, i removed the execute function and create a streamapp code
