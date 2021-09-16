#!/usr/bin/env python3
#
# This Python script generates UPDATE statements to be applied to the Plex sqlite database titling episodes according
# to the respective file name. To take effect the resulting SQL must be applied from within the sqlite client
# provided by Plex as described below. The location of the Plex database and the Plex executable that allows you to
# edit the database vary with your platform. Our examples relate to the TrueNAS plugin. For other implementations
# you will need to find the correct information. The original version can be found at
# https://github.com/FilmAf/NamePlexEpisode
#
# Parameters and flags
#
#    - 1st parameter: Location of the plex database (mandatory)
#      As of this writing, the TrueNAS Plex plugin puts the Plex database here:
#          /mnt/<PoolName>/iocage/jails/PlexMediaServerJail/root/Plex\ Media\ Server/Plug-in\ Support/Databases/com.plexapp.plugins.library.db
#
#    - 2nd parameter: Partial file location of the episodes to the titled (mandatory)
#      This is the path to the series including the library folder. For example if the structure is as follows:
#          /media/
#              Series/
#                  BluRay/
#                      Star_Trek_The_Original_Series (1966-1969) {imdb-tt0060028}/
#                          Season 01/
#                              Star_Trek_The_Original_Series (1966) - s01-e01 - Man_Trap_The (1966-09-08).mkv
#                              Star_Trek_The_Original_Series (1966) - s01-e02 - Charlie_X (1966-09-15).mkv
#                              <...>
#      We can provide
#          /media/Series/BluRay/Star_Trek
#      This will look at all which begins with /media/Series/BluRay/Star_Trek. If you provide /media/Series it would
#      look at all libraries within that path.
#
#    --force
#      Normally only episodes missing a title are considered. This forces us to look at all episodes.
#
#    --show-current
#      Produces additional output detailing the file name, current title, and episode number (also known as 'index').
#
#    --ignore-parenthesis-content
#      Ignore the text between parenthesis when proposing a title
#
# Notes
#
#    - This only works for .mkv files.
#
#    - It expects the files to be named as
#          "<series> - s01e01 - <episode title>"
#
#    - Use the sqlite client that comes with Plex to run those statements and apply the changes (you must have r/w
#      access to the db file)
#          <plexapp> --sqlite <database>
#
#      Example:
#          cd /mnt/POOLNAME/iocage/jails/PlexMediaServerJail/root/Plex\ Media\ Server/Plug-in\ Support/Databases
#          sudo ../../../usr/local/share/plexmediaserver/Plex\ Media\ Server --sqlite com.plexapp.plugins.library.db
#              <run the UPDATE statements>
#              ;
#              .quit
#
#    - Stop the Plex Server and make a backup of your database before you start. Then run the statements. Then restart
#      the Plex Server. If things got messed up, stop the server again and restore the copy of the database you saved.
#      No guarantees expressed or implied. Best of Luck!
#

import argparse
import re
import sqlite3


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print('ERROR: ' + str(e) + ' ' + db_file)
    return conn


def get_cmd_args():
    parser = argparse.ArgumentParser(description='Update Plex Episode name from file name')
    parser.add_argument('plex_db_file', type=str, help='Plex database file')
    parser.add_argument('episode_path', type=str, help='Plex episode path within Plex library')
    parser.add_argument('--force', action='store_true', help='Include episodes which already have titles')
    parser.add_argument('--show-current', action='store_true', help='Provides details on matches')
    parser.add_argument('--ignore-parenthesis-content', action='store_true', help='Ignore text between parenthesis')
    args = parser.parse_args()
    args.episode_path = args.episode_path.replace('\\\\', '/').replace('\\', '/').replace('//', '/')
    # print (args)
    return args


class Episodes:
    def __init__(self, id, file, old_title, old_title_sort, index):
        self.id = id
        self.file = file
        self.new_title = ''
        self.old_title = old_title
        self.old_title_sort = old_title_sort
        self.index = index


def find_episodes(conn, file_match):
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT md.id, mp.file, md.title, md.title_sort, md.'index' " +
                "  FROM media_parts mp " +
                "  JOIN media_items mi ON mp.media_item_id = mi.id " +
                "  JOIN metadata_items md ON mi.metadata_item_id = md.id " +
                " WHERE mp.file LIKE '" + file_match + "%'")
    rows = cur.fetchall()
    episode_list = []
    for row in rows:
        episode_list.append(Episodes(row['id'], row['file'], row['title'], row['title_sort'], row['index']))
    return episode_list


def extract_episode_names(episode_list, ignore_parenthesis_content):
    for ep in episode_list:
        title = ep.file
        z = re.search(' [sS]\d+[eE]\d+ -.', title)
        if z:
            title = title[z.end():].strip()
            if ignore_parenthesis_content:
                title = re.sub('\(.*\)', ' ', title).strip()
            title = re.sub('\.mkv$', '', title)
            title = re.sub('[ _]+', ' ', title).strip()
        else:
            title_sort = ''
            title = ''
        ep.new_title = title


def generate_update_sql(episode_list, force_title_update):
    for ep in episode_list:
        if ep.old_title == '' or force_title_update:
            if ep.new_title == '':
                print ("ERROR finding episode in [" + ep.file + "]")
            else:
                sql = "UPDATE metadata_items " + \
                      "SET title = '" + ep.new_title + "' " + \
                      "WHERE id = " + str(ep.id) + ";"
                print(sql)


def show_current(episode_list, force_title_update):
    for ep in episode_list:
        if ep.old_title == '' or force_title_update:
            print('id=[' + str(ep.id) + '] ' + \
                  'index=[' + str(ep.index) + '] ' + \
                  'new_title=[' + ep.new_title + '] ' + \
                  'old_title=[' + ep.old_title + '] ' + \
                  'old_title_sort=[' + ep.old_title_sort + '] ' + \
                  'file=[' + ep.file + ']')


def main():
    args = get_cmd_args()
    conn = create_connection(args.plex_db_file)
    if conn:
        episode_list = find_episodes(conn, args.episode_path)
        extract_episode_names(episode_list, args.ignore_parenthesis_content)
        if args.show_current:
            show_current(episode_list, args.force)
        generate_update_sql(episode_list, args.force)
        conn.close()


main()
