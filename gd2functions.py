#!/usr/bin/python
import urllib2
import xml.etree.ElementTree as ET
import datetime
from bs4 import BeautifulSoup
import time
import re
from datetime import date
from datetime import datetime
import string
import json
import traceback

def SetGd2Url(gameid, file):
    year, month, day = gameid[0:4], gameid[5:7], gameid[8:10] #extract date info from the gameid string
    baseURL = 'http://gd2.mlb.com/components/game/mlb/year_' #set URL beginning
    return baseURL + year + '/month_' + month + '/day_' + day + '/gid_' + gameid + '/' + file #full URL

def GetGd2FileXML(gameid, file):
    """Takes MLB gameid string, returns an elementtree object containing file contents"""
    fullURL = SetGd2Url(gameid, file)
    try:
        return ET.parse(urllib2.urlopen(fullURL)) # Tries to return the parsed game element from the XML file if the URL can be opened. If it can't 
    except:                                      # (this only is the case for some extra 2012 Marlins gameids as far as I know), returns none
        print "Couldn't retrieve", file
        return None

def GetGamePlayers(gameid):
    """Takes MLB gameid string, returns an elementtree object containing all players"""
    return GetGd2FileXML(gameid, 'players.xml')                              #
   
def GetGameBox(gameid):
    """Takes MLB gameid string, returns an elementtree object containing the box score"""
    return GetGd2FileXML(gameid, 'rawboxscore.xml')                             #
      
def GetGame(gameid):
    """Takes MLB gameid string, returns an elementtree object containing all innings"""
    return GetGd2FileXML(gameid, 'inning/inning_all.xml')                             #

def GetGameEvents(gameid):
    """Takes MLB gameid string, returns an elementtree object containing all game events"""
    return GetGd2FileXML(gameid, 'game_events.xml')

def GetGameBoxScoreJson(gameid):
    """Takes MLB gameid string, returns an elementtree object containing the box score"""
    fullURL = SetGd2Url(gameid, 'boxscore.json')
    #    print fullURL
    #    print len(fullURL)
    try:
        page = urllib2.urlopen(fullURL)
        data = page.read()
        jdata = json.loads(data)
        return jdata
    except:
        #tb = traceback.format_exc()
        #print tb
        print "Couldn't retrieve box score"

        return None

def DateGames(today = "today"):
    """Takes a date string yyyy-mm-dd, returns list of gameids corresponding to games on that date"""
    if today == "today":
        today = date.today().__str__()
    year, month, day = today[0:4], today[5:7], today[8:10]
    baseURL = 'http://gd2.mlb.com/components/game/mlb/year_'
    fullURL = baseURL + year + '/month_' + month + '/day_' + day + '/'
    return [a.text.strip()[4:-1] for a in BeautifulSoup(urllib2.urlopen(fullURL), "html.parser").find_all('li',text=re.compile("gid_"))]
 
