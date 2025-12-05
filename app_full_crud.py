import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# --- Config & env ---
st.set_page_config(page_title="🎵 Music DB CRUD", page_icon="🎵", layout="wide")
load_dotenv()

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")

if not all([PGDATABASE, PGUSER, PGPASSWORD]):
    st.error("Missing DB credentials. Please set PGDATABASE, PGUSER, and PGPASSWORD in your .env file.")
    st.stop()

from sqlalchemy.engine import URL
from sqlalchemy import event

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
            "sslmode": "require"
        },
    )

engine = create_engine(
    make_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=0,
    pool_timeout=5,
    pool_recycle=1800,
)

@event.listens_for(engine, "connect")
def _set_search_path(dbapi_connection, connection_record):
    with dbapi_connection.cursor() as cur:
        cur.execute("SET statement_timeout TO 8000")
        cur.execute(f"SET search_path TO {PGUSER}, public")

# --- Session flash ---
st.session_state.setdefault("just_inserted", None)
st.session_state.setdefault("just_updated", None)
st.session_state.setdefault("just_deleted", None)

st.title("🎵 Night Hawk's Music Database - Full CRUD")
st.caption("Create, Read, Update, Delete operations for your music database")

# --- Helpers ---
def fetch_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()

def fetch_users() -> pd.DataFrame:
    return fetch_df("SELECT userID, userName FROM User_table ORDER BY userID")

def fetch_artists() -> pd.DataFrame:
    return fetch_df("SELECT artistID, artist_name, artist_location FROM Artist ORDER BY artistID")

def fetch_albums() -> pd.DataFrame:
    return fetch_df("SELECT albumID, album_name, release_date FROM Album ORDER BY albumID")

def fetch_songs(limit: int) -> pd.DataFrame:
    sql = 'SELECT song_id, songName, dayReleased FROM Song ORDER BY song_id LIMIT :lim'
    return fetch_df(sql, {"lim": int(limit)})

def fetch_playlists() -> pd.DataFrame:
    return fetch_df("SELECT playlistID, playlist_name, num_songs FROM Playlist ORDER BY playlistID")

# --- SONG CRUD ---
def insert_song(name: str, date_released):
    sql = 'INSERT INTO Song(songName, dayReleased) VALUES (:n, :d) RETURNING song_id, songName, dayReleased'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"n": name, "d": date_released})
    return df.iloc[0].to_dict() if not df.empty else None

def update_song(sid: int, name: str, date_released):
    sql = 'UPDATE Song SET songName = :n, dayReleased = :d WHERE song_id = :sid RETURNING song_id, songName, dayReleased'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"sid": int(sid), "n": name, "d": date_released})
    return df.iloc[0].to_dict() if not df.empty else None

def delete_song(sid: int):
    sql = 'DELETE FROM Song WHERE song_id = :sid RETURNING song_id, songName, dayReleased'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"sid": int(sid)})
    return df.iloc[0].to_dict() if not df.empty else None

# --- ARTIST CRUD ---
def insert_artist(name: str, location: str | None):
    sql = 'INSERT INTO Artist(artist_name, artist_location) VALUES (:n, :l) RETURNING artistID, artist_name, artist_location'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"n": name, "l": location})
    return df.iloc[0].to_dict() if not df.empty else None

def update_artist(aid: int, name: str, location: str | None):
    sql = 'UPDATE Artist SET artist_name = :n, artist_location = :l WHERE artistID = :aid RETURNING artistID, artist_name, artist_location'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"aid": int(aid), "n": name, "l": location})
    return df.iloc[0].to_dict() if not df.empty else None

def delete_artist(aid: int):
    sql = 'DELETE FROM Artist WHERE artistID = :aid RETURNING artistID, artist_name, artist_location'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"aid": int(aid)})
    return df.iloc[0].to_dict() if not df.empty else None

# --- USER CRUD ---
def insert_user(username: str):
    sql = 'INSERT INTO User_table(userName) VALUES (:n) RETURNING userID, userName'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"n": username})
    return df.iloc[0].to_dict() if not df.empty else None

def update_user(uid: int, username: str):
    sql = 'UPDATE User_table SET userName = :n WHERE userID = :uid RETURNING userID, userName'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"uid": int(uid), "n": username})
    return df.iloc[0].to_dict() if not df.empty else None

def delete_user(uid: int):
    sql = 'DELETE FROM User_table WHERE userID = :uid RETURNING userID, userName'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"uid": int(uid)})
    return df.iloc[0].to_dict() if not df.empty else None

# --- PLAYLIST CRUD ---
def insert_playlist(name: str, num_songs: int):
    sql = 'INSERT INTO Playlist(playlist_name, num_songs) VALUES (:n, :ns) RETURNING playlistID, playlist_name, num_songs'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"n": name, "ns": num_songs})
    return df.iloc[0].to_dict() if not df.empty else None

def update_playlist(pid: int, name: str, num_songs: int):
    sql = 'UPDATE Playlist SET playlist_name = :n, num_songs = :ns WHERE playlistID = :pid RETURNING playlistID, playlist_name, num_songs'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"pid": int(pid), "n": name, "ns": num_songs})
    return df.iloc[0].to_dict() if not df.empty else None

def delete_playlist(pid: int):
    sql = 'DELETE FROM Playlist WHERE playlistID = :pid RETURNING playlistID, playlist_name, num_songs'
    with engine.begin() as conn:
        df = pd.read_sql(text(sql), conn, params={"pid": int(pid)})
    return df.iloc[0].to_dict() if not df.empty else None

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Options")
    row_limit = st.number_input("Row limit", min_value=1, max_value=2000, value=200, step=50)
    st.markdown("---")
    st.caption("🦅 Night Hawk Edition")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Users", "🎤 Artists", "🎵 Songs", "💿 Albums", "📋 Playlists"])

# ============================================
# TAB 1: USERS CRUD
# ============================================
with tab1:
    st.subheader("👤 Users")

    # Flash messages
    for key, icon, msg in [
        ("just_inserted", "✅", "Inserted"),
        ("just_updated", "✏️", "Updated"),
        ("just_deleted", "🗑️", "Deleted")
    ]:
        if st.session_state.get(key):
            rec = st.session_state[key]
            st.success(f"{icon} {msg} user: {rec.get('username', rec.get('userName', 'N/A'))} (ID {rec.get('userid', rec.get('userID', 'N/A'))})")
            st.session_state[key] = None

    users = fetch_users()
    st.dataframe(users, use_container_width=True)

    # INSERT
    st.markdown("### ➕ Insert User")
    with st.form("insert_user_form", clear_on_submit=False):
        username = st.text_input("Username*", placeholder="night_hawk_rocks")
        if st.form_submit_button("Insert User"):
            if not username.strip():
                st.warning("Username is required.")
            else:
                rec = insert_user(username.strip())
                if rec:
                    st.session_state.just_inserted = rec
                    st.rerun()

    # UPDATE
    st.markdown("### ✏️ Update User")
    if users.empty:
        st.caption("No users to update.")
    else:
        user_choices = {int(r.userid): f"{int(r.userid)} — {r['username']}" for _, r in users.iterrows()}
        sel_uid = st.selectbox("User", options=list(user_choices.keys()), format_func=lambda k: user_choices[k], key="upd_user_sel")
        current = users[users["userid"] == sel_uid].iloc[0]

        with st.form("update_user_form", clear_on_submit=False):
            new_username = st.text_input("Username", current["username"])
            if st.form_submit_button("Update User"):
                rec = update_user(sel_uid, new_username.strip())
                if rec:
                    st.session_state.just_updated = rec
                    st.rerun()

    # DELETE
    st.markdown("### 🗑️ Delete User")
    if users.empty:
        st.caption("No users to delete.")
    else:
        colA, colB = st.columns([3, 2])
        with colA:
            del_uid = st.selectbox("Select user", options=list(user_choices.keys()),
                                  format_func=lambda k: user_choices[k], key="del_user_sel")
        with colB:
            confirm = st.checkbox("Confirm deletion", key="del_user_confirm")

        if st.button("Delete User"):
            if not confirm:
                st.warning("Please confirm before deleting.")
            else:
                rec = delete_user(int(del_uid))
                if rec:
                    st.session_state.just_deleted = rec
                    st.rerun()

# ============================================
# TAB 2: ARTISTS CRUD
# ============================================
with tab2:
    st.subheader("🎤 Artists")

    # Flash messages
    for key, icon, msg in [
        ("just_inserted", "✅", "Inserted"),
        ("just_updated", "✏️", "Updated"),
        ("just_deleted", "🗑️", "Deleted")
    ]:
        if st.session_state.get(key):
            rec = st.session_state[key]
            st.success(f"{icon} {msg} artist: {rec.get('artist_name', 'N/A')} (ID {rec.get('artistid', 'N/A')})")
            st.session_state[key] = None

    artists = fetch_artists()
    st.dataframe(artists, use_container_width=True)

    # INSERT
    st.markdown("### ➕ Insert Artist")
    with st.form("insert_artist_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            artist_name = st.text_input("Artist Name*", placeholder="Taylor Swift")
        with c2:
            artist_location = st.text_input("Location (optional)", placeholder="Nashville, TN")
        if st.form_submit_button("Insert Artist"):
            if not artist_name.strip():
                st.warning("Artist name is required.")
            else:
                rec = insert_artist(artist_name.strip(), artist_location.strip() or None)
                if rec:
                    st.session_state.just_inserted = rec
                    st.rerun()

    # UPDATE
    st.markdown("### ✏️ Update Artist")
    if artists.empty:
        st.caption("No artists to update.")
    else:
        artist_choices = {int(r.artistid): f"{int(r.artistid)} — {r['artist_name']}" for _, r in artists.iterrows()}
        sel_aid = st.selectbox("Artist", options=list(artist_choices.keys()), format_func=lambda k: artist_choices[k], key="upd_artist_sel")
        current = artists[artists["artistid"] == sel_aid].iloc[0]

        with st.form("update_artist_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                new_name = st.text_input("Artist Name", current["artist_name"])
            with c2:
                new_location = st.text_input("Location", current["artist_location"] or "")
            if st.form_submit_button("Update Artist"):
                rec = update_artist(sel_aid, new_name.strip(), new_location.strip() or None)
                if rec:
                    st.session_state.just_updated = rec
                    st.rerun()

    # DELETE
    st.markdown("### 🗑️ Delete Artist")
    if artists.empty:
        st.caption("No artists to delete.")
    else:
        colA, colB = st.columns([3, 2])
        with colA:
            del_aid = st.selectbox("Select artist", options=list(artist_choices.keys()),
                                  format_func=lambda k: artist_choices[k], key="del_artist_sel")
        with colB:
            confirm = st.checkbox("Confirm deletion", key="del_artist_confirm")

        if st.button("Delete Artist"):
            if not confirm:
                st.warning("Please confirm before deleting.")
            else:
                rec = delete_artist(int(del_aid))
                if rec:
                    st.session_state.just_deleted = rec
                    st.rerun()

# ============================================
# TAB 3: SONGS CRUD
# ============================================
with tab3:
    st.subheader("🎵 Songs")

    # Flash messages
    for key, icon, msg in [
        ("just_inserted", "✅", "Inserted"),
        ("just_updated", "✏️", "Updated"),
        ("just_deleted", "🗑️", "Deleted")
    ]:
        if st.session_state.get(key):
            rec = st.session_state[key]
            st.success(f"{icon} {msg} song: {rec.get('songname', rec.get('songName', 'N/A'))} (ID {rec.get('song_id', 'N/A')})")
            st.session_state[key] = None

    songs = fetch_songs(int(row_limit))
    st.dataframe(songs, use_container_width=True)

    # INSERT
    st.markdown("### ➕ Insert Song")
    with st.form("insert_song_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            song_name = st.text_input("Song Name*", placeholder="Anti-Hero")
        with c2:
            date_released = st.date_input("Release Date")
        if st.form_submit_button("Insert Song"):
            if not song_name.strip():
                st.warning("Song name is required.")
            else:
                rec = insert_song(song_name.strip(), date_released)
                if rec:
                    st.session_state.just_inserted = rec
                    st.rerun()

    # UPDATE
    st.markdown("### ✏️ Update Song")
    if songs.empty:
        st.caption("No songs to update.")
    else:
        song_choices = {int(r.song_id): f"{int(r.song_id)} — {r['songname']}" for _, r in songs.iterrows()}
        sel_sid = st.selectbox("Song", options=list(song_choices.keys()), format_func=lambda k: song_choices[k], key="upd_song_sel")
        current = songs[songs["song_id"] == sel_sid].iloc[0]

        with st.form("update_song_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                new_song_name = st.text_input("Song Name", current["songname"])
            with c2:
                new_date = st.date_input("Release Date", pd.to_datetime(current["dayreleased"]))
            if st.form_submit_button("Update Song"):
                rec = update_song(sel_sid, new_song_name.strip(), new_date)
                if rec:
                    st.session_state.just_updated = rec
                    st.rerun()

    # DELETE
    st.markdown("### 🗑️ Delete Song")
    if songs.empty:
        st.caption("No songs to delete.")
    else:
        colA, colB = st.columns([3, 2])
        with colA:
            del_sid = st.selectbox("Select song", options=list(song_choices.keys()),
                                  format_func=lambda k: song_choices[k], key="del_song_sel")
        with colB:
            confirm = st.checkbox("Confirm deletion", key="del_song_confirm")

        if st.button("Delete Song"):
            if not confirm:
                st.warning("Please confirm before deleting.")
            else:
                rec = delete_song(int(del_sid))
                if rec:
                    st.session_state.just_deleted = rec
                    st.rerun()

# ============================================
# TAB 4: ALBUMS (READ ONLY)
# ============================================
with tab4:
    st.subheader("💿 Albums")
    albums = fetch_albums()
    st.dataframe(albums, use_container_width=True)
    st.info("💡 Album CRUD coming soon! For now, you can view albums here.")

# ============================================
# TAB 5: PLAYLISTS CRUD
# ============================================
with tab5:
    st.subheader("📋 Playlists")

    # Flash messages
    for key, icon, msg in [
        ("just_inserted", "✅", "Inserted"),
        ("just_updated", "✏️", "Updated"),
        ("just_deleted", "🗑️", "Deleted")
    ]:
        if st.session_state.get(key):
            rec = st.session_state[key]
            st.success(f"{icon} {msg} playlist: {rec.get('playlist_name', 'N/A')} (ID {rec.get('playlistid', 'N/A')})")
            st.session_state[key] = None

    playlists = fetch_playlists()
    st.dataframe(playlists, use_container_width=True)

    # INSERT
    st.markdown("### ➕ Insert Playlist")
    with st.form("insert_playlist_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            playlist_name = st.text_input("Playlist Name*", placeholder="My Favorites")
        with c2:
            num_songs = st.number_input("Number of Songs", min_value=0, value=0, step=1)
        if st.form_submit_button("Insert Playlist"):
            if not playlist_name.strip():
                st.warning("Playlist name is required.")
            else:
                rec = insert_playlist(playlist_name.strip(), int(num_songs))
                if rec:
                    st.session_state.just_inserted = rec
                    st.rerun()

    # UPDATE
    st.markdown("### ✏️ Update Playlist")
    if playlists.empty:
        st.caption("No playlists to update.")
    else:
        playlist_choices = {int(r.playlistid): f"{int(r.playlistid)} — {r['playlist_name']}" for _, r in playlists.iterrows()}
        sel_pid = st.selectbox("Playlist", options=list(playlist_choices.keys()), format_func=lambda k: playlist_choices[k], key="upd_playlist_sel")
        current = playlists[playlists["playlistid"] == sel_pid].iloc[0]

        with st.form("update_playlist_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                new_playlist_name = st.text_input("Playlist Name", current["playlist_name"])
            with c2:
                new_num_songs = st.number_input("Number of Songs", min_value=0, value=int(current["num_songs"]), step=1)
            if st.form_submit_button("Update Playlist"):
                rec = update_playlist(sel_pid, new_playlist_name.strip(), int(new_num_songs))
                if rec:
                    st.session_state.just_updated = rec
                    st.rerun()

    # DELETE
    st.markdown("### 🗑️ Delete Playlist")
    if playlists.empty:
        st.caption("No playlists to delete.")
    else:
        colA, colB = st.columns([3, 2])
        with colA:
            del_pid = st.selectbox("Select playlist", options=list(playlist_choices.keys()),
                                  format_func=lambda k: playlist_choices[k], key="del_playlist_sel")
        with colB:
            confirm = st.checkbox("Confirm deletion", key="del_playlist_confirm")

        if st.button("Delete Playlist"):
            if not confirm:
                st.warning("Please confirm before deleting.")
            else:
                rec = delete_playlist(int(del_pid))
                if rec:
                    st.session_state.just_deleted = rec
                    st.rerun()