# NamePlexEpisode
Generates SQL to update Plex episode titles based on file names

This Python script generates UPDATE statements to be applied to the Plex sqlite database titling episodes according to the respective file name.  To take effect the resulting SQL must be applied from within the sqlite client provided by Plex as described below. The location of the Plex database and the Plex executable that allows you to edit the database vary with your platform.  Our examples relate to the TrueNAS plugin.  For other implementations you will need to find the correct information.

# Parameters and flags

   - 1st parameter: **Location of the plex database** (mandatory)
   
     As of this writing, the TrueNAS Plex plugin puts the Plex database here:
     
         /mnt/<PoolName>/iocage/jails/PlexMediaServerJail/root/Plex\ Media\ Server/Plug-in\ Support/Databases/com.plexapp.plugins.library.db

   - 2nd parameter: **Partial file location of the episodes to the titled** (mandatory)
   
     This is the path to the series including the library folder. For example if the structure is as follows:
     
         /media/
             Series/
                 BluRay/
                     Star_Trek_The_Original_Series (1966-1969) {imdb-tt0060028}/
                         Season 01/
                             Star_Trek_The_Original_Series (1966) - s01-e01 - Man_Trap_The (1966-09-08).mkv
                             Star_Trek_The_Original_Series (1966) - s01-e02 - Charlie_X (1966-09-15).mkv
                             <...>
     
     We can provide
     
         /media/Series/BluRay/Star_Trek
         
     This will look at all which begins with /media/Series/BluRay/Star_Trek. If you provide /media/Series it would look at all libraries within that path.

   - **--force**
   
     Normally only episodes missing a title are considered. This forces us to look at all episodes. 

   - **--show-current**
     
     Produces additional output detailing the file name, current title, and episode number (also known as 'index').

   - **--ignore-parenthesis-content**
     
     Ignore the text between parenthesis when proposing a title

# Notes

   - This only works for .mkv files.
   
   - It expects the files to be named as
   
         "<series> - s01e01 - <episode title>"
     
   - Use the sqlite client that comes with Plex to run those statements and apply the changes (you must have r/w access to the db file)
   
         <plexapp> --sqlite <database>
         
     Example:
     
         cd /mnt/POOLNAME/iocage/jails/PlexMediaServerJail/root/Plex\ Media\ Server/Plug-in\ Support/Databases
         
         sudo ../../../usr/local/share/plexmediaserver/Plex\ Media\ Server --sqlite com.plexapp.plugins.library.db
             <run the UPDATE statements>
             ;
             .quit
             
   - Stop the Plex Server and make a backup of your database before you start. Then run the statements. Then restart the Plex Server. If things got messed up, stop the server again and restore the copy of the database you saved. No guarantees expressed or implied. Best of Luck!
