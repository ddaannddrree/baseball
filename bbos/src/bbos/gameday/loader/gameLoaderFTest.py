import unittest
from bbos.gameday.www.gameXMLProvider import GamedayXMLProvider
from bbos.gameday.loader.gameLoader import GamedayGameLoader
from bbos.db.db import DB

class GamedayLoaderFTest(unittest.TestCase):
    
    def setUp(self):
        self.db = DB();
            
    def testLoad(self):
        url = "http://gd2.mlb.com/components/game/mlb/year_2008/month_04/day_12/gid_2008_04_12_milmlb_nynmlb_1/"
        
        xmlProvider = GamedayXMLProvider(url)
        
        gameLoader = GamedayGameLoader(self.db, xmlProvider)
        
        gameLoader.delete()
        
        gameLoader.loadGame()
        
        loaded = gameLoader.isAlreadyLoaded()
        
        self.assertTrue(loaded)      
                   
    
           
              

        
        