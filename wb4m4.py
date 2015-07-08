#!/usr/bin/python
import urllib2
import xml.etree.ElementTree as ET
import datetime
from bs4 import BeautifulSoup
import re
import csv
import time
from datetime import date
from datetime import timedelta
from datetime import datetime
import pytz
import gspread 
import MySQLdb
import MySQLdb.cursors
import string
import collections
import copy
import pickle
import json
import numpy
import pdb

db= MySQLdb.connect(user='root' , passwd='andnotbut', db='wb3m4')
cursor = db.cursor()

dbd = MySQLdb.connect(user='root' , passwd='andnotbut', db='wb3m4',cursorclass=MySQLdb.cursors.DictCursor)
cursord = dbd.cursor()

def hist(s):
   d = {}
   for i in s.upper():
      if i.isalpha():
         d[i] = d[i] + 1 if i in d else 1
         for k in sorted(d.keys()):
            print k*d[k]

def getGamesForPlayer(player_id):
   n = cursord.execute('select * from info where player=%s order by date,id'%(str(player_id)))
   if n > 0:
      res = cursord.fetchall()
      return res
   else:
      return None

def printGameToCSV(file,g,first):
   fnames = ['team', 'first_name','last_name','player','date','gamekey','status','pitcherp','W','SV','ER','QS','DP','HR','SB','H','ASS','BB']   
   w = csv.DictWriter(file,fnames,extrasaction='ignore')
   if first:
      w.writer.writerow(fnames)
   w.writerow(g)

def addUpdate(d,key,val):
   if key in d:
      d[key] = d[key] + val
   else:
      d[key] = val
   return d

def getLastNameCount(t):
   players = t['batters'] + t['pitchers']
   lastlets = ''.join([x['name'][0][0] for x in players])
   return collections.Counter(lastlets).most_common()[0][1]

def getLongestStreak(x,onlyLatest=False):
   stk_n = 0
   in_stk = 0
   max_stk = 0
   for xx in x:
      if xx:
         if in_stk:
            stk_n = stk_n+1
         else:
            stk_n = 1
            in_stk = 1
      else:
         in_stk = 0
         stk_n = 0
      if stk_n > max_stk:
         max_stk = stk_n
   if (onlyLatest):
      return stk_n
   else:
      return max_stk

def teamScore(t,onlyLatest=False):
   team_w = {}
   team_sv = {}
   team_hr = {}
   team_sb = {}

   team_h = 0
   team_bb = 0
   team_ass = 0
   team_qs = 0
   team_dp = 0
   team_er = 0
   tscore = {}
   tscore['team_name'] = t['team_name']

   team_name_streak = getLastNameCount(t)

   for b in t['batters']:
      gs = getGamesForPlayer(b['id'])
      if gs:
         hs = [int(x['H']>0) for x in gs]
         bbs = [int(x['BB']>0) for x in gs]
         asss = [int(x['ASS']>0) for x in gs]
         hrs =  [int(x['HR']>0) for x in gs]
         sbss =  [int(x['SB']>0) for x in gs]
         dates =  [x['date'] for x in gs]
         team_h = team_h + getLongestStreak(hs,onlyLatest)
         team_bb = team_bb + getLongestStreak(bbs,onlyLatest)
         team_ass = team_ass + getLongestStreak(asss,onlyLatest)
         for d,hhh in zip(dates,hrs):
            team_hr = addUpdate(team_hr,d,hhh)
         for d,sss in zip(dates,sbss):
            team_sb = addUpdate(team_sb,d,sss)
   shr = [x for x in team_hr.iteritems()]
   shr.sort(key=lambda x: x[0])
   team_hr_streak = getLongestStreak([x[1] for x in shr],onlyLatest)
   ssb = [x for x in team_sb.iteritems()]
   ssb.sort(key=lambda x: x[0])
   team_sb_streak = getLongestStreak([x[1] for x in ssb],onlyLatest)
   tscore['H']=team_h
   tscore['ASS']=team_ass
   tscore['BB']=team_bb
   tscore['HR'] = team_hr_streak
   tscore['SB'] = team_sb_streak

   for b in t['pitchers']:
      gs = getGamesForPlayer(b['id'])
      if gs:
         qss = [int(x['QS']>0) for x in gs]
         dps = [int(x['DP']>0) for x in gs]
         ers = [int(x['ER']<1) for x in gs]
         ws =  [int(x['W']>0) for x in gs]
         svs =  [int(x['SV']>0) for x in gs]
         dates =  [x['date'] for x in gs]
         team_qs = team_qs + getLongestStreak(qss,onlyLatest)
         team_dp = team_dp + getLongestStreak(dps,onlyLatest)
         team_er = team_er + getLongestStreak(ers,onlyLatest)
         for d,www in zip(dates,ws):
            team_w = addUpdate(team_w,d,www)
         for d,sss in zip(dates,svs):
            team_sv = addUpdate(team_sv,d,sss)
   sw = [x for x in team_w.iteritems()]
   sw.sort(key=lambda x: x[0])
   team_w_streak = getLongestStreak([x[1] for x in sw],onlyLatest)
   ssv = [x for x in team_sv.iteritems()]
   ssv.sort(key=lambda x: x[0])
   team_sv_streak = getLongestStreak([x[1] for x in ssv],onlyLatest)
   tscore['QS'] = team_qs
   tscore['DP'] = team_dp
   tscore['ER'] = team_er
   tscore['W'] = team_w_streak
   tscore['SV'] = team_sv_streak
   tscore['team_name_streak'] = team_name_streak
   
   return tscore

def printTeamToCSV(t,file,first):
   tname = t['team_name']
   for b in t['batters']:
      gs = getGamesForPlayer(b['id'])
      if gs:
         for g in gs:
            g['team'] = t['team_name']
            g['first_name'] = b['name'][1]
            g['last_name'] = b['name'][0]
            printGameToCSV(file, g,first)
            first = 0
   for b in t['pitchers']:
      gs = getGamesForPlayer(b['id'])
      if gs:
         for g in gs:
            g['team'] = t['team_name']
            g['first_name'] = b['name'][1]
            g['last_name'] = b['name'][0]
            printGameToCSV(file, g,first)
            first = 0

#Use this to print out team CSV   
def printTeamsCSV(file):
   f = open(file,'wb') 
   teams = getTeams()
   first = 1
   for t in teams:
      printTeamToCSV(t,f,first)
      first = 0
   f.close()

def printTeamScores():
   teams = getTeams()
   for t in teams:
      ts = teamScore(t)
      print ts
      
def getTeamScores(onlyLatest=False):
   teams = getTeams()
   tscores = []
   for t in teams:
      dts = teamScore(t,onlyLatest)
      dts['team_name'] = t['team_name']
      tscores.append(dts)
   return tscores


def scoreVector(v):
   res = [0 for x in v]
   i=0
   for x in v:
      res[i] = 0.5+ sum( [float(x > y) for y in v]) + 0.5*sum([float(x==y) for y in v])
      i = i+1
   return res

def scoreSingle(v,i):
   x = v[i]
   res = 0.5+ sum( [float(x > y) for y in v]) + 0.5*sum([float(x==y) for y in v])
   return res

def getVictoryPoints(ts):
   #return a list of dictonaries with the season-point scores
   #Total Bases, Runs, SB, SF + SH, BB; 
   #Quality Starts, x Runs Allowed, Saves, Holds, x Strikeouts
   fnames_for_scoring = ['team','tb','runs','sb','sacsf','bb','qs','runs-a','saves','holds','so','total']
   tsc = copy.deepcopy(ts)
   vsc = []
   for tsii in tsc:
      tsii['total'] = tsii['salary']
   for lab  in fnames_for_scoring[1:len(fnames_for_scoring)-1]:
      nteams = len(tsc)
      for tt in range(0,nteams):
         dascore = scoreSingle([x[lab] for x in ts],tt)
         tsc[tt][lab] = dascore
         tsc[tt]['total'] = tsc[tt]['total'] + dascore
   return tsc

def lookupPlayer(lastname,players):
   pls = [x for x in players.values() if x['last']==lastname]
   for p in pls:
      print p['boxname'] + ' ' + p['id']

def getID(player):
   #player is a list with [lastname,firstname]
   #print player
   #print "in getID, player is " + player[1] +','+player[0]
   db = MySQLdb.connect(user='root',passwd='andnotbut',db='gameday')
   cursor = db.cursor()
   rt = cursor.execute("select id from player where first_name='"+player[1]+"' and last_name='"+player[0]+"'")
   res = cursor.fetchone()
   try:
      return(int(res[0]))
   except:
      print "error -- can't find player " + str(player)

def makeTeamDict(tname,hit_teams,pit_teams,offset,m1,m2):
   dd = {}
   dd['team_name'] = tname
   dd['hit_teams'] = hit_teams
   dd['pit_teams'] = pit_teams
   dd['salary'] = offset
   dd['m1'] = m1
   dd['m2'] = m2
   dd['mtotal'] = m1+m2
   return dd

def extractTeam(team,label,ts):
   matches = [x['team_name'] for x in ts if team in x[label]]
   if len(matches) > 0:
      return matches[0]
   else:
      return ''


def getFilledTeams(date1,date2):
   ts = getTeams()
   ress = CompileRangeGames(date1,date2)
   for t in ts:
      #Total Bases, Runs, SB, SF + SH, BB; 
      #Quality Starts, x Runs Allowed, Saves, Holds, x Strikeouts
      mysum=lambda teams,label:sum([x[label] for x in ress if x['team'] in teams])
      print t
      t['tb'] = mysum(t['hit_teams'],'tb')
      t['runs'] = mysum(t['hit_teams'],'runs_for')
      t['sb'] = mysum(t['hit_teams'],'sb')
      t['sacsf'] = mysum(t['hit_teams'],'sacsf')
      t['bb'] = mysum(t['hit_teams'],'bb')
      t['qs'] = mysum(t['pit_teams'],'qs')
      t['runs-a'] = -mysum(t['pit_teams'],'runs_against')
      t['saves'] = mysum(t['pit_teams'],'saves')
      t['holds'] = mysum(t['pit_teams'],'holds')
      t['so'] = mysum(t['pit_teams'],'so')
   for r in ress:
      r['batting_team'] = extractTeam(r['team'],'hit_teams',ts)
      r['pitching_team'] = extractTeam(r['team'],'pit_teams',ts)
   return ts,ress


def getTeamsJune():
   ts = [];
   team_names = ['Detroit Noojies (aka dbags)','No-Talent Ass Clowns', 'Portlandia Misfits', 'The Rube', 'Paly Players', 'Dr. Watson', 'Buena Vista Bottoms', 'Damnedest of the Nice']
   #def makeTeamDict(tname,hit_teams,pit_teams,m1,m2):

   ts.append(makeTeamDict(team_names[0],['chn','cin','lan'],['cle','mil','was'],-4,4,4))
   ts.append(makeTeamDict(team_names[1],['ari','mil','sdn'],['cha','ana','sln'],0,5.5,1))
   ts.append(makeTeamDict(team_names[2],['col','hou','sfn'],['chn','nya','sfn'],-4,5.5,4))
   ts.append(makeTeamDict(team_names[3],['mia','oak','was'],['cin','pit','sea'],4,3,2))
   ts.append(makeTeamDict(team_names[4],['kca','pit','sln'],['hou','kca','tex'],0,1,6))
   ts.append(makeTeamDict(team_names[5],['bos','cle','tba'],['ari','nyn','sdn'],-4,7,7.5))
   ts.append(makeTeamDict(team_names[6],['det','min','tor'],['lan','mia','oak'],0,2,4))
   ts.append(makeTeamDict(team_names[7],['atl','bal','tex'],['atl','det','tba'],0,8,7.5))
   return ts

           
def getTeamsMay():
   ts = [];
   team_names = ['Detroit Noojies (aka dbags)','No-Talent Ass Clowns', 'Portlandia Misfits', 'The Rube', 'Paly Players', 'Dr. Watson', 'Buena Vista Bottoms', 'Damnedest of the Nice']
   ts.append(makeTeamDict(team_names[0],'13','2392','2889',4))
   ts.append(makeTeamDict(team_names[1],'4169','3312','5',5.5))
   ts.append(makeTeamDict(team_names[2],'680','15','2680',5.5))
   ts.append(makeTeamDict(team_names[3],'14','10','17',3))
   ts.append(makeTeamDict(team_names[4],'16','2602','3313',1))
   ts.append(makeTeamDict(team_names[5],'2','7','32',7))
   ts.append(makeTeamDict(team_names[6],'4','19','2394',2))
   ts.append(makeTeamDict(team_names[7],'12','2681','3309',8))
   return ts

def getTeams():
    team_names = ['Detroit Tednugents','No-Talent Ass Clowns', 'Portlandia Misfits', 'The Rube', 'Paly Players', 'Dr. Watson', 'Buena Vista Bottoms', 'Damnedest of the Nice']

    players = pickle.load(open('players_wb4m4.p','rb'))

    pitchers = [];
    pitchers.append([519293,543243,477132,431148,447714,519267])#brad
    pitchers.append([502042,453329,489265,453562,544931,425844])#brent
    pitchers.append([434628,450212,429717,502188,453286,430935])#scott
    pitchers.append([446372,434538,425657,519242,517593,456501])#John
    pitchers.append([518813,471911,453343,461833,519455,518886])#jesse
    pitchers.append([518516,434378,453178,502202,571666,605476])#dave
    pitchers.append([453265,433587,518774,547888,452657,448306])#martin
    pitchers.append([572971,543037,547973,594798,605228,456034])#tom


    batters = [];
    batters.append([460026,452252,543401,133380,593428,453568,545361,519184,457803])#brad
    batters.append([457763,502671,622110,592178,493351,488726,430945,571740,624577])#brent
    batters.append([519390,519203,514888,453943,407908,502110,458731,456715,572821])#scott
    batters.append([431145,458015,450314,571448,543063,461314,542303,547180,592518])#john
    batters.append([452095,408236,429664,518626,408314,457705,443558,457708,405395])#jesse
    batters.append([501647,425902,543829,134181,453064,460075,460576,493316,467055])#dave
    batters.append([518960,408234,543281,630111,434670,605141,466320,471865,120074])#martin
    batters.append([435263,547989,605412,121347,543760,516782,430832,453056,429665])#tom

    teams = []
    i=0
    for team_name in team_names:
       fbs = [];
       fps = [];
       for b in batters[i]:
          player = players[str(b)]
          fbs.append({'name':player['name'],'id':b})
       for p in pitchers[i]:
          player = players[str(p)]
          fps.append({'name':player['name'],'id':p})
       teams.append({'team_name':team_name, 'batters':fbs, 'pitchers':fps})
       i=i+1
    return teams

def printTeams():
   teams = getTeams()
   for team in teams:
      print 'Team name is ' + team['team_name']
      for batter in team['batters']:
         print 'Batter: ' + batter['name'] + ' id: ' + str(batter['id'])
      for pitcher in team['pitchers']:
         print 'Pitcher: ' + pitcher['name'] + ' id: ' + str(pitcher['id'])
         
def SetFieldNames():
   """returns the list of fieldnames for the dictwriter"""
   return ['gameid', 'away_team', 'home_team', 'inningnum', 'score', 'away_team_runs', 'home_team_runs', 'next', 'num', 'b', 's', 'o', 'start_tfs', 'start_tfs_zulu', 'batter', 'battingteam', 'stand', 'b_height', 'pitcher', 'p_throws', 'playdes', 'esplaydes', 'event', 'des', 'des_es', 'id', 'on_1b', 'on_2b', 'on_3b', 'type', 'tfs', 'tfs_zulu', 'x', 'y', 'sv_id', 'start_speed', 'end_speed', 'sz_top', 'sz_bot', 'pfx_x', 'pfx_z', 'px', 'pz', 'x0', 'y0', 'z0', 'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az', 'break_y', 'break_angle', 'break_length', 'pitch_type', 'type_confidence', 'zone', 'nasty', 'spin_dir', 'spin_rate', 'cc', 'mt']

def CreateWriter(file):
   """takes an open, writable CSV file, creates a dict writer for parse games function"""   
   fieldnames = SetFieldNames()
   return csv.DictWriter(file, delimiter = ',', fieldnames = fieldnames)  

def GetGamePlayers(gameid):
   """Takes MLB gameid string, returns an elementtree object containing all players"""
   year, month, day = gameid[0:4], gameid[5:7], gameid[8:10] #extract date info from the gameid string
   baseURL = 'http://gd2.mlb.com/components/game/mlb/year_' #set URL beginning
   fullURL = baseURL + year + '/month_' + month + '/day_' + day + '/gid_' + gameid + '/players.xml' #construct full URL for the players XML file
   try:
      return ET.parse(urllib2.urlopen(fullURL)) # Tries to return the parsed game element from the XML file if the URL can be opened. If it can't 
   except:                                      # (this only is the case for some extra 2012 Marlins gameids as far as I know), returns none
      return None                               #
   
def GetGameBox(gameid):
   """Takes MLB gameid string, returns an elementtree object containing all game events"""
   year, month, day = gameid[0:4], gameid[5:7], gameid[8:10] #extract date info from the gameid string
   baseURL = 'http://gd2.mlb.com/components/game/mlb/year_' #set URL beginning
   fullURL = baseURL + year + '/month_' + month + '/day_' + day + '/gid_' + gameid + '/rawboxscore.xml' #construct full URL for the game event XML file
   try:
      return ET.parse(urllib2.urlopen(fullURL)) # Tries to return the parsed game element from the XML file if the URL can be opened. If it can't 
   except:                                      # (this only is the case for some extra 2012 Marlins gameids as far as I know), returns none
      return None                               #
      
def GetGame(gameid):
   """Takes MLB gameid string, returns an elementtree object containing all game events"""
   year, month, day = gameid[0:4], gameid[5:7], gameid[8:10] #extract date info from the gameid string
   baseURL = 'http://gd2.mlb.com/components/game/mlb/year_' #set URL beginning
   fullURL = baseURL + year + '/month_' + month + '/day_' + day + '/gid_' + gameid + '/inning/inning_all.xml' #construct full URL for the game event XML file
   try:
      return ET.parse(urllib2.urlopen(fullURL)) # Tries to return the parsed game element from the XML file if the URL can be opened. If it can't 
   except:                                      # (this only is the case for some extra 2012 Marlins gameids as far as I know), returns none
      return None                               #

def GetGameEvents(gameid):
   """Takes MLB gameid string, returns an elementtree object containing all game events"""
   year, month, day = gameid[0:4], gameid[5:7], gameid[8:10] #extract date info from the gameid string
   baseURL = 'http://gd2.mlb.com/components/game/mlb/year_' #set URL beginning
   fullURL = baseURL + year + '/month_' + month + '/day_' + day + '/gid_' + gameid + '/game_events.xml' #construct full URL for the game event XML file
   try:
      return ET.parse(urllib2.urlopen(fullURL)) # Tries to return the parsed game element from the XML file if the URL can be opened. If it can't 
   except:                                      # (this only is the case for some extra 2012 Marlins gameids as far as I know), returns none
      return None                               #

#HR- gettable from boxcar json, a bit tricky...
#Triples - gettable from json, a bit tricky
#Game time, boxscore json (time) [ might be confused by multi-day games? ] 
#LOB -- can get from boxscore, a bit ugly...
#Attendance, boxscore json
# Temperature, boxscore json, weather

def GetGameBoxScoreJson(gameid):
   """Takes MLB gameid string, returns an elementtree object containing all game events"""
   year, month, day = gameid[0:4], gameid[5:7], gameid[8:10] #extract date info from the gameid string
   baseURL = 'http://gd2.mlb.com/components/game/mlb/year_' #set URL beginning
   fullURL = baseURL + year + '/month_' + month + '/day_' + day + '/gid_' + gameid + '/boxscore.json' #construct full URL for the game event XML file
   try:
      page = urllib2.urlopen(fullURL)
      data = page.read()
      jdata = json.loads(data)
      return jdata
   except:                                      # (this only is the case for some extra 2012 Marlins gameids as far as I know), returns none
      return None                               #


#
def ExtractTeamRecords(dd):
   """Takes json dictionary of all boxscore, returns relevant stuff"""
   retval = [];
   badval = [];
   res = {}
   resH = {};
   resA = {};
   try:
      resH['team'] = dd['data']['boxscore']['home_team_code']
      resH['runs_for'] = int(dd['data']['boxscore']['linescore']['home_team_runs'])
      resH['runs_against'] = int(dd['data']['boxscore']['linescore']['away_team_runs'])
      resH['game_id'] = dd['data']['boxscore']['game_id']

      resA['team'] = dd['data']['boxscore']['away_team_code']
      resA['runs_for'] = int(dd['data']['boxscore']['linescore']['away_team_runs'])
      resA['runs_against'] = int(dd['data']['boxscore']['linescore']['home_team_runs'])
      resA['game_id'] = dd['data']['boxscore']['game_id']

      bats = dd['data']['boxscore']['batting']
      bh = [b for b in bats if b['team_flag']=='home']
      ba = [b for b in bats if b['team_flag']=='away']

      resH['bb'] = bh[0]['bb']
      resA['bb'] = ba[0]['bb']
      
      pits = dd['data']['boxscore']['pitching']
      ph = [p for p in pits if p['team_flag']=='home']
      pa = [p for p in pits if p['team_flag']=='away']

      resH['so'] = int(ph[0]['so'])
      resA['so'] = int(pa[0]['so'])

      #Total Bases, Runs, SB, SF + SH, BB; 
      bh_list = bh[0]['batter']
      ba_list = ba[0]['batter']
      resH['hr'] = sum([int(x['hr']) for x in bh_list])
      resA['hr'] = sum([int(x['hr']) for x in ba_list])
      resH['t'] = sum([int(x['t']) for x in bh_list])
      resA['t'] = sum([int(x['t']) for x in ba_list])
      resH['d'] = sum([int(x['d']) for x in bh_list])
      resA['d'] = sum([int(x['d']) for x in ba_list])
      resH['h'] = sum([int(x['h']) for x in bh_list])
      resA['h'] = sum([int(x['h']) for x in ba_list])
      resH['tb'] = resH['h'] + resH['hr']*3 + resH['t']*2 + resH['d']
      resA['tb'] = resA['h'] + resA['hr']*3 + resA['t']*2 + resA['d']
      resH['sac'] = sum([int(x['sac']) for x in bh_list])
      resA['sac'] = sum([int(x['sac']) for x in ba_list])
      resH['sf'] = sum([int(x['sf']) for x in bh_list])
      resA['sf'] = sum([int(x['sf']) for x in ba_list])
      resH['sacsf'] = int(resH['sac']) + int(resH['sf'])
      resA['sacsf'] = int(resA['sac']) + int(resA['sf'])
      resH['bb'] = sum([int(x['bb']) for x in bh_list])
      resA['bb'] = sum([int(x['bb']) for x in ba_list])
      resH['sb'] = sum([int(x['sb']) for x in bh_list])
      resA['sb'] = sum([int(x['sb']) for x in ba_list])

      #Total Bases, Runs, SB, SF + SH, BB; 
      #Quality Starts, x Runs Allowed, Saves, Holds, x Strikeouts
      ph_list = ph[0]['pitcher']      
      pa_list = pa[0]['pitcher']      

      if isinstance(pa_list,(dict)):
         pa_list = [pa_list]
      if isinstance(ph_list,(dict)):
         ph_list = [ph_list]
      
      resH['saves'] = len([s for s in ph_list if 'save' in s.keys()])
      resA['saves'] = len([s for s in pa_list if 'save' in s.keys()])

      #ok, futzing....
      notesH = [p['note'] for p in ph_list if 'note' in p.keys()]
      notesA = [p['note'] for p in pa_list if 'note' in p.keys()]

      resH['holds'] = len([x for x in notesH if '(H' in x])
      resA['holds'] = len([x for x in notesA if '(H' in x])

      outsH = int(ph_list[0]['out'])
      outsA = int(pa_list[0]['out'])

      erH = int(ph_list[0]['er'])
      erA = int(pa_list[0]['er'])

      if erH <= 3 and outsH >= 18:
         resH['qs'] = 1
      else:
         resH['qs'] = 0
         
      if erA <= 3 and outsA >= 18:
         resA['qs'] = 1
      else:
         resA['qs'] = 0

   except:
      print 'no data yet'
      print resH
      print resA
      fres = res
      res = {}
      #pdb.set_trace()
      resH = {}
      resA = {}
      
   if (len(resH) > 0):
      retval.append(resH)      
   if (len(resA) > 0):
      retval.append(resA)      
   return retval

      
def TodaysGames():
   """Returns a list of gameids corresponding to games on the current date"""
#   today = datetime.date.today().__str__()
   today = date.today().__str__()
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

def AddBatterToDB(bb,g,date,gb):
   #Get the stuff out of bb
   global cursor
   global db
   
   date = date;
   player = int(bb.attrib['id'])
   gamekey = g
   pitcherp = 0
   status = gb.findall(".")[0].attrib['status_ind']
   W = 0
   SV = 0
   QS = 0
   DP = 0
   ER = 0
   H = bb.attrib['h']
   HR = bb.attrib['hr']
   BB = bb.attrib['bb']
   ASS = bb.attrib['a']
   SB = bb.attrib['sb']
   foo = cursor.execute("select id from info where gamekey='%s' and player=%s"%(gamekey,str(player)))
   all_res = cursor.fetchall()
   if len(all_res) > 0:
      #use alter
      id = int(all_res[0][0])
      querystr = "REPLACE into info (id, date, player,gamekey,pitcherp,status,W,SV,QS,DP,ER,H,HR,BB,ASS,SB) values (%s, '%s', %s, '%s', %s, '%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"%(str(id),date,str(player),gamekey,str(pitcherp),str(status),str(W),str(SV),str(QS),str(DP),str(ER),str(H),str(HR),str(BB),str(ASS),str(SB))
      #print querystr
      cursor.execute(querystr)
   else:
      #use insert
      querystr = "INSERT into info (date, player,gamekey,pitcherp,status,W,SV,QS,DP,ER,H,HR,BB,ASS,SB) values ('%s', %s, '%s', %s, '%s',%s,%s,%s,%s,%s,%s,%s,%s,%s, %s)"% (date,str(player),gamekey,str(pitcherp),str(status),str(W),str(SV),str(QS),str(DP),str(ER),str(H),str(HR),str(BB),str(ASS),str(SB))
      #print querystr
      #print type(querystr)
      cursor.execute(querystr)
      db.commit()

def AddPitcherToDB(pp,g,date,gb):
   #Get the stuff out of pp
   global cursor
   global db
   
   date = date;
   player = int(pp.attrib['id'])
   gamekey = g
   pitcherp = 1
   status = gb.findall(".")[0].attrib['status_ind']
   if ('win' in pp.attrib.keys()):
      W = 1
   else:
      W = 0
   if ('save' in pp.attrib.keys()):
      SV = 1
   else:
      SV = 0
   outs = pp.attrib['out']
   ER = pp.attrib['er']
   #print "outs %s, ER %s"%(str(outs),str(ER))
   #print "type of outs is " + str(type(outs))
   #print "type of ER is " + str(type(ER))
   DP = 0
   if int(outs) >= 18 and int(ER) <=3:
      QS = 1
      #print 'should be qs'
   else:
      QS = 0
      #print 'should not be qs'      
   H = 0
   HR = 0
   BB = 0
   ASS = 0
   SB = 0
   foo = cursor.execute("select id from info where gamekey='%s' and player=%s"%(gamekey,str(player)))
   all_res = cursor.fetchall()
   if len(all_res) > 0:
      #use replace
      id = int(all_res[0][0])
      querystr = "REPLACE into info (id, date, player,gamekey,pitcherp,status,W,SV,QS,DP,ER,H,HR,BB,ASS,SB) values (%s, '%s', %s, '%s', %s, '%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"%(str(id),date,str(player),gamekey,str(pitcherp),str(status),str(W),str(SV),str(QS),str(DP),str(ER),str(H),str(HR),str(BB),str(ASS),str(SB))
      #print querystr
      cursor.execute(querystr)
   else:
      #use insert
      querystr = "INSERT into info (date, player,gamekey,pitcherp,status,W,SV,QS,DP,ER,H,HR,BB,ASS,SB) values ('%s', %s, '%s', %s, '%s',%s,%s,%s,%s,%s,%s,%s,%s,%s, %s)"% (date,str(player),gamekey,str(pitcherp),str(status),str(W),str(SV),str(QS),str(DP),str(ER),str(H),str(HR),str(BB),str(ASS),str(SB))
      #print querystr
      #print type(querystr)
      cursor.execute(querystr)
      db.commit()

def AddAtBatToDB(ab,g,date):
   global cursor
   global db
   pp = ab.attrib['pitcher']
   querystr = "select id,DP from info where gamekey = '%s' and player = %s"%(g,str(pp))
   #print querystr
   cursor.execute(querystr)
   ress = cursor.fetchall()
   if len(ress) < 1 or len(ress) > 1:
      print 'ERROR in atbat'
   else:
      sqlid = ress[0][0]
      DP  = ress[0][1]
      DP = DP + 1
      querystr = "update info set DP=%s where id=%s"%(str(DP),str(sqlid))
      #print querystr
      cursor.execute(querystr)
      db.commit()

   
def AddGameToDB(g,date):
   ge = GetGameEvents(g)
   gb = GetGameBox(g)
   if (gb != None and ge != None):
      batters = gb.findall('.//batter')
      pitchers = gb.findall('.//pitcher')
      for bb in batters:
         AddBatterToDB(bb,g,date,gb)
         for pp in pitchers:
            AddPitcherToDB(pp,g,date,gb)
         atbats = ge.findall(".//atbat[@event='Double Play']")
         w2 = ge.findall(".//atbat[@event='Grounded Into DP']")
         for a in w2:
            atbats.append(a)
         w3 = ge.findall(".//atbat[@event='Triple Play']")
         for a in w3:
            atbats.append(a)      
         for ab in atbats:
            AddAtBatToDB(ab,g,date)

def printDictList(ff, dlist, cols=None):
   if cols is None:
      cols = dlist[0].keys
   #printheader
   ff.write('<table><tr>')
   for c in cols:
      ff.write('<th>%s</th>'%(c))
   ff.write('\n</tr>')
   #now write the data
   for r in dlist:
      ff.write('<tr>')
      for c in cols:
         ff.write('<td>%s</td>'%(r[c]))
      ff.write('</tr>\n')
   ff.write('</table>')
   ff.flush()

def printDictListCSV(ff, dlist, cols=None):
   if cols is None:
      cols = dlist[0].keys()
   #printheader
   for c in cols:
      ff.write('%s,'%(c))
   ff.write('\n')
   #now write the data
   for r in dlist:
      for c in cols:
         ff.write('%s,'%(r[c]))
      ff.write('\n')
   ff.flush()


def OutputTablesToFile(filename,ts,tsToday,ress):
   tls = ts
   vps = getVictoryPoints(ts)
   svps = sorted(vps,key=lambda k: k['total'],reverse=True)
   sts = [x for (x,y) in sorted(zip(ts,vps),key=lambda k: k[1]['total'],reverse=True)]   
   stsToday = [x for (x,y) in sorted(zip(tsToday,vps),key=lambda k: k[1]['total'],reverse=True)]

   ii = 0
   for svi in svps:
      m3s = scoreSingle([x['total'] for x in svps],ii)      
      svi['through_three'] = svi['mtotal'] + m3s
      svi['m3'] = m3s
      ii = ii+1
   ff = open(filename,'wb')
   #   ff.write('teams<br>')
   #   printDictList(ff,sts,['team_name','runs_for_team','runs_against_team','error_team'])
   #   ff.flush()
   ff.write('<BR><BR>Stats<BR>')
   printDictList(ff,sts,['team_name','tb','runs','sb','sacsf','bb','qs','runs-a','saves','holds','so','salary'])
   ff.flush()
   ff.write('<BR><BR>Points<BR>')
   printDictList(ff,svps,['team_name','tb','runs','sb','sacsf','bb','qs','runs-a','saves','holds','so','total'])
   ff.write('<BR><BR>Today Stats<BR>')
   printDictList(ff,stsToday,['team_name','tb','runs','sb','sacsf','bb','qs','runs-a','saves','holds','so'])

   ff.write('<BR><BR>Season scores As of Today:<BR>')

   ssvps = sorted(svps,key=lambda k: k['through_three'],reverse=True)
   printDictList(ff,ssvps,['team_name','m1','m2','m3','through_three'])
   ff.write('<BR><BR>')
   ff.write("<a href='all.csv'> all.csv </a><BR><BR>")

   ff.write(str(datetime.now()))

   ff.close()
   ff = open('/home/eddie7/code/wb4m3/all.csv','wb')
   printDictListCSV(ff,ress,['team','game_id','runs_for','h','d','t','hr','tb','bb','sb','sac','sf','sacsf','runs_against','qs','so','saves','holds','batting_team','pitching_team'])
#   printDictListCSV(ff,ress)
   ff.close()


def d2s(d):
   return datetime.strftime(d,'%Y_%m_%d')


def DoTheDay():
   today = datetime.now()
   today = today.date()
   start_date = date(2015,1,1)
   end_date = date(2015,7,1)
   end_date = min(end_date,today)
   ts,ress = getFilledTeams(d2s(start_date),d2s(end_date))
   tsToday,rignore = getFilledTeams(d2s(end_date),d2s(end_date))
   OutputTablesToFile('/home/eddie7/code/wb4m3/stats_wb4m3.html',ts,tsToday,ress)

def ExtractPlayers(gg,pdict):
   try:
      root= gg.getroot()
   except:
      return []
   players = [pyr for pyr in root.iter('player')]   
   new_players = [p for p in players if p.attrib['id'] not in pdict]
   for p in new_players:
      pd = p.attrib
      subd = {'id':pd['id'], 'first':pd['first'],'last':pd['last'],'boxname':pd['boxname'], 'name':pd['first']+' '+pd['last']}
      pdict[pd['id']] = subd
      #pdict[subd['name']] = subd

def ExtractEvents(gg):
   try:
      root= gg.getroot()
   except:
      return []
   atbats = [atbat for atbat in root.iter('atbat')]
   events = [ab.attrib['event'] for ab in atbats]
   return events

def GetDayPlayers(date,pdict):
   gameids = DateGames(date)
   for g in gameids:
      print 'Doing game ' + g
      ExtractPlayers(GetGamePlayers(g),pdict)

def GetDayEvents(date):
   c = collections.Counter()
   gameids = DateGames(date)
   for g in gameids:
      print 'Doing game ' + g
      dinfo = ExtractEvents(GetGame(g))
      if 'Runner Out' in dinfo:
         print 'Found Runner Out in ' + g
      if 'Catcher Interference' in dinfo:
         print 'Found Runner Out in ' + g
      if (len(dinfo) >0):
         c.update(dinfo)
   return c

def CompileDayGames(date):
   res = []
   badres = []
   gameids = DateGames(date)
   for g in gameids:
      print 'Doing game ' + g
      dinfo = ExtractTeamRecords(GetGameBoxScoreJson(g))
      if (len(dinfo) >0):
         res.extend(dinfo)
   return res

def DayGamesToDB(date):
   gameids = DateGames(date)
   for g in gameids:
      print 'Doing game ' + g
      if not(g == '2014_07_15_nasmlb_aasmlb_1'):
         AddGameToDB(g,date)
         print 'Added game ' + g

#Call RangeGamesToDB('2014_07_01','2014_07_13') to update the DB
def RangeGamesToDB(date1,date2):
   pdate1 = datetime.strptime(date1,'%Y_%m_%d').date()
   pdate2 = datetime.strptime(date2,'%Y_%m_%d').date()
   if pdate2 <= pdate1:
      raise Exception('date2 must be after date1')
   oneday = timedelta(1)
   thedate = pdate1
   while thedate <=pdate2:
      print 'Doing games for date ' + str(thedate)
      DayGamesToDB(thedate.strftime('%Y_%m_%d'))
      thedate = thedate+oneday

def GetThePlayers(date1,date2):
   pdate1 = datetime.strptime(date1,'%Y_%m_%d').date()
   pdate2 = datetime.strptime(date2,'%Y_%m_%d').date()
   if pdate2 < pdate1:
      raise Exception('date2 must be at or after date1')
   oneday = timedelta(1)
   thedate = pdate1
   res = {}
   while thedate <=pdate2:
      print 'Doing games for date ' + str(thedate)
      GetDayPlayers(thedate.strftime('%Y_%m_%d'),res)
      thedate = thedate+oneday
   return res

def GetTheEvents(date1,date2):
   pdate1 = datetime.strptime(date1,'%Y_%m_%d').date()
   pdate2 = datetime.strptime(date2,'%Y_%m_%d').date()
   if pdate2 < pdate1:
      raise Exception('date2 must be at or after date1')
   oneday = timedelta(1)
   thedate = pdate1
   res = collections.Counter()
   while thedate <=pdate2:
      print 'Doing games for date ' + str(thedate)
      events = GetDayEvents(thedate.strftime('%Y_%m_%d'))
      res.update(events)
      thedate = thedate+oneday
   return res
   

def CompileRangeGames(date1,date2):
   res = []
   badres = []
   while thedate <=pdate2:
      print 'Doing games for date ' + str(thedate)
      thetup = CompileDayGames(thedate.strftime('%Y_%m_%d'))
      res.extend(thetup)
      thedate = thedate+oneday
   return res

def PrintMonth():
    print 'Rangers,Reds,Rockies,Rays,Tigers,Brewers,Orioles,Indians,Giants,Braves,Pirates,BlueJays,RedSox,Mets,Cardinals,Yankees,'
    teamlist = ['tex','cin','col','tba','det','mil','bal','cle','sfn','atl','pit','tor','bos','nyn','sln','nya']
    today= date.today();
    
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

