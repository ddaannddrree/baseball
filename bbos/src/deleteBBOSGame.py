from bbos.config import loggingSetup
loggingSetup.initializeLogging("deleteBBOSGame.py")
import logging
from bbos.gameday.www.directoryStructure import GamedayDirectoryStructure
from bbos.gameday.options import commandLineOptionsParser
from bbos.config.bbosConfig import BBOSConfig
from bbos.gameday.loader.gameLoader import GamedayGameLoader
from bbos.gameday.www.gameXMLProvider import GamedayXMLProvider
from bbos.gameday.loader.gameStatsWorkList import GameStatsWorkList
from bbos.db.db import DB
      
       
def main():
    
    options = commandLineOptionsParser.parseDeleteOptions()
    
    logging.info("Starting delete!")
    
    league = options.league
    
    gamedayDirectory = GamedayDirectoryStructure(BBOSConfig.gamedayURL, league)
    
    if not options.game:
        logging.error("delete only accepts league and -g gameName as parameters")
        
    gamedayGameURLs = gamedayDirectory.getGameURLsForGame(options.game)  
    
    xmlProvider = GamedayXMLProvider(gamedayGameURLs[0])
        
    db = DB();
        
    gameStatsWorkList = GameStatsWorkList()
            
    gameLoader = GamedayGameLoader(db, xmlProvider, gameStatsWorkList)
        
    gameLoader.delete()
    
    logging.info("")
    logging.info("delete complete!")


if __name__ == '__main__': main()
    
