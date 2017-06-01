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
    return({'stat':stat,'dates':dates,'r1':None,'r2':None,'p1':None,'p2':None})

def makeTeam(name,t1,t2,t3,t4,stats,m1,datelist):
    team = {'team':name,'bteams':[t1,t2],'pteams':[t3,t4],
            'frames':[makeFrame(s,dates) for s,dates in zip(stats,datelist)],'m1':m1}
    #team['frames'][9]['r3'] = None
    #team['frames'][9]['p3'] = None
    #team['frames'][9]['bs3'] = None
    #team['frames'][9]['extraDates'] = datelist[10]
    
    return team

def getTeams():
    #team_names = ['Drumpfallacious','No-Talent Ass Clowns', 'Portlandia Misfits', 'The Rube', 'Paly Players', 'Dr. Watson', 'Buena Vista Bottoms', 'Damnedest of the Nice']
    #players = loadCSVDict(codehome + 'players2016.csv')

    sd = date(2017,5,4)
    dlist = [[i*3+0,3*i+1,3*i+2] for i in range(0,10)]
    dlist.append([30,31])
    datelist = [[sd+timedelta(i) for i in frame] for frame in dlist]

    teams = [makeTeam('Drumpies','lan','hou','lan','bos',['H','W','R','D','SOUTS','K','BB','SB','GE','HR','HR'],8,datelist),
             makeTeam('No-Talent Ass Clowns','mil','sea','bal','cle',['W','SOUTS','HR','BB','SB','K','GE','H','R','D','D'],3,datelist),
             makeTeam('Portlandia Misfits','was','sln','ana','sln',['BB','H','HR','D','GE','K','W','R','SB','SOUTS','SOUTS'],5,datelist),
             makeTeam('The Rube','ari','cin','sfn','nya',['HR','K','H','SB','R','D','SOUTS','W','BB','GE','GE'],1,datelist),
             makeTeam('Paly Players','nyn','col','cha','tba',['K','W','HR','GE','R','SOUTS','D','SB','BB','H','H'],2,datelist),
             makeTeam('Dr. Watson','chn','atl','kca','nyn',['SOUTS','W','K','SB','D','HR','H','R','BB','GE','GE'],7,datelist),
             makeTeam('Buena Vista Bottoms','nya','tex','ari','was',['W','BB','GE','K','SB','H','HR','D','R','SOUTS','SOUTS'],6,datelist),
             makeTeam('Damnedest of the Nice','cle','det','hou','chn',['SB','GE','R','HR','D','K','W','BB','SOUTS','H','H'],4,datelist)]

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
   if stat=='souts':
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
   stats = ['hits','bb','hr','runs','d','sb','souts','win','k','gooseEggs']
   for stat in stats:
      zelist = [makeDictForDateStat(ress,stat,date) for date in dates]
      ff = open(filename_base+stat+'.html','wb')
      ff.write('<BR><BR>' + stat + '<BR><tt>')   
      cnames = ['date']
      cnames.extend(allteams)
      printDictList(ff,zelist,cnames)
      ff.flush()
      ff.close()

def bowlingScoreToText(f):
   if 'p3' in f.keys():
      if f['p1'] == 10:
         if f['p2'] == 10:
            if f['p3'] == 10:
               return 'XXX'
            else:
               return 'XX%s'%(f['p3'])
         else:
            if f['p2']+f['p3'] >=10:
               return 'X%s/'%(f['p2'])
            else:
               return'X%s%s'%(f['p2'],f['p3'])
      elif f['p1']+f['p2'] >=10:
         if f['p3'] == 10:
            return '%s/X'%(f['p1'])
         else:
            return '%s/%s'%(f['p1'],f['p3'])
      else:
         return '%s %s'%(str(f['p1']),str(f['p2']))
   else:
      if f['p1'] == 10:
         return 'X  '
      elif f['p1'] + f['p2'] >= 10:
         return '%s /'%(str(f['p1']))
      else:
         return '%s %s'%(str(f['p1']),str(f['p2']))

def printGE(filename,ress):
   ff = open(filename,'wb')
   printDictListCSV(ff,ress,['game_id','team','gooseEggs'])
   ff.flush()
   ff.close()
      
def printTeamsToFile(filename,ts):
   ff = open(filename,'wb')
   for t in ts:
      ff.write('<BR>Team %s <BR>'%(t['team']))
      i=1
      for f in t['frames']:
         if f['p1'] == None:
            break
         if f['stat'] in ['W','GE','K','SOUTS']:
            lteams = t['pteams']
         else:
            lteams = t['bteams']
         ff.write('<BR>Frame%s, need %s, target %s, from %s, %s<BR>'%(str(i),f['stat'],getTarget(f['stat']),lteams[0],lteams[1]))
         ff.write('From %s, got %s / %s -> %s pins<BR>'%(lteams[0],f['r1'],getTarget(f['stat']),pinnize(f['r1'],getTarget(f['stat']))))
         ff.write('From %s, got %s / %s -> %s pins<BR>'%(lteams[1],f['r2'],getTarget(f['stat']),pinnize(f['r2'],getTarget(f['stat']))))
         if i!=11:
            f['bscore'] = bowlingScoreToText(f)
            ff.write('Bowling Score = %s<BR>'%(f['bscore']))
         t['teamtotal'] = f['total']
         i = i+1
   ff.flush()
   #Now write the bowling scores in a more bowling format...
   steams = sorted(ts,key=lambda k: k['teamtotal'],reverse=True)
   ff.write('<BR><BR><table border=1 style="border:1px solid"><tr><th>Team</th>')
   for i in range(1,11):
      ff.write('<th>___%s___</th>'%(str(i)))
   ff.write('<th>Total</th></tr>')
   for t in steams:
      ff.write('<tr><td>%s</td>'%(t['team']))
      for f in t['frames'][0:10]:
         if f['p1'] != None: 
            ff.write('<td>%s</td>'%(f['bscore']))
         else:
            ff.write('<td></td>')
      ff.write('<td>%s</td></tr>'%t['teamtotal'])
      ff.write('<tr><td></td>')
      for f in t['frames'][0:10]:
         if (f['p1'] != None):
            ff.write('<td>%s</td>'%(str(f['total'])))
         else:
            ff.write('<td></td>')
      ff.write('<td></td></tr>')
   ii = 0
   for st in steams:
      m2s = scoreSingle([x['teamtotal'] for x in steams],ii)      
      st['through_two'] = st['m1'] + m2s
      st['m2'] = m2s
      ii=ii+1
   ff.write('</table>')
   ff.flush()
   ff.write('<BR><BR><BR>Season scores As of Today:<BR>')

   ssteams = sorted(steams,key=lambda k: k['through_two'],reverse=True)
   printDictList(ff,ssteams,['team','m1','m2','through_two'])
   ff.write('<BR><BR>')
      
   ff.write(str(datetime.now()))
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

      tgh['souts'] = float(hpits[0]['out'])
      tga['souts'] = float(apits[0]['out'])
      
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
         print 'bonk in inning ' + (inn.attrib['num']) + ' half' + str(team)
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
   #print 'start of GGEFH, team is  '+str(team)
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
         if not(run_d >= 0 and run_d < 3) and not(pob+1 >= run_d and run_d>0):
            gooseAlive = False  #not a GE situation
            #print 'not GE sitch, ' + 'runs_for:'+str(runs_for)+',runs_ag:'+str(runs_against)+',pob:'+str(pob)
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
   except Exception as e:
      print(traceback.format_exc())
      print 'ouch'
      print e
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
         ht = jsonbox['data']['boxscore']['home_team_code']
         at = jsonbox['data']['boxscore']['away_team_code']
         if gooseEggs is None:
            gooseEggs={ht:0,at:0}
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

def statMap():
    sm = {'W':'win','BB':'bb','H':'hits','R':'runs','D':'d','SOUTS':'souts','K':'k','HR':'hr','GE':'gooseEggs','SB':'sb'}
    return sm

def statTargets():
    sm = {'W':3,'BB':15,'H':35,'R':21,'D':9,'SOUTS':63,'K':32,'HR':6,'GE':4,'SB':4}
    return sm

def getTarget(stat):
    sm = statTargets()
    return(sm[stat])

def getSecondScore(p1,p2,fnum):
   if fnum <= 9:
      if(p1 < 10):
         return min(10-p1,p2)
      else:
         return 0
   else:
      if p1==10:
         return p2
      else:
         return min(10-p1,p2)

def pinnize(s,targ):
   return min(10,10*s / targ)

def getPreviousScore(fnum,t):
   if fnum > 0:
      return t['frames'][fnum-1]['total']
   else:
      return 0

def getNextScores(fnum,t,n):
   if t['frames'][fnum+1]['p1']==None:
      return 0
   elif n==1:
      return t['frames'][fnum+1]['p1']
   elif n==2:
      if t['frames'][fnum+1]['p1'] == 10:
         return 10+getNextScores(fnum+1,t,1)
      else:
         return t['frames'][fnum+1]['p1'] + t['frames'][fnum+1]['p2']

def scoreBowlingFrame(fnum,t) :
   p1 = t['frames'][fnum]['p1']
   p2 = t['frames'][fnum]['p2']
   if p1==None or p2==None:
      return
   if fnum < 9:
      if p1+p2 < 10:
         t['frames'][fnum]['total'] = getPreviousScore(fnum,t) + p1+p2
      else:
         if p1==10:
            t['frames'][fnum]['total'] = getPreviousScore(fnum,t) + 10 + getNextScores(fnum,t,2)
         else:
            t['frames'][fnum]['total'] = getPreviousScore(fnum,t) + 10 + getNextScores(fnum,t,1)
   else:
      try:
         p3 = t['frames'][fnum]['p3']
      except:
         p3 = 0
      if p1==10 and p2==10:
         t['frames'][fnum]['total'] = getPreviousScore(fnum,t)+20+p3
      elif p1==10:
         t['frames'][fnum]['total'] = getPreviousScore(fnum,t)+10+p2+p3
      elif p1+p2==10:
         t['frames'][fnum]['total'] = getPreviousScore(fnum,t)+10+p3
      else:
         t['frames'][fnum]['total'] = getPreviousScore(fnum,t)+p1+p2
         
            

def fillFramesForTeam(t,ress):
   sm = statMap()
   fnum = 1
   for f in t['frames']:
      lstat = sm[f['stat']]
      if f['stat'] in ['W','GE','K','SOUTS']:
         lteams = t['pteams']
      else:
         lteams = t['bteams']
      gs1 = [r for r in ress if r['pdate'] in f['dates'] and r['team'] == lteams[0]]
      gs2 = [r for r in ress if r['pdate'] in f['dates'] and r['team'] == lteams[1]]
      if len(gs1) > 0 or len(gs2) > 0:
         f['games1'] = gs1
         f['games2'] = gs2
         f['r1'] = sum([int(r[lstat]) for r in gs1])
         f['r2'] = sum([int(r[lstat]) for r in gs2])
         targ = getTarget(f['stat'])
         p1 = pinnize(f['r1'],targ)
         p2 = pinnize(f['r2'],targ)
         if p1>=p2:
            f['p1'] = p1
            f['p2'] = getSecondScore(p1,p2,fnum)
         else:
            f['p1'] = p2
            f['p2'] = getSecondScore(p2,p1,fnum)
         fnum = fnum+1
      else:
         break
   #need to fix up frame 10...
   if fnum > 8:
       f10 = t['frames'][9]
       f11 = t['frames'][10]
      
   if (fnum > 9) and (f10['p1']+f10['p2'])>=10: 
      if not f11['p1'] is None:
         if f10['p1']==10 and f10['p2']==10 or f10['p1']!=10 and f10['p1']+f10['p2']==10:
            f10['p3'] = pinnize(f11['r1']+f11['r2'],getTarget(f10['stat']))
         else:
            f10['p3'] = pinnize(max(f11['r1'],f11['r2']),getTarget(f10['stat']))
      else:
         f10['p3'] = 0
   #Ok, now that we have pins, fill in the scores, dealing specially with 10/11
    
   for fnum in range(0,10):
      scoreBowlingFrame(fnum,t) 
   return t

def fillFramesWithStats(teams,ress):
    teams = [fillFramesForTeam(t,ress) for t in teams]
    return teams

def printTeam(t):
   print 'for team ' + str(t['team'])
   for f in t['frames']:
      if f['p1'] != None:
         print str(f['p1'])+','+str(f['p2'])+','+str(f['total'])
    

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
    [r.update({'pdate':datetime.strptime(r['date'],'%Y_%m_%d').date()})  for r in ress]
    #pickle.dump( ress, open( "ress.p", "wb" ) )
    teams = getTeams()
    #OutputTablesToFiles(codehome + monthfolder + 'stats_wb6m2_',ress)
    
    teams = fillFramesWithStats(teams,ress)
    printTeamsToFile('/home/eddie7/code/wb6m2/wb6m2_statsByDave.html',teams)
    print ('done with main file')
    printGE('/home/eddie7/code/wb6m2/wb6m2_gooseEggs.csv',ress)
    print ('done with GE file')
    
    return ress,teams
    
