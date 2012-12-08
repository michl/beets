import os
import logging
from beets import plugins
from beets import ui
from beets.util import normpath
from beets.ui import commands
from beets.ui import Subcommand

log = logging.getLogger('beets')
log.setLevel(logging.DEBUG)

DEFAULT_GENRELIST = os.path.join(os.path.dirname(__file__), 'genres.txt')

fallback_str = None
genres = {}

def reverse_dict(orig):
	reverse = {}
	for (genre, artists) in orig.items():
		for artist in artists:
			reverse[artist]=genre
	return reverse

def get_genre(artist, genre_dict):
	try:
		return genre_dict[artist]
	except KeyError:
		return None
		
update_cmd = Subcommand('update-genres', help='Update the genres of all media in library acording to the current genre list file')
def update_genres(lib, config, opts, args):
	global genres
	global fallback_str
	for item in lib.items(ui.decargs(args)):
		if item.album_id is not None:
			continue
		genre = get_genre(item.artist, genres)
		log.warn("title: %s, artist: %s, genre: %s" % (item.title, item.artist, genre))
		if not genre and fallback_str != None:
			genre = fallback_str
			log.warn(u'no genre for %s in list: fallback to %s' % (item.artist, genre))
		if genre is not None:
			log.warn(u'adding genre for %s from list: %s' % (item.artist, genre))
		item.genre = genre
		lib.store(item)
		item.write()

	for album in lib.albums():
		genre = get_genre(album.albumartist, genres)
		if (genre is None) and (fallback_str is not None):
			genre = fallback_str
			log.warn(u'no genre for %s in list: fallback to %s' % (album.albumartist, genre))
		if genre is not None:
			log.warn(u'adding genre for %s from list: %s' % (album.albumartist, genre))
			bluo=''
		album.genre = genre
		for item in album.items():
			item.write()
update_cmd.func=update_genres

class GenreListPlugin(plugins.BeetsPlugin):
    def __init__(self):
        super(GenreListPlugin, self).__init__()
        self.import_stages = [self.imported]
        
    def commands(self):
        return [update_cmd]

    def configure(self, config):
        global fallback_str
        global genres
        
        gl_filename = ui.config_val(config, 'genrelist', 'listfile', None)
        # Read the genres tree for canonicalization if enabled.
        if gl_filename is not None:
            gl_filename = gl_filename.strip()
            if not gl_filename:
                gl_filename = DEFAULT_GENRELIST
            gl_filename = normpath(gl_filename)

            from yaml import load
            genres_tree = load(open(gl_filename, 'r'))
            genres=reverse_dict(genres_tree)

        fallback_str = ui.config_val(config, 'genrelist', 'fallback_str', None)

    def imported(self, config, task):
        if task.is_album:
            album = config.lib.get_album(task.album_id)
            genre = get_genre(album.albumartist, genres)
        else:
            item = task.item
            genre = get_genre(item.artist, genres)

        if not genre and fallback_str != None:
            genre = fallback_str
            log.debug(u'no genre in list: fallback to %s' % genre)

        if genre is not None:
            log.warn(u'adding genre from list: %s' % genre)

            if task.is_album:
				album.genre = genre
            else:
                item.genre = genre
                config.lib.store(item)
