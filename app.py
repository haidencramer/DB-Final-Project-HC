import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import base64

# ------- MY IMPORTS FOR VISUALIZATIONS -------
import networkx as nx
from pyvis.network import Network
import plotly.express as px
import plotly.graph_objects as go
# ----------------------------------------------


st.set_page_config(page_title=" AUDIOPLANE", page_icon="./assets/img/audioplaneWindowIcon.png", layout="wide")
load_dotenv()

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGSSLMODE = os.getenv("PGSSLMODE", "require")

if not all([PGDATABASE, PGUSER, PGPASSWORD]):
    st.error("Missing DB credentials. Please set PGDATABASE, PGUSER, and PGPASSWORD in your .env file.")
    st.stop()

def make_url() -> URL:
    return URL.create(
        "postgresql+psycopg2",
        username=PGUSER,
        password=PGPASSWORD,
        host=PGHOST,
        port=int(PGPORT),
        database=PGDATABASE,
        query={
            "connect_timeout": "5",
            "sslmode": PGSSLMODE
        },
    )

@st.cache_resource
def get_engine():
    engine = create_engine(
        make_url(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=0,
        pool_timeout=5,
        pool_recycle=1800,
    )

    @event.listens_for(engine, "connect")
    def _set_statement_timeout(dbapi_connection, connection_record):
        with dbapi_connection.cursor() as cur:
            cur.execute("SET statement_timeout TO 8000")
            cur.execute(f"SET search_path TO {PGUSER}, public")

    return engine

engine = get_engine()

def fetch_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})
    except Exception as e:
        st.error(f"DB error: {e}")
        return pd.DataFrame()

# This was such a pain to figure out because my logo I made is an SVG file so i had to convert it to base64 in order to get it to work properly and hover like I wanted.
#I had no trouble when i used st.image with the svg but getting the hover effect I needed to do it this way but it was fun learning this!
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
# --- File Path to my Logo
image_file_path = "assets/img/AudioplaneLogo.svg" 
try:
    base64_img = get_base64_image(image_file_path)
except FileNotFoundError:
    st.error(f"Image not found at: {image_file_path}. Please check your path.")
    base64_img = "" 

html_content = f"""
<style>
  @keyframes float {{
    0% {{ transform: translateY(5px); }}
    50% {{ transform: translateY(-5px); }}
    100% {{ transform: translateY(5px); }}
  }}
  .float-image {{
    width: 1500px;
    animation-name: float;
    animation-duration: 3s;
    animation-timing-function: ease-in-out;
    animation-iteration-count: infinite;
    display: block; 
    margin: 0 auto;
  }}
</style>

<img src="data:image/svg+xml;base64,{base64_img}" alt="Audioplane" class="float-image">
"""

# Injects my html for the logo to hover into this app 
if base64_img:
    st.markdown(html_content, unsafe_allow_html=True)

st.title("Welcome to the World of Audioplane")
st.caption("Your personal music database viewer")

with st.sidebar:
    st.header("Options")
    row_limit = st.number_input("Row limit", min_value=1, max_value=2000, value=200, step=50)
    st.markdown("---")
    st.caption("Night Hawk Edition")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "👤 Users",
    "🎵 Songs",
    "💿 Albums",
    "🎤 Artists",
    "📋 Playlists",
    "🔗 Relationships",

])

# ---------------- Tab 1: Users ----------------
with tab1:
    st.subheader("👤 Users")
    sql = "SELECT * FROM User_table ORDER BY userID LIMIT :lim"
    df = fetch_df(sql, {"lim": int(row_limit)})
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        st.metric("Total Users", len(df))

# ---------------- Tab 2: Songs ----------------
with tab2:
    st.subheader("🎵 Songs")

    col1, col2 = st.columns(2)
    # Displays all of the songs currently within my database
    with col1:
        st.markdown("#### All Songs")
        sql = "SELECT * FROM Song ORDER BY song_id LIMIT :lim"
        df = fetch_df(sql, {"lim": int(row_limit)})
        st.dataframe(df, use_container_width=True)
    # Display Songs along with the artist who created them
    with col2:
        st.markdown("#### Songs and Who Created Them")
        sql = """
            SELECT s.song_id, s.songName, s.dayReleased, a.artist_name
            FROM Song s
            JOIN Produces p ON s.song_id = p.song_id
            JOIN Artist a ON p.artistID = a.artistID
            ORDER BY s.song_id
            LIMIT :lim
        """
        df2 = fetch_df(sql, {"lim": int(row_limit)})
        st.dataframe(df2, use_container_width=True)

    if not df.empty:
        st.metric("Total Songs", len(df))

# ---------------- Tab 3: Albums ----------------
with tab3:
    st.subheader("💿 Albums")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### All Albums")
        sql = "SELECT * FROM Album ORDER BY albumID LIMIT :lim"
        df = fetch_df(sql, {"lim": int(row_limit)})
        st.dataframe(df, use_container_width=True)

    with col2:
        st.markdown("#### Albums with Artists")
        sql = """
            SELECT al.albumID, al.album_name, al.release_date, ar.artist_name
            FROM Album al
            JOIN Records r ON al.albumID = r.albumID
            JOIN Artist ar ON r.artistID = ar.artistID
            ORDER BY al.release_date DESC
            LIMIT :lim
        """
        df2 = fetch_df(sql, {"lim": int(row_limit)})
        st.dataframe(df2, use_container_width=True)

    if not df.empty:
        st.metric("Total Albums", len(df))

# ---------------- Tab 4: Artists ----------------
with tab4:
    st.subheader("🎤 Artists")
    sql = "SELECT * FROM Artist ORDER BY artistID LIMIT :lim"
    df = fetch_df(sql, {"lim": int(row_limit)})
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        st.metric("Total Artists", len(df))

        st.markdown("#### Artist Song Counts")
        sql2 = """
            SELECT a.artist_name, COUNT(p.song_id) as song_count
            FROM Artist a
            LEFT JOIN Produces p ON a.artistID = p.artistID
            GROUP BY a.artistID, a.artist_name
            ORDER BY song_count DESC
            LIMIT :lim
        """
        df2 = fetch_df(sql2, {"lim": int(row_limit)})
        st.dataframe(df2, use_container_width=True)

# ---------------- Tab 5: Playlists ----------------
with tab5:
    st.subheader("📋 Playlists")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### All Playlists")
        sql = "SELECT * FROM Playlist ORDER BY playlistID LIMIT :lim"
        df = fetch_df(sql, {"lim": int(row_limit)})
        st.dataframe(df, use_container_width=True)

    with col2:
        st.markdown("#### Playlists with Creators")
        sql = """
            SELECT p.playlistID, p.playlist_name, p.num_songs, u.userName as creator
            FROM Playlist p
            JOIN Creates c ON p.playlistID = c.playlistID
            JOIN User_table u ON c.userID = u.userID
            ORDER BY p.playlistID
            LIMIT :lim
        """
        df2 = fetch_df(sql, {"lim": int(row_limit)})
        st.dataframe(df2, use_container_width=True)

    if not df.empty:
        st.metric("Total Playlists", len(df))

    st.markdown("#### Playlist Contents")
    playlists_sql = "SELECT playlistID, playlist_name FROM Playlist ORDER BY playlistID"
    playlists = fetch_df(playlists_sql)

    if not playlists.empty:
        selected_playlist = st.selectbox(
            "Select a playlist to view songs:",
            options=playlists['playlistid'].tolist(),
            format_func=lambda x: playlists[playlists['playlistid']==x]['playlist_name'].iloc[0]
        )

        sql3 = """
            SELECT s.songName, a.artist_name, sv.position
            FROM Saves sv
            JOIN Song s ON sv.song_id = s.song_id
            JOIN Produces p ON s.song_id = p.song_id
            JOIN Artist a ON p.artistID = a.artistID
            WHERE sv.playlistID = :pid
            ORDER BY sv.position
        """
        playlist_songs = fetch_df(sql3, {"pid": int(selected_playlist)})
        st.dataframe(playlist_songs, use_container_width=True)

# ---------------- Tab 6: Relationship Views ----------------
with tab6:
    st.subheader("🔗 Relationship Views")

    view_choice = st.radio(
        "Choose a view:",
        ["User Likes", "Album Tracks", "Most Liked Songs", "User Activity"]
    )

    if view_choice == "User Likes":
        sql = """
            SELECT u.userName, s.songName, a.artist_name, l.liked_date
            FROM Likes l
            JOIN User_table u ON l.userID = u.userID
            JOIN Song s ON l.song_id = s.song_id
            JOIN Produces p ON s.song_id = p.song_id
            JOIN Artist a ON p.artistID = a.artistID
            ORDER BY l.liked_date DESC
            LIMIT :lim
        """
        st.dataframe(fetch_df(sql, {"lim": int(row_limit)}), use_container_width=True)

    elif view_choice == "Album Tracks":
        sql = """
            SELECT al.album_name, s.songName, c.track_number, ar.artist_name
            FROM Contains c
            JOIN Album al ON c.albumID = al.albumID
            JOIN Song s ON c.song_id = s.song_id
            JOIN Records r ON al.albumID = r.albumID
            JOIN Artist ar ON r.artistID = ar.artistID
            ORDER BY al.album_name, c.track_number
            LIMIT :lim
        """
        st.dataframe(fetch_df(sql, {"lim": int(row_limit)}), use_container_width=True)

    elif view_choice == "Most Liked Songs":
        sql = """
            SELECT s.songName, a.artist_name, COUNT(l.userID) as like_count
            FROM Song s
            JOIN Produces p ON s.song_id = p.song_id
            JOIN Artist a ON p.artistID = a.artistID
            LEFT JOIN Likes l ON s.song_id = l.song_id
            GROUP BY s.song_id, s.songName, a.artist_name
            ORDER BY like_count DESC
            LIMIT :lim
        """
        st.dataframe(fetch_df(sql, {"lim": int(row_limit)}), use_container_width=True)

    elif view_choice == "User Activity":
        sql = """
            SELECT 
                u.userName,
                COUNT(DISTINCT l.song_id) as songs_liked,
                COUNT(DISTINCT c.playlistID) as playlists_created
            FROM User_table u
            LEFT JOIN Likes l ON u.userID = l.userID
            LEFT JOIN Creates c ON u.userID = c.userID
            GROUP BY u.userID, u.userName
            ORDER BY songs_liked DESC
            LIMIT :lim
        """
        st.dataframe(fetch_df(sql, {"lim": int(row_limit)}), use_container_width=True)


st.header("Some Cool Visualizations You Should Check Out!")

# -------------------- Network Graph --------------------

st.markdown("### User-Song Network")
st.caption("Interactive visualization showing which users like which songs. Hover over songs to see the artist!")

# Legend
st.markdown("""
<div style="background-color: #2d2d2d; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
    <h4 style="margin-top: 0;">Legend:</h4>
    <div style="display: flex; gap: 30px; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 20px; height: 20px; background-color: #0CECA1; border-radius: 50%;"></div>
            <span>Users</span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 20px; height: 20px; background-color: #8980DF; border-radius: 50%;"></div>
            <span>Songs (hover to see artist)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 40px; height: 2px; background-color: #999;"></div>
            <span>Connection (user likes song)</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

sql = """
    SELECT u.userName, s.songName, a.artist_name
    FROM Likes l
    JOIN User_table u ON l.userID = u.userID
    JOIN Song s ON l.song_id = s.song_id
    JOIN Produces p ON s.song_id = p.song_id
    JOIN Artist a ON p.artistID = a.artistID
    LIMIT 500
"""
df_rel = fetch_df(sql)

if not df_rel.empty:
    G = nx.Graph()

    # Add nodes with different colors
    for _, row in df_rel.iterrows():
        user = row['username']
        song = row['songname']
        artist = row['artist_name']

        # Add user nodes 
        if not G.has_node(f"{user}"):
            G.add_node(f"{user}", color="#0CECA1", size=25, title=f"User: {user}")
        
        # Add song nodes with artist in hover 
        song_label = f"{song}"
        if not G.has_node(song_label):
            G.add_node(song_label, color="#8980DF", size=20, title=f"Song: {song}\nArtist: {artist}")
        
        # Connect user to song
        G.add_edge(f"{user}", song_label)

    # Create network visualization
    net = Network(height="700px", width="100%", bgcolor="#1a1a1a", font_color="white")
    net.from_nx(G)
    
    # Physics settings for better layout
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 150,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": {"iterations": 150}
      }
    }
    """)
    
    net.save_graph("network.html")
    
    st.components.v1.html(open("network.html").read(), height=720)
    
    # Additional info below the graph
    st.info(f"📊 Showing {len(G.nodes())} nodes and {len(G.edges())} connections")
else:
    st.info("No relationship data found.")

# A little Pie Chart action to visualize TOP 10 most liked songs 
st.markdown("### Top 10 Most Liked Songs")

sql = """
    SELECT s.songName, COUNT(l.userID) AS like_count
    FROM Song s
    LEFT JOIN Likes l ON s.song_id = l.song_id
    GROUP BY s.songName
    ORDER BY like_count DESC
    LIMIT 5
"""
df_popular = fetch_df(sql)

if not df_popular.empty:
    fig = px.pie(
        df_popular,
        names="songname",
        values="like_count",
        title="Top 10 Song by Popularity (Likes)"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available for popularity chart.")


# Just taking the average of songs per playlist for a cool looking visual (In My Opinion)
st.markdown("### Average Songs Per Playlist")

sql = """
    SELECT AVG(song_count) AS avg_songs
    FROM (
        SELECT playlistID, COUNT(song_id) AS song_count
        FROM Saves
        GROUP BY playlistID
    ) t
"""
df_avg = fetch_df(sql)

if not df_avg.empty:
    avg_val = df_avg["avg_songs"].iloc[0] or 0

    st.metric("Average Songs Per Playlist", f"{avg_val:.2f}")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_val,
        title={"text": "Avg Songs per Playlist"},
        gauge={"axis": {"range": [0, max(10, avg_val * 2)]}}
    ))

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No playlist activity found.")

# Footer
st.markdown("---")
st.caption(f"Data Dude ©")
