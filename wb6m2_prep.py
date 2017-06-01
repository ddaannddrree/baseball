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
import pickle

codehome = "/home/eddie7/code/"
#codehome = "/Users/martin/Baseball/WhiskeyBall/Code/"
monthfolder = "wb6m2/"

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
   return ress

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

def makeFrame(stat,dates):
    return({'stat':stat,'dates':dates,'r1':None,'r2':None,'p1':None,'p2':None,'total':None})

def makeTeam(name,t1,t2,t3,t4,stats,m1,datelist):
    team = {'team':name,'bteams':[t1,t2],'pteams':[t3,t4],
            'frames':[makeFrame(s,dates) for s,dates in zip(stats,datelist[0:10])],'m1':m1}
    team['frames'][9]['r3'] = None
    team['frames'][9]['p3'] = None
    team['frames'][9]['extraDates'] = datelist[10]
    
    return team

def getTeams():
    #team_names = ['Drumpfallacious','No-Talent Ass Clowns', 'Portlandia Misfits', 'The Rube', 'Paly Players', 'Dr. Watson', 'Buena Vista Bottoms', 'Damnedest of the Nice']
    #players = loadCSVDict(codehome + 'players2016.csv')

    sd = date(2017,5,4)
    dlist = [[i*3+0,3*i+1,3*i+2] for i in range(0,10)]
    dlist.append([30,31])
    datelist = [[sd+timedelta(i) for i in frame] for frame in dlist]

    teams = [makeTeam('Drumpies','lan','hou','lad','bos',['H','W','R','D','SIP','K','BB','SB','GE','HR'],7,datelist),
             makeTeam('No-Talent Ass Clowns','mil','sea','bal','cle',['W','SIP','HR','BB','SB','K','GE','H','R','D'],3,datelist),
             makeTeam('Portlandia Misfits','was','sln','ana','sln',['BB','H','HR','D','GE','K','W','R','SB','SIP'],5,datelist),
             makeTeam('The Rube','ari','cin','sfn','nya',['HR','K','H','SB','R','D','SIP','W','BB','GE'],1,datelist),
             makeTeam('Paly Players','nyn','col','cha','tba',['K','W','HR','GE','R','SIP','D','SB','BB','H'],2,datelist),
             makeTeam('Dr. Watson','chn','atl','kca','nyn',['SIP','W','K','SB','D','HR','H','R','BB','GE'],8,datelist),
             makeTeam('Buena Vista Bottoms','nya','tex','ari','was',['W','BB','GE','K','SB','H','HR','D','R','SIP'],6,datelist),
             makeTeam('Damnedest of the Nice','cle','det','hou','chn',['SB','GE','R','HR','D','K','W','BB','SIP','H'],4,datelist)]

    return teams

def CleanStats(sts):
   sns = makeScoringNames(10)
   for s in sts:
      for n in sns:
         s[n] = round(s[n] * 50,1)
   return sts

def myunique(seq, idfun=None): 
   # order preserving
   if idfun is None:
       def idfun(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = idfun(item)
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result

def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z

def makeDictForDateStat(ress,stat,date):
   dress = [r for r in ress if r['date'] == date]
   allteams =  getAllMLBTeams()
   if stat=='sip':
      newdict = {team:sum([float(r[stat]) for r in dress if r['team'] ==unicode(team)]) for team in allteams}
      print newdict
   else:
      newdict = {team:sum([int(r[stat]) for r in dress if r['team'] ==unicode(team)]) for team in allteams}
   newdict['date'] = date
   return newdict

def OutputTablesToFiles(filename_base,ress):
   allteams =  getAllMLBTeams()

   #print separate spreadsheet for each stat

   dates = myunique([r['date'] for r in ress])
   stats = ['hits','bb','hr','runs','d','sb','sip','win','k','gooseEggs']
   for stat in stats:
      zelist = [makeDictForDateStat(ress,stat,date) for date in dates]
      ff = open(filename_base+stat+'.html','wb')
      ff.write('<BR><BR>' + stat + '<BR><tt>')   
      cnames = ['date']
      cnames.extend(allteams)
      printDictList(ff,zelist,cnames)
      ff.flush()
      ff.close()
      
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

def getAllMLBTeams():
    teamMapping = {'ana':'Angels', 'ari':'Diamondbacks', 'atl':'Braves', 'bal':'Orioles', 'bos':'Red Sox', 'cha':'White Sox',
                    'chn':'Cubs', 'cin':'Reds', 'cle':'Indians', 'col':'Rockies', 'det':'Tigers', 'hou':'Astros', 'kca':'Royals',
                    'lan':'Dodgers', 'mia':'Marlins', 'mil':'Brewers', 'min':'Twins', 'nya':'Yankees', 'nyn':'Mets', 'oak':'Athletics',
                    'phi':'Phillies', 'pit':'Pirates', 'sdn':'Padres', 'sea':'Mariners', 'sfn':'Giants', 'sln':'Cardinals', 'tba':'Rays',
                    'tex':'Rangers', 'tor':'Blue Jays', 'was':'Nationals'}
    return teamMapping.keys()
        
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

def ExtractTeamRecords(dd,gooseEggs,curdate):
   """Takes json dictionary of all boxscore, returns relevant stuff"""
   tgh = {}
   tga = {}
   res = None
   try:
      tgh['team'] = dd['data']['boxscore']['home_team_code']
      tga['team'] = dd['data']['boxscore']['away_team_code']

      tgh['game_id'] = dd['data']['boxscore']['game_id']
      tga['game_id'] = dd['data']['boxscore']['game_id']

      tgh['date'] = curdate
      tga['date'] = curdate

      tgh['runs'] = int(dd['data']['boxscore']['linescore']['home_team_runs'])
      tga['runs'] = int(dd['data']['boxscore']['linescore']['away_team_runs'])

      if tgh['runs'] > tga['runs']:
         tgh['win'] = 1
         tga['win'] = 0
      else:
         tgh['win'] = 0
         tga['win'] = 1

      bats = dd['data']['boxscore']['batting']
      bh = [b for b in bats if b['team_flag']=='home']
      ba = [b for b in bats if b['team_flag']=='away']

      tgh['hits'] = bh[0]['h']
      tga['hits'] = ba[0]['h']

      tgh['bb'] = bh[0]['bb']
      tga['bb'] = ba[0]['bb']

      tgh['hr'] = bh[0]['hr']
      tga['hr'] = ba[0]['hr']

      tgh['d'] = bh[0]['d']
      tga['d'] = ba[0]['d']
      
      hbats = bh[0]['batter']
      abats = ba[0]['batter']

      tgh['sb'] = sum([int(b['sb']) for b in hbats])
      tga['sb'] = sum([int(b['sb']) for b in abats])
      
      pits = dd['data']['boxscore']['pitching']
      ph = [p for p in pits if p['team_flag']=='home']
      pa = [p for p in pits if p['team_flag']=='away']

      tgh['k'] = ph[0]['so']
      tga['k'] = pa[0]['so']
      
      hpits = ph[0]['pitcher']
      if type(hpits) is dict:
         hpits= [hpits]
      apits = pa[0]['pitcher']
      if type(apits) is dict:
         apits= [apits]

      tgh['sip'] = float(hpits[0]['out'])/3.0
      tga['sip'] = float(apits[0]['out'])/3.0
      
      tgh['gooseEggs'] = gooseEggs[tgh['team']]
      tga['gooseEggs'] = gooseEggs[tga['team']]


      res = [tga,tgh]
   except:
      traceback.print_exc()
      print 'no data yet'
   return res

def runnersFromAB(ab):
   numR = [1 for runner in ab.iter('runner') if len(runner.attrib['start'])>0]
   return sum(numR)

def runsScoredFromAB(ab):
   numR = [1 for runner in ab.iter('runner') if ('score' in runner.attrib and runner.attrib['score'] == 'T')]
   return sum(numR)

def scoringRunnersFromAB(ab):
   runners = [runner.attrib['id'] for runner in ab.iter('runner') if ('score' in runner.attrib and runner.attrib['score'] == 'T')]
   if runners is None:
      runners = []
   return runners

def basedRunnersFromAB(ab):
   brunners = [runner.attrib['id'] for runner in ab.iter('runner') if len(runner.attrib['end'])>0]
   if brunners is None:
      brunners = []
   return brunners

def GetGooseEggs(lins,team,sp):
   #takes late inning records, team (0 or 1) and the starting pitcher's id.   
   #returns single team's GE for all late innings
   ge = 0
   for inn in lins:
      try:
         hinn = inn[team]
         ge = ge + GetGooseEggsFromHinn(hinn,team,sp)
      except:
         print 'bonk in inning ' + (inn.attrib['num'])
         ge = ge
   return ge

def GetGooseEggsFromHinn(hinn,team,sp):
   #initialize  to first atbat pitcher
   #initialize runs to 0, outs to 0, inhr to 0,on-base
   # then, using for ab in inn7[team].iter('atbat'):
   #if-pitcher changes or we are out of atbats, score pitcher
   #if new pitcher, then is_ge_opp must be evaluated,
   #    which is up by two or less, tied, or tying run on base or at bat
   #then, for that pitcher, success is
   #    no runs charged and
   #    records 3 outs in the inning OR records and out and #outs plus inhr >=3
   # and add the right thing for when the pitcher changes....  must keep track for each pitcher...
   # must score the current pitcher on a pitcher change and score on end of inning...
   pitcher=0
   gooses = 0
   outs = 0
   goose_list = [];
   for ab in hinn.iter('atbat'):
      runs_this_ab = runsScoredFromAB(ab)
      if(ab.attrib['pitcher'] != pitcher):
         #new Pitcher
         #close out old pitcher
         if (pitcher != 0):
            #print 'gooseAlive:' + str(gooseAlive) + ',pruns'+str(pruns)+',pouts:'+str(pouts)+',pob:'+str(pob)         
            if gooseAlive and pruns == 0 and (pouts==3 or (pouts > 0 and pouts + pob >= 3)):
               #gooses = gooses+1
               goose_list.append([pitcher,runners_allowed])
               #print 'GOOSE'
            #else:
               #print 'NO GOOSE'
         #init new pitcher
         pob = runnersFromAB(ab)
         pruns = 0
         gooseAlive = True
         pouts = 0
         pitcher = ab.attrib['pitcher']
         runners_allowed = []
         #print pitcher
         if (team==0):
            runs_against = int(ab.attrib['away_team_runs'])-runs_this_ab
            runs_for = int(ab.attrib['home_team_runs'])
         else:
            runs_against = int(ab.attrib['home_team_runs'])-runs_this_ab
            runs_for = int(ab.attrib['away_team_runs'])
         if pitcher == sp:
            gooseAlive = False  #not the starting pitcher
            #print 'startingP'
         run_d = runs_for - runs_against
         if not(run_d >= 0 and run_d < 3) or (pob+1 >= run_d and run_d>0):
            gooseAlive = False  #not a GE situation
            #print 'not GE sitch'
      pruns = pruns + runs_this_ab
      runners_allowed = runners_allowed + basedRunnersFromAB(ab)
      goose_list = [g for g in goose_list if len(set(g[2]).intersection(scoringRunnersFromAB(ab))) == 0]
      abouts = int(ab.attrib['o'])
      if (abouts > outs):
         pouts = pouts + abouts - outs
         outs = abouts
   #print 'gooseAlive:' + str(gooseAlive) + ',pruns'+str(pruns)+',pouts:'+str(pouts)+',pob:'+str(pob)         
   if gooseAlive and pruns == 0 and (pouts==3 or (pouts > 0 and pouts + pob >= 3)):
      goose_list.append([pitcher,[]])
      #print 'GOOSE'
   #else:
      #print 'NO GOOSE'
   gooses = len(goose_list)
   return gooses
         

def getStartingPitcher(gg,team):
   root=gg.getroot()
   finning = [inn for inn in root.iter('inning') if int(inn.attrib['num'])==1]
   if (team=='home'):
      abs = [ab for ab in finning[0][0].iter('atbat')]  
   else:
      abs = [ab for ab in finning[0][1].iter('atbat')]
   pitcher = abs[0].attrib['pitcher']
   return pitcher
         
def ExtractGooseEggs(gg):
   try:
      root= gg.getroot()
   except:
      return []
   #first get innings above 7
   #then get first for one team, then the other, return dictionary of team, ge
   linnings = [inn for inn in root.iter('inning') if int(inn.attrib['num'])>6]
   try:
      home_team = linnings[0].attrib['home_team']
      away_team = linnings[0].attrib['away_team']
      home_sp = getStartingPitcher(gg,'home')
      away_sp = getStartingPitcher(gg,'away')
      ges = {home_team:GetGooseEggs(linnings,0,home_sp),away_team:GetGooseEggs(linnings,1,away_sp)}
   except:
      print 'ouch'
      return None
   return ges



def CompileDayGames(curdate):
   team_games = []

   gameids = DateGames(curdate)
   for g in gameids:
      print 'Doing game ' + g
      sys.stdout.flush()
      jsonbox = GetGameBoxScoreJson(g)
      if not jsonbox is None:
         innings_all = GetGame(g)
         gooseEggs = ExtractGooseEggs(innings_all)
         if not gooseEggs is None:
            trs = ExtractTeamRecords(jsonbox,gooseEggs,curdate)
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
    #start_date_16 = date(2016,4,3)
    #end_date_16 = date(2016,10,2)
    #start_date_17 = date(2017,5,4)
    #end_date_17 = date(2017,6,4)
    today = datetime.now()
    today = today.date()
    start_date = date(2017,5,4)
    end_date = date(2017,6,4)
    end_date = min(end_date,today)
    print end_date
    #end_date = min(end_date,today)
    #ress_16 = getFilledTeams(d2s(start_date_16),d2s(end_date_16))
    #pickle.dump( ress, open( "ress_16.p", "wb" ) )
    ress_17 = getFilledTeams(d2s(start_date),d2s(end_date))
    pickle.dump( ress_17, open( "ress_17.p", "wb" ) )
    #ress_16.extend(ress_17)
    ress = ress_17

    #pickle.dump( ress, open( "ress.p", "wb" ) )
    
    OutputTablesToFiles(codehome + monthfolder + 'stats_wb6m2_',ress)
    return ress
    
