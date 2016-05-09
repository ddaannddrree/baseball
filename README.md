# baseball

CAVEAT: Each file has much cruft.   This is sometimes helpful but more often confusing, probably.    YMMV.   I am ashamed of this code, FWIW, but it's exactly as good as the time and my relative lack of skill in python allowed. 

Ok, the way this works is that there is a wbNmK.py file that has the basic code in for wb year N month K. 

The basic code gets called by a run_wbNmK.py file that also publishes the resulting webpage to a server [note that the run-script will not work with the current password -- that needs to be the updated right password].   

The code calls wbNmK.DoTheDay() which is effectively the main function.   It figures out the date range and calls getFilledTeams, which is responsible for building up the stats for each team (and all their players).   The function OutputTablesToFile writes the html.  

GetFilledTeams works by first getting the teams, then getting all the stats for the games within a range (by calling CompileRangeGames) and gets stats for pitchers (press) and batters (bress).   It then pushes the stats into the teams. 

getTeams is usually where I start for a month.   There are examples in various wbNmK files for team based and player based "teams".   Usually in getTeams is also where modifiers or offsets get added in as well.   It's also where I typically load in the previous months' standings for the season-to-date tables.    

CompileRangeGames() calls CompileDayGames() which for each game on a day, gets the json boxscore and then calls the appropriate extraction functions for the month's statistics.   GetGame(g) gets the innings_all xml, which was necessary for last month to get stolen bases against (for example).   Often, everything is available in the jsonbox, which we then call ExtractPlayerInfo() to get at only those stats we want.    Inside of ExtractPlayerInfo, makeBattterDict and makePitcherDict are called (passing along any other pitcher or batter stats calculcated outside of here, such as p_atbats in wb5m1.py).   These two functions are where the stats needed for the month are specified (at least for player based months).   
These functions change every month.   We should really keep an archive of the rules for each month to make it easier to match up code to new functionality. 

Key to getting the scoring right is to set the fnames_for_scoring in getVictoryPoints, and to set the right columns in OutputTablesToFile. 

Apologies for the cruft in the repository.   












