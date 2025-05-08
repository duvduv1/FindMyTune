// lib/models/song.dart

class Song {
  final int id;
  final String songName;
  final String artistName;
  final String? albumName;
  final String? albumCoverImage;
  final String albumType;
  final String? releaseDate;
  final String? spotifyUrl;

  Song({
    required this.id,
    required this.songName,
    required this.artistName,
    this.albumName,
    this.albumCoverImage,
    required this.albumType,
    this.releaseDate,
    this.spotifyUrl,
  });

  factory Song.fromJson(Map<String, dynamic> json) => Song(
        id: json['id'] as int,
        songName: json['song_name'] as String,
        artistName: json['artist_name'] as String,
        albumName: json['album_name'] as String?,
        albumCoverImage: json['album_cover_image'] as String?,
        albumType: json['album_type'] as String,
        releaseDate: json['release_date'] as String?,
        spotifyUrl: json['spotify_url'] as String?,
      );
}
