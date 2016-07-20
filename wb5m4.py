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
codehome = "/Users/dandre/Code/wb/baseball/"
#codehome = "/Users/martin/Baseball/WhiskeyBall/Code/"
monthfolder = "wb5m4/"

def getBattersOfWildPitches(ge):
    actions = ge.findall(".//action[@event='Wild Pitch']")
    results = [a.attrib['player'] for a in actions]
    return results

def getVictoryPoints(ts):
   #return a list of dictonaries with the season-point scores
   #PA, BB%-K%, wOBA, wSB
   #IP, K%-BB%, FIP, LOB%

   cats = makeScoringNames()
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

def makeScoringNames():
    return(['total_bases','runs_scored','strikeouts','wsbsf','sb','total_bases_allowed','runs_against','strikeouts_po','whbpwp','ips'])

def getWP(g,ge):
    home_team_wp = 0
    away_team_wp = 0
    bats = g['data']['boxscore']['batting']
    bh = [b for b in bats if b['team_flag']=='home']
    ba = [b for b in bats if b['team_flag']=='away']
    hbats = bh[0]['batter']
    abats =ba[0]['batter']
    hbat_ids = [h['id'] for h in hbats]
    abat_ids = [h['id'] for h in abats]
    
    #    actions = ge.findall(".//action[@event='Wild Pitch']")
    
    acs = getBattersOfWildPitches(ge)
    
    home_team = g['data']['boxscore']['home_team_code']
    away_team = g['data']['boxscore']['away_team_code']
    for bwp in acs:
        if (int(bwp) in [int(a) for a in abat_ids]):
            home_team_wp +=1
        if (int(bwp) in [int(a) for a in hbat_ids]):
            away_team_wp +=1
    return home_team_wp, away_team_wp

def scoreThree(d):
    vals = d.values()
    vals.sort()
    return min(vals[2]-vals[1],vals[1]-vals[0])

def getFilledTeams(date1,date2):
    ts = getTeams()
    (ress) = CompileRangeGames(date1,date2) 
    for t in ts:
        #print 'doing', t['team_name']
        
        mysum=lambda team,label,llist:sum([int(x[label]) for x in llist if x['team'] == team])

        t['stats'] = {}
        t['stats']['total_bases'] = {}
        t['stats']['runs_scored'] = {}
        t['stats']['strikeouts'] = {}
        t['stats']['wsbsf'] = {}
        t['stats']['sb'] = {}
        for ht in t['hitting_team_teams']:
            t['stats']['total_bases'][ht] = mysum(ht,'total_bases',ress)
            t['stats']['runs_scored'][ht] = mysum(ht,'runs_scored',ress)
            t['stats']['strikeouts'][ht] = mysum(ht,'h_so',ress)
            t['stats']['wsbsf'][ht] = mysum(ht,'h_bb',ress) + mysum(ht,'sac',ress) + mysum(ht,'sf',ress)
            t['stats']['sb'][ht] = mysum(ht,'sb',ress)
        t['stats']['total_bases_allowed'] = {}
        t['stats']['runs_against'] = {}
        t['stats']['strikeouts_po'] = {}
        t['stats']['whbpwp'] = {}
        t['stats']['ips'] = {}
        for pt in t['pitching_team_teams']:
            t['stats']['total_bases_allowed'][pt] = mysum(pt,'total_bases_allowed',ress)
            t['stats']['runs_against'][pt] = mysum(pt,'runs_against',ress)
            t['stats']['strikeouts_po'][pt] = mysum(pt,'p_so',ress)
            t['stats']['whbpwp'][pt] = mysum(pt,'hbp',ress) + mysum(pt,'p_bb',ress) + mysum(pt,'wild_pitches',ress)
            t['stats']['ips'][pt] = mysum(pt,'ips',ress)
        t['total_bases'] = scoreThree(t['stats']['total_bases'])
        t['runs_scored'] = scoreThree(t['stats']['runs_scored'])
        t['strikeouts'] = scoreThree(t['stats']['strikeouts'])
        t['wsbsf'] = scoreThree(t['stats']['wsbsf'])
        t['sb'] = scoreThree(t['stats']['sb'])
        t['total_bases_allowed'] = scoreThree(t['stats']['total_bases_allowed'])
        t['runs_against'] = scoreThree(t['stats']['runs_against'])
        t['strikeouts_po'] = scoreThree(t['stats']['strikeouts_po'])
        t['whbpwp'] = scoreThree(t['stats']['whbpwp'])
        t['ips'] = scoreThree(t['stats']['ips'])
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

def printStatsForTeams(ts,fn):
    ff = open(codehome + monthfolder + fn,'wb')
    for t in ts:
        ff.write('Hitting Stats for: ' + t['team_name'] + '<BR>')
        ff.write('<table><tr>')
        ff.write('<th>Category</th>')
        cols = t['hitting_team_teams']
        for c in cols:
            ff.write('<th>%s</th>'%(c))
        ff.write('\n</tr>')
        #now write the data
        hitting_stats = ['total_bases','strikeouts','wsbsf','runs_scored','sb']
        for r in hitting_stats:
            ff.write('<tr><td>'+r+'</td>')
            for c in cols:
                ff.write('<td>%s</td>'%(t['stats'][r][c]))
            ff.write('</tr>\n')
        ff.write('</table>')
        ff.flush()

        ff.write('Pitching Stats for: ' + t['team_name'] + '<BR>')
        ff.write('<table><tr>')
        ff.write('<th>Category</th>')
        cols = t['pitching_team_teams']
        for c in cols:
            ff.write('<th>%s</th>'%(c))
        ff.write('\n</tr>')
        #now write the data
        pitching_stats = ['total_bases_allowed','strikeouts_po','whbpwp','runs_against','ips']
        for r in pitching_stats:
            ff.write('<tr><td>'+r+'</td>')
            for c in cols:
                ff.write('<td>%s</td>'%(t['stats'][r][c]))
            ff.write('</tr>\n')
        ff.write('</table>')
        ff.flush()
    ff.close()
        
        
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
      m4s = scoreSingle([x['total'] for x in svps],ii)      
      svi['through_four'] = svi['mtotal'] + m4s
      svi['m1'] = svi['mscores'][0]
      svi['m2'] = svi['mscores'][1]
      svi['m3'] = svi['mscores'][1]
      svi['m4'] = m4s
      ii = ii+1
   ff = open(filename,'wb')
   ff.write('<BR><BR>Stats<BR><tt>')
   cats = makeScoringNames()
   plist = ['team']
   plist.extend(cats)
   #csts = CleanStats(sts)
   printDictList(ff,sts,plist) 
   ff.flush()
   ff.write('<BR><BR>Points<BR>')
   plist.append('total')
   printDictList(ff,svps,plist)

   ff.write('<BR><BR>Season scores As of Today:<BR>')

   ssvps = sorted(svps,key=lambda k: k['through_four'],reverse=True)
   printDictList(ff,ssvps,['team_name','m1','m2','m3','m4','through_four'])
   ff.write('<BR><BR>')
   ff.write("For detailed stats <a href='all.html'> all.html </a><BR><BR>")
   
   # provide links to all teams' batter and pitcher stat files
   #   ff.write("<a href='TheRube_pitchers.csv'> Rube pitchers </a><BR>")

   ff.write('<BR><BR>')
   ff.write('</tt>')
   ff.write(str(datetime.now()))

   ff.close()
   printStatsForTeams(ts,'all.html')
   
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

#Batting:
#total bases, runs scored, strikeouts, walks + sacrifice bunts + sacrifice flies, stolen bases

#Pitching:
#total bases allowed, runs allowed, strikeouts, walks + hit batsmen + wild pitches,
#innings pitched by starters

def ExtractTeamRecords(dd,ge):
    """Takes json dictionary of all boxscore, returns relevant stuff"""
    tgh = {}
    tga = {}
    res = None
    try:
        tgh['team'] = dd['data']['boxscore']['home_team_code']
        tga['team'] = dd['data']['boxscore']['away_team_code']
        
        hwp,awp = getWP(dd,ge)
        tgh['wild_pitches'] = hwp
        tga['wild_pitches'] = awp
        
        tgh['runs_scored'] = dd['data']['boxscore']['linescore']['home_team_runs']      
        tga['runs_against'] = tgh['runs_scored']
        
        tga['runs_scored'] = dd['data']['boxscore']['linescore']['away_team_runs']      
        tgh['runs_against'] = tga['runs_scored']
        
        tgh['game_id'] = dd['data']['boxscore']['game_id']
        tga['game_id'] = dd['data']['boxscore']['game_id']
        
        bats = dd['data']['boxscore']['batting']
        bh = [b for b in bats if b['team_flag']=='home']
        ba = [b for b in bats if b['team_flag']=='away']
        hbats = bh[0]['batter']
        abats =ba[0]['batter']
        
        pits = dd['data']['boxscore']['pitching']
        ph = [p for p in pits if p['team_flag'] =='home']
        pa = [p for p in pits if p['team_flag'] =='away']
        if type(ph[0]['pitcher']) is dict:
            hpits = [ph[0]['pitcher']]
        else:
            hpits = [p for p in ph[0]['pitcher']]
        if type(pa[0]['pitcher']) is dict:
            apits = [pa[0]['pitcher']]
        else:
            apits = [p for p in pa[0]['pitcher']]

        tgh['total_bases'] = sum([int(h['h'])+int(h['d'])+int(h['t'])*2+int(h['hr'])*3 for h in hbats])
        tga['total_bases'] = sum([int(h['h'])+int(h['d'])+int(h['t'])*2+int(h['hr'])*3 for h in abats])
        tga['total_bases_allowed'] = tgh['total_bases']
        tgh['total_bases_allowed'] = tga['total_bases']

        tgh['hbp'] = sum([int(h['hbp']) for h in abats])
        tga['hbp'] = sum([int(h['hbp']) for h in hbats])
        
        tgh['p_so'] = sum([int(p['so']) for p in hpits])
        tga['p_so'] = sum([int(p['so']) for p in apits])
        tgh['h_so'] = tga['p_so']
        tga['h_so'] = tgh['p_so']
        
        tgh['p_bb'] = sum([int(p['bb']) for p in hpits])
        tga['p_bb'] = sum([int(p['bb']) for p in apits])
        tgh['h_bb'] = tga['p_so']
        tga['h_bb'] = tgh['p_so']
        
        tgh['sb'] = sum([int(h['sb']) for h in hbats])
        tga['sb'] = sum([int(h['sb']) for h in abats])
        
        tgh['sf'] = sum([int(h['sf']) for h in hbats])
        tga['sf'] = sum([int(h['sf']) for h in abats])
        
        tgh['sac'] = sum([int(h['sac']) for h in hbats])
        tga['sac'] = sum([int(h['sac']) for h in abats])
        
        tgh['ips'] = int(hpits[0]['out'])
        tga['ips'] = int(apits[0]['out'])
        
        #here -- try this out. 
      
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
        ge = GetGameEvents(g)          
        trs = ExtractTeamRecords(jsonbox,ge)
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
    start_date = date(2016,7,14)
    end_date = date(2016,8,9)
    #end_date = date(2016,5,10)
    end_date = min(end_date,today)
    ts,ress = getFilledTeams(d2s(start_date),d2s(end_date))
    OutputTablesToFile(codehome + monthfolder + 'stats_wb5m4.html',ts,ress)
