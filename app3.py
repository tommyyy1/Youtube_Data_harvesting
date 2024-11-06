#creating a streamlit app, installed all necessary libraries. 

import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
from youtube_api import get_youtube_client, get_channel_data, get_video_data

# Initialize session state
if 'channels' not in st.session_state:
    st.session_state.channels = []

# Enter your YouTube API key directly here
api_key = "your_API_Key"
youtube = get_youtube_client(api_key)


# Replace these with your actual database connection details
db_username = "your username"
db_password = "yourpassword"
db_host = "yourhost"
db_port = "xxxx"
db_name = "youtube_analyzer"

# Construct the connection string
db_connection_string = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create the SQLAlchemy engine
engine = create_engine(db_connection_string)

st.title("YouTube Channel Analyzer")

# Input for channel ID and retrieve relevant data
channel_id = st.text_input("Enter YouTube Channel ID")

if st.button("Fetch Channel Data"):
    channel_data = get_channel_data(youtube, channel_id)
    if channel_data:
        video_data = get_video_data(youtube, channel_data['playlist_id'])
        channel_data['videos'] = video_data
        channel_data['channel_id'] = channel_id  # Store the actual channel ID
        st.session_state.channels.append(channel_data)
        st.success(f"Data fetched for channel: {channel_data['channel_name']}")
    else:
        st.error("Failed to fetch channel data. Please check the channel ID.")

# Display fetched channels
st.subheader("Fetched Channels")
for idx, channel in enumerate(st.session_state.channels):
    st.write(f"{idx + 1}. {channel['channel_name']} (ID: {channel['channel_id']})")

# Button to store data in SQL database
if st.button("Store Data in Database"):
    for channel in st.session_state.channels:
        # Store channel data
        channel_df = pd.DataFrame([{
            'channel_id': channel['channel_id'],
            'channel_name': channel['channel_name'],
            'subscribers': channel['subscribers'],
            'total_videos': channel['total_videos']
        }])
        channel_df.to_sql('channels', engine, if_exists='append', index=False)

        # Store video data
        video_df = pd.DataFrame(channel['videos'])
        video_df['channel_id'] = channel['channel_id']
        video_df.to_sql('videos', engine, if_exists='append', index=False)

    st.success("Data stored in the database successfully!")

# Search functionality
st.subheader("Search Database")
search_option = st.selectbox("Select search option", ["Channel Details", "Video Details"])

if search_option == "Channel Details":
    channel_search = st.text_input("Enter channel ID or name")
    if st.button("Search"):
        query = """SELECT * FROM channels WHERE channel_id = %s OR channel_name LIKE %s"""
        result = pd.read_sql(query, engine, params=(channel_search, f"%{channel_search}%"))
        st.dataframe(result)

elif search_option == "Video Details":
    channel_search = st.text_input("Enter channel ID or name")
    if st.button("Search"):
        query = """SELECT v.*, c.channel_name, c.subscribers, c.total_videos
        FROM videos v
        JOIN channels c ON v.channel_id = c.channel_id
        WHERE v.channel_id = %s OR c.channel_name LIKE %s
        """
        result = pd.read_sql(query, engine, params=(channel_search, f"%{channel_search}%"))
        st.dataframe(result)

# Add these visualizations in appropriate sections of your app
st.title("YouTube Channel Analytics Dashboard")
st.header("Channel Statistics")

#Fetch data from sql
def get_channel_data():
    return pd.read_sql("SELECT * FROM channels", engine)

@st.cache_data
def get_video_data():
    return pd.read_sql("SELECT * FROM videos", engine)

# Fetch data
channel_data = get_channel_data()
video_data = get_video_data()

# Convert numeric columns to appropriate types
numeric_columns = ['subscribers', 'total_videos', 'likes', 'comments']
for col in numeric_columns:
    if col in channel_data.columns:
        channel_data[col] = pd.to_numeric(channel_data[col], errors='coerce')
    if col in video_data.columns:
        video_data[col] = pd.to_numeric(video_data[col], errors='coerce')


#Barchart for subscribers
def plot_subscribers_bar_chart():
    fig = px.bar(channel_data, x='channel_name', y='subscribers', title='Subscribers by Channel')
    st.plotly_chart(fig)
#scatter plot for likes Vs comments
def plot_likes_vs_comments():
    fig = px.scatter(video_data, x='likes', y='comments', color='channel_id',
                     title='Likes vs. Comments per Video')
    st.plotly_chart(fig)
#box plot for engagement distribution

def plot_engagement_distribution():
    numeric_video_data = video_data[['channel_id', 'likes', 'comments']]
    fig = px.box(numeric_video_data, x='channel_id', y=['likes', 'comments'],
                 title='Engagement Distribution by Channel')
    st.plotly_chart(fig)

#channel metrics
def plot_channel_metrics():
    channel_metrics = video_data.groupby('channel_id').agg({
        'video_id': 'count',
        'likes': 'sum',
        'comments': 'sum'
    }).reset_index()
    channel_metrics = channel_metrics.merge(channel_data[['channel_id', 'channel_name']], on='channel_id')
    
    fig = px.bar(channel_metrics, x='channel_name', 
                 y=['video_id', 'likes', 'comments'],
                 title='Channel Metrics Comparison',
                 labels={'value': 'Count', 'variable': 'Metric'})
    st.plotly_chart(fig)

# Pie chart for video distribution across channels
def plot_video_distribution():
    video_counts = video_data.groupby('channel_id')['video_id'].count().reset_index(name='video_count')
    video_counts = video_counts.merge(channel_data[['channel_id', 'channel_name']], on='channel_id')
    fig = px.pie(video_counts, values='video_count', names='channel_name',
                 title='Video Distribution Across Channels')
    st.plotly_chart(fig)
    
# Main Streamlit app
st.title("YouTube Channel Analytics Dashboard")

st.header("Channel Statistics")

plot_subscribers_bar_chart()
plot_channel_metrics()
plot_likes_vs_comments()
plot_video_distribution()
plot_engagement_distribution()



#During writing this code, I faced numerous issues storing the data in Mysql and displaying search options. I did use internet to seek help for adding, storing, reteriving and searching relavent data from the database using streamlit app creation. 
