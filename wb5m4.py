#!/usr/bin/python
import urllib
import urllib2
import xml.etree.ElementTree as ET
import datetime
from bs4 import BeautifulSoup
import re
import time
from datetime import date
from datetime import timedelta
from datetime import datetime
import string
import collections
import copy
import pdb
import sys
import traceback
from gd2functions import *
from wbhelpers import *
import os.path

codehome = "/home/eddie7/code/"
#codehome = "/Users/martin/Baseball/WhiskeyBall/Code/"
monthfolder = "wb5m4/"

def getVictoryPoints(ts):
   #return a list of dictonaries with the season-point scores
   #PA, BB%-K%, wOBA, wSB
   #IP, K%-BB%, FIP, LOB%

   cats = makeScoringNames(10)
   fnames_for_scoring = ['team']
   fnames_for_scoring.extend(cats)
   fnames_for_scoring.append('total')   

   tsc = copy.deepcopy(ts)
   vsc = []
   for tsii in tsc:
      tsii['total'] = 0
   for lab in fnames_for_scoring[1:len(fnames_for_scoring)-1]:
      nteams = len(tsc)
      for tt in range(0,nteams):
         dascore = scoreSingle([x[lab] for x in ts],tt)
         tsc[tt][lab] = dascore
         tsc[tt]['total'] = tsc[tt]['total'] + dascore
   return tsc
   
def GameInRange(gid,start,end):
    gamedate = gid[0:10]
    if gamedate >= start and gamedate <= end:
        return True
    return False

def pythag(r,ra):
   #1/(1+[runs allowed/runs scored]^2)   
   if r == 0:
      if ra == 0:
         return 0.5
      else:
         return 0
   else:
      return 1/(1+(float(ra)/float(r))**2)

def makeScoringNames(N):
   zinlist = ['inn'+str(i+1) for i in range(N)]
   zinlist[-1] = 'innX'
   return zinlist

def getFilledTeams(date1,date2):
   ts = getTeams()
   (ress) = CompileRangeGames(date1,date2) 
   labels = ['inning_runs','inning_runs_against']
   for t in ts:
      #print 'doing', t['team_name']
        
      zlist = range(0,10)
      zinlist = makeScoringNames(len(zlist))

      mysum=lambda team,label,idx,llist:sum([int(x[label][idx]) for x in llist if x['team'] == team])

      stats = {}

      #need to do the teams separately!!!
      # get player stats  
      i=0
      t['inning_recs'] = {}

      for tm in t['team_teams']:
         t['inning_recs'][tm] = {}
         myir = t['inning_recs'][tm]
         for lbl in labels:
            myir[lbl] = [mysum(tm,lbl,i,ress) for i in zlist]
         myir['pythag'] = [pythag(myir['inning_runs'][i],myir['inning_runs_against'][i]) for i in zlist]
      t['inning_recs']['joint'] = [t['inning_recs'][t['team_teams'][0]]['pythag'][i] + t['inning_recs'][t['team_teams'][1]]['pythag'][i] for i in zlist]
      for i in range(10):
         t[zinlist[i]] = t['inning_recs']['joint'][i]

   return ts,ress

def printTeamTeamInnings(ts,tm):
   print ts['team'] + ',' + tm + ',runs, ' + str(ts['inning_recs'][tm]['inning_runs'])
   print ts['team'] + ',' + tm + ',ra, ' + str(ts['inning_recs'][tm]['inning_runs_against'])
   print ts['team'] + ',' + tm + ',pythag, ' + str(ts['inning_recs'][tm]['pythag'])

def printTeamInnings(ts):
   printTeamTeamInnings(ts,ts['team_teams'][0])
   printTeamTeamInnings(ts,ts['team_teams'][1])

def printAllTeams(ts):
   for t in ts:
      printTeamInnings(t)

def printFilesForTeams(ts,press,bress):
   for t in ts:
      bff = open(codehome + monthfolder + t['team_name'].replace(" ","") + '_batters.csv','wb')
      pff = open(codehome + monthfolder + t['team_name'].replace(" ","") + '_pitchers.csv','wb')
      bre = getBattingRawEvents(bress,t)
      pre = getPitchingRawEvents(press,t)
      printDictListCSV(bff,bre)
      printDictListCSV(pff,pre)
      bff.close()
      pff.close()

def getTeams():
    team_names = ['Drumpfallacious','No-Talent Ass Clowns', 'Portlandia Misfits', 'The Rube', 'Paly Players', 'Dr. Watson', 'Buena Vista Bottoms', 'Damnedest of the Nice']

    hitting_team_teams = [['nya','sfn','nyn'],['tex','lan','mil'],['col','cin','sln'],['mia','hou','pit'],['oak','chn','ari'],['bos','sdn','det'],['bal','ana','kca'],['pit','atl','tor']]
    pitching_team_teams = [['was','ana','mia'],['min','lad','atl'],['sln','det','phi'],['cin','nya','oak'],['chn','kca','ari'],['bos','bal','tor'],['nyn','tba','pit'],['cle','col','sfn']]
    
    mscores = [[7,7,2.5],[3.5,8,1],[3.5,4,5],[5,5,7],[1,1,6],[2,3,4],[6,6,8],[8,2,2.5]]
    mtotal =  [sum(x) for x in mscores]

    teams = []
    i=0
    for team_name in team_names:
       teams.append({'team_name':team_name, 'team':team_name, 'hitting_team_teams':hitting_team_teams[i],'pitching_team_teams':pitching_team_teams[i], 'mscores':mscores[i], 'mtotal':mtotal[i]})
       i=i+1
    return teams

def CleanStats(sts):
   sns = makeScoringNames(10)
   for s in sts:
      for n in sns:
         s[n] = round(s[n] * 50,1)
   return sts

def OutputTablesToFile(filename,ts,ress):
   tls = ts
   vps = getVictoryPoints(ts)
   svps = sorted(vps,key=lambda k: k['total'],reverse=True)
   sts = [x for (x,y) in sorted(zip(ts,vps),key=lambda k: k[1]['total'],reverse=True)]   
   #stsToday = [x for (x,y) in sorted(zip(tsToday,vps),key=lambda k: k[1]['total'],reverse=True)]

   ii = 0
   for svi in svps:
      m3s = scoreSingle([x['total'] for x in svps],ii)      
      svi['through_three'] = svi['mtotal'] + m3s
      svi['m1'] = svi['mscores'][0]
      svi['m2'] = svi['mscores'][1]
      svi['m3'] = m3s
      ii = ii+1
   ff = open(filename,'wb')
   ff.write('<BR><BR>Stats<BR><tt>')
   cats = makeScoringNames(10)
   plist = ['team']
   plist.extend(cats)
   csts = CleanStats(sts)
   printDictList(ff,csts,plist) 
   ff.flush()
   ff.write('<BR><BR>Points<BR>')
   plist.append('total')
   printDictList(ff,svps,plist)

   ff.write('<BR><BR>Season scores As of Today:<BR>')

   ssvps = sorted(svps,key=lambda k: k['through_three'],reverse=True)
   printDictList(ff,ssvps,['team_name','m1','m2','m3','through_three'])
   ff.write('<BR><BR>')
   #ff.write("<a href='all.csv'> all.csv </a><BR><BR>")
   
   # provide links to all teams' batter and pitcher stat files
   #   ff.write("<a href='TheRube_pitchers.csv'> Rube pitchers </a><BR>")

   ff.write('<BR><BR>')
   ff.write('</tt>')
   ff.write(str(datetime.now()))

   ff.close()
   #printFilesForTeams(ts,press,bress)
   
   #ff = open(codehome + monthfolder + 'all.csv','wb')
   #printDictListCSV(ff,ress,['team','game_id','runs_for','h','d','t','hr','tb','bb','sb','sac','sf','sacsf','runs_against','qs','so','saves','holds','batting_team','pitching_team'])
   #printDictListCSV(ff,ress)
   #ff.close()
      
        
def getFullTeamName(teamcode):
    teamMapping = {'ana':'Angels', 'ari':'Diamondbacks', 'atl':'Braves', 'bal':'Orioles', 'bos':'Red Sox', 'cha':'White Sox',
                    'chn':'Cubs', 'cin':'Reds', 'cle':'Indians', 'col':'Rockies', 'det':'Tigers', 'hou':'Astros', 'kca':'Royals',
                    'lan':'Dodgers', 'mia':'Marlins', 'mil':'Brewers', 'min':'Twins', 'nya':'Yankees', 'nyn':'Mets', 'oak':'Athletics',
                    'phi':'Phillies', 'pit':'Pirates', 'sdn':'Padres', 'sea':'Mariners', 'sfn':'Giants', 'sln':'Cardinals', 'tba':'Rays',
                    'tex':'Rangers', 'tor':'Blue Jays', 'was':'Nationals'}
    return teamMapping[teamcode]
    
def myint(x):
   if x == 'x':
      return 0
   else:
      return int(x)

def getRuns(x,teamloc):
   try:
      rval = myint(x[teamloc])
   except:
      rval = 0
   return rval

def getInningRuns(teamloc, dd):
   try:
      retvec = [getRuns(x,teamloc) for x in dd['data']['boxscore']['linescore']['inning_line_score'] if int(x['inning']) < 10]
      extras = [getRuns(x,teamloc) for x in dd['data']['boxscore']['linescore']['inning_line_score'] if int(x['inning']) > 9]
      if len(retvec) < 9:
         retvec.extend([0]*9-len(retvec))

      if len(extras) > 0:
         retvec.append(sum(extras))
      else:
         retvec.append(0)
            
   except:
      retvec = [0]*10
   return retvec

def ExtractTeamRecords(dd):
   """Takes json dictionary of all boxscore, returns relevant stuff"""
   tgh = {}
   tga = {}
   res = None
   try:
      tgh['team'] = dd['data']['boxscore']['home_team_code']
      tga['team'] = dd['data']['boxscore']['away_team_code']

      tgh['game_id'] = dd['data']['boxscore']['game_id']
      tga['game_id'] = dd['data']['boxscore']['game_id']

      tgh['inning_runs'] = getInningRuns('home',dd)
      tgh['inning_runs_against'] = getInningRuns('away',dd)
      tga['inning_runs'] = getInningRuns('away',dd)
      tga['inning_runs_against'] = getInningRuns('home',dd)
      res = [tga,tgh]
   except:
      traceback.print_exc()
      print 'no data yet'
   return res

def parseWildPitches(tag):
   strs = tag.text.split(',')
   # so, first str IS a name, but might be a name/number pair
   # if so, name doesn't have a first name, so record it.
   # otherwise, look at next str to see if it's an initial or initial/number
   # if so, merge em and record, otherwise record with 1 WP
   # use a while loop?
   # HERE
   pitchers={};
   i=0;
   while i < len(strs):
      name_re = re.compile('[A-Za-z]*')
      name_nu_rem = re.compile('[A-Za-z]*\s*\d*')
      init = re.compile('\s*[A-Z]')
      init_num = re.compile('\s*[A-Z]\s*\d*')
      m = name_re.match(strs[i])
      if len(strs[i]) == m.end():
         #single name, no letter
         #must look at next name
         name_pre = m.group()
         nwp = 1
         if i+1 < len(strs):
            mi_n = init_num.match(strs[i+1])
            if not(mi_n is None): #we have init num
               pname = name_pre + strs[i+1][1]
               nwp = int(strs[i+1][3:])
               i +=1
            else:
               mi = init.match(strs[i+1])
               if not(mi is None) and mi.end() == len(strs[i+1]): 
                  pname = name_pre + strs[i+1][1]
                  i +=1
      else:
         #must have number and no next name
         m2 = name_nu_re.match(strs[i])
         pname = strs[i][0:m.end()]
         nwp = int(strs[i][m.end()+1:])
      pitchers[pname] = nwp
      i+=1
   return pitchers

def CompileDayGames(curdate):
   team_games = []

   gameids = DateGames(curdate)
   for g in gameids:
      print 'Doing game ' + g
      sys.stdout.flush()
      jsonbox = GetGameBoxScoreJson(g)
      if not jsonbox is None:
         trs = ExtractTeamRecords(jsonbox)
         if not trs is None:
            team_games.extend(trs)
            
   return (team_games)

def CompileRangeGames(date1,date2):
    res = []
    pdate1 = datetime.strptime(date1,'%Y_%m_%d').date()
    pdate2 = datetime.strptime(date2,'%Y_%m_%d').date()
    if pdate2 < pdate1:
        raise Exception('date2 must be at or after date1')
    oneday = timedelta(1)
    thedate = pdate1
    while thedate <= pdate2:
        print 'Doing games for date ' + str(thedate)
        sys.stdout.flush()
        (rs) = CompileDayGames(thedate.strftime('%Y_%m_%d'))
        if len(rs) > 0:
            res.extend(rs)
        thedate = thedate+oneday
    return (res)  

def DoTheDay():
    today = datetime.now()
    today = today.date()
    start_date = date(2016,6,7)
    end_date = date(2016,7,10)
    #end_date = date(2016,5,10)
    end_date = min(end_date,today)
    ts,ress = getFilledTeams(d2s(start_date),d2s(end_date))
    OutputTablesToFile(codehome + monthfolder + 'stats_wb5m3.html',ts,ress)
