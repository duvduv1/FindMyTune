# song.py

from typing import Dict, Any, Optional, List
from database.song_database import SongDatabase

class Song:
    """
    Simple wrapper around a row in the songs database,
    exposing all metadata fields as attributes and providing
    a .to_dict() for easy JSON serialization to clients.
    """

    def __init__(self,
                 song_name: str,
                 db: SongDatabase):
        """
        Load the song record by its unique name.
        Raises ValueError if not found.
        """
        row = db.get_song_by_name(song_name)
        if not row:
            raise ValueError(f"Song '{song_name}' not found in database.")

        # Unpack columns in order:
        # (id, song_name, artist_name, album_name,
        #  album_cover_image, album_type, release_date,
        #  spotify_url, spectrograms)
        (self.id,
         self.song_name,
         self.artist_name,
         self.album_name,
         self.album_cover_image,
         self.album_type,
         self.release_date,
         self.spotify_url,
         self.spectrograms_path) = row
    def to_dict(self) -> Dict[str, Any]:
        """
        Return a JSON-serializable representation of this song.
        Excludes internal spectrogram path.
        """
        return {
            "id": self.id,
            "song_name": self.song_name,
            "artist_name": self.artist_name,
            "album_name": self.album_name,
            "album_cover_image": self.album_cover_image,
            "album_type": self.album_type,
            "release_date": self.release_date,
            "spotify_url": self.spotify_url
        }

    @staticmethod
    def all_song_names(db: SongDatabase) -> List[str]:
        """
        Return a list of every song_name in the DB.
        Useful for building game option pools.
        """
        # db.list_all_songs() returns List[Tuple], where row[1] is song_name
        return [row[1] for row in db.list_all_songs()]

    @staticmethod
    def lookup_by_id(song_id: int, db: SongDatabase) -> Optional["Song"]:
        """
        Factory to load a Song by its numeric ID.
        Returns None if not found.
        """
        row = db.get_song_by_id(song_id)
        if not row:
            return None
        # row[1] is song_name
        return Song(row[1], db)
