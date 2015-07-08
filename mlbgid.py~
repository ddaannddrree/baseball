import urllib2
import xml.etree.ElementTree as ET
import datetime
from bs4 import BeautifulSoup
import re
import csv
import time
from datetime import date
import pytz
import gspread 

global awayteamruns
global hometeamruns

def SetFieldNames():
   """returns the list of fieldnames for the dictwriter"""
   return ['gameid', 'away_team', 'home_team', 'inningnum', 'score', 'away_team_runs', 'home_team_runs', 'next', 'num', 'b', 's', 'o', 'start_tfs', 'start_tfs_zulu', 'batter', 'battingteam', 'stand', 'b_height', 'pitcher', 'p_throws', 'playdes', 'esplaydes', 'event', 'des', 'des_es', 'id', 'on_1b', 'on_2b', 'on_3b', 'type', 'tfs', 'tfs_zulu', 'x', 'y', 'sv_id', 'start_speed', 'end_speed', 'sz_top', 'sz_bot', 'pfx_x', 'pfx_z', 'px', 'pz', 'x0', 'y0', 'z0', 'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az', 'break_y', 'break_angle', 'break_length', 'pitch_type', 'type_confidence', 'zone', 'nasty', 'spin_dir', 'spin_rate', 'cc', 'mt']

def CreateWriter(file):
   """takes an open, writable CSV file, creates a dict writer for parse games function"""   
   fieldnames = SetFieldNames()
   return csv.DictWriter(file, delimiter = ',', fieldnames = fieldnames)  
   
def GetGame(gameid):
   """Takes MLB gameid string, returns an elementtree object containing all game events"""
   year, month, day = gameid[0:4], gameid[5:7], gameid[8:10] #extract date info from the gameid string
   baseURL = 'http://gd2.mlb.com/components/game/mlb/year_' #set URL beginning
   fullURL = baseURL + year + '/month_' + month + '/day_' + day + '/gid_' + gameid + '/inning/inning_all.xml' #construct full URL for the game event XML file
   try:
      return ET.parse(urllib2.urlopen(fullURL)) # Tries to return the parsed game element from the XML file if the URL can be opened. If it can't 
   except:                                      # (this only is the case for some extra 2012 Marlins gameids as far as I know), returns none
      return None                               #
      
def TodaysGames():
   """Returns a list of gameids corresponding to games on the current date"""
   today = datetime.date.today().__str__()
   year, month, day = today[0:4], today[5:7], today[8:10]
   baseURL = 'http://gd2.mlb.com/components/game/mlb/year_'
   fullURL = baseURL + year + '/month_' + month + '/day_' + day + '/'
   return [a.text.strip()[4:-1] for a in BeautifulSoup(urllib2.urlopen(fullURL)).find_all('li',text=re.compile("gid_"))]

def DateGames(date):
   """Takes a date string yyyy-mm-dd, returns list of gameids corresponding to games on that date"""
   today = date
   year, month, day = today[0:4], today[5:7], today[8:10]
   baseURL = 'http://gd2.mlb.com/components/game/mlb/year_'
   fullURL = baseURL + year + '/month_' + month + '/day_' + day + '/'
   return [a.text.strip()[4:-1] for a in BeautifulSoup(urllib2.urlopen(fullURL)).find_all('li',text=re.compile("gid_"))]
   
def ParsePitch(pitch, GameProperties, InnProperties, ABProperties, istop, writer):
   """Takes pitch XML element, dictionaries for game, inning, and AB properties, boolean for top/bottom inning, and a dictwriter; writes all attributes + pitch attributes as CSV row"""
   if istop:
      battingTeam = {'battingteam' : InnProperties['away_team']}
   else:
      battingTeam = {'battingteam' : InnProperties['home_team']}
   PitchProperties = pitch.attrib
   try:
      PitchProperties['on_1b']
   except KeyError:
      PitchProperties['on_1b'] = ' '
   try:
      PitchProperties['on_2b']
   except KeyError:
      PitchProperties['on_2b'] = ' '
   try:
      PitchProperties['on_3b']
   except KeyError:
      PitchProperties['on_3b'] = ' '
   finaldict = dict(GameProperties.items() + InnProperties.items() + ABProperties.items() + battingTeam.items() + PitchProperties.items()) #DIE FOREVER TEXT ENCODING
   
   for key in finaldict.keys():
      finaldict[key] = finaldict[key].encode('ascii','ignore')
	  
   writer.writerow(finaldict)
   
   return 'pitch written' #not sure what this should return really

def ParseAtBat(atbat):
   """Takes an atbat XML element, returns dictionary of atbat properties"""  
   global awayteamruns
   global hometeamruns
   atbatdict = atbat.attrib
   atbatdict['playdes'] = atbatdict.pop('des')
   try:
      atbatdict['esplaydes'] = atbatdict.pop('des_es')
   except KeyError:
      atbatdict['esplaydes'] = ' '
   try:
      atbatdict['away_team_runs']
      newawayruns = int(atbatdict['away_team_runs'])
      atbatdict['away_team_runs'] = str(awayteamruns)
      awayteamruns = newawayruns
   except KeyError:
      atbatdict['away_team_runs'] = str(awayteamruns)
   try:	  
      atbatdict['home_team_runs']
      newhomeruns = int(atbatdict['home_team_runs'])
      atbatdict['home_team_runs'] = str(hometeamruns)
      hometeamruns = newhomeruns
   except KeyError:
	  atbatdict['home_team_runs'] = str(hometeamruns)
   try:
      atbatdict['score']
   except KeyError:
      atbatdict['score'] = ' '
   try:
      del atbatdict['event2']
   except KeyError:
      return atbatdict
 	  
   return atbatdict

def ParseInning(inning):
   """Takes an inning XML element, returns dictionary of inning properties"""
   inningdict = inning.attrib
   inningdict['inningnum'] = inningdict.pop('num')
   return inningdict

def GetNumberOfInnings(game):
    """Returns the # of innings"""
    maxinning = 0
    for element in game.iter():
        if element.tag == 'inning':
            foodict = element.attrib
            inum = foodict.pop('num')
            if inum > maxinning:
                maxinning = inum
    return maxinning

def AddGameToSet(game,set):
    maxinning = 0
    hometeam = '';
    awayteam = '';
    if (game != None):
        for element in game.iter():
            if element.tag == 'inning':
                foodict = element.attrib
                maxinning = maxinning+1
                hometeam = foodict['home_team']
                awayteam = foodict['away_team']
                set[hometeam] = maxinning
                set[awayteam] = maxinning
    return set

def BuildInningSet(date):
    gameids = DateGames(date)
    inningset = dict()
    for game in gameids:
       thegame = GetGame(game)
       inningset = AddGameToSet(thegame,inningset)
    return inningset


def PrintMonth():
    print 'Rangers,Reds,Rockies,Rays,Tigers,Brewers,Orioles,Indians,Giants,Braves,Pirates,BlueJays,RedSox,Mets,Cardinals,Yankees,'
    teamlist = ['tex','cin','col','tba','det','mil','bal','cle','sfn','atl','pit','tor','bos','nyn','sln','nya']
    today = date.today();
    
    for i in range(1,31):
        if  i <= today.day:
            iset = BuildInningSet('2013-08-%02d'%i)
            s = '2013-08-%02d,'%i
            for team in teamlist:
                if (team in iset):
                    if iset[team] > 9:
                        s += '%d,'%(iset[team]-9)
                    else:
                        s += '0,'
                else:
                    s += '0,'
            print s

            

def UpdateTodayInSheet():
    gs = gspread.login('dandreauto@gmail.com','841Melissa5814')
    spreadsheet = gs.open('Extra Innings')
    worksheet = spreadsheet.worksheet('AutoImport')
    teamlist = ['tex','cin','col','tba','det','mil','bal','cle','sfn','atl','pit','tor','bos','nyn','sln','nya']
    today = date.today();
    
    i = today.day
    iset = BuildInningSet('2013-08-%02d'%i)
    s = '2013-08-%02d,'%i
    col= 2
    row = i + 2
    for tt in range(0,len(teamlist)):
        team = teamlist[tt]
        if (team in iset):
            if iset[team] > 9:
                worksheet.update_cell(row,col,iset[team]-9) 
        col = col+1
    

    
def ParseGame(game, gameid, writer):
   """Takes a game element, a gameid string, and a dictwriter and adds rows to a csv file correpsonding to the game's pitches"""
   
   global awayteamruns
   global hometeamruns
   
   GameProperties = {'gameid' : gameid}  
   awayteamruns = 0
   hometeamruns = 0   
   
   for element in game.iter():
      if element.tag == 'inning':
         InnProperties = ParseInning(element)
      if element.tag == 'top':
         istop = True
      if element.tag == 'bottom':
         istop = False
      if element.tag == 'atbat':
         ABProperties = ParseAtBat(element)
      if element.tag == 'pitch':
         ParsePitch(element, GameProperties, InnProperties, ABProperties, istop, writer)
      else:
         continue

def WriteGames(gameids, filename):
   """Takes a list of game ids and a csv filename string and uses ParseGame to write each to a csv file"""
   global awayteamruns
   global hometeamruns
   outputFile = open(filename,'wb')
   outputWriter = CreateWriter(outputFile)
   outputWriter.writeheader()
   for game in gameids:
      try:
	     ParseGame(GetGame(game), game, outputWriter)
      except AttributeError:
         print "Couldn't find " + game
      print game + ' completed'
   return outputFile

