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
#import MySQLdb
#import MySQLdb.cursors
import string
import collections
import copy
import pickle
import json
import numpy
import pdb

#db= MySQLdb.connect(user='root' , passwd='andnotbut', db='wb3m4')
#cursor = db.cursor()

#dbd = MySQLdb.connect(user='root' , passwd='andnotbut', db='wb3m4',cursorclass=MySQLdb.cursors.DictCursor)
#cursord = dbd.cursor()

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

def loadCSV(filename):
    with open(filename,'rU') as csvfile:
        reader = csv.DictReader(csvfile)
        kept2 = [row for row in reader]    
    return kept2

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def printBest(player_stats,pos,k=24):
    best = getBestForPos(player_stats,pos)
    i = 0
    for p in best:
        if i < k:
            print str(i) + ' ' + p['PLAYER'] + ' ops_pred: '+ str(p['ops_pred']) + ' mean:' + str(p['mean_ops']) +   ' median:' + str(p['median_ops']) + ', OPS: ' + str(p['OPS'])
        i = i+1
    
def getBestForPos(player_stats, pos):
    is_field = 'is_'+pos 
    score_field = is_field + '_pred_sort'
    subset = sorted(player_stats,key=lambda k: k[score_field])
    subset = [x for x in subset if x[is_field]]
    return subset
    
def makePlayerStats(battergames):
    c = collections.Counter([x['id'] for x in battergames])
    ids = c.keys()
    plys = [];
    bpreds = loadCSV('/Users/dandre/downloads/ops_preds.csv')
    bp_ids = [x['MLB_ID'] for x in bpreds]
    for i in bp_ids:
        pgs = [x for x in battergames if str(x['id']) == i]
        base_dict = [x for x in bpreds if x['MLB_ID'] == i]
        if base_dict is None:
            print 'No BP element for ' + str(bp_ids)
        if not(pgs is None):
            if len(pgs) > 1:
                print 'doing ' + str(i)
                base_dict = base_dict[0]                
                if not(is_number(base_dict['OPS'])):
                    base_dict['OPS'] = 0
                    print 'No OPS?!?'
                ops = [float(x['ops']) for x in pgs]
                base_dict['mean_ops'] = numpy.mean(ops)
                base_dict['std_ops'] = numpy.std(ops)
                base_dict['median_ops'] = numpy.median(ops)
                print 'base_dict-OPS is ' + str(base_dict['OPS']) + ' median is ' + str(base_dict['median_ops']) + ' mean is ' + str(base_dict['mean_ops']) + ' and std is ' + str(base_dict['std_ops'])
                
                base_dict['ops_pred'] = 0.5*float(base_dict['OPS']) + 0.3*base_dict['median_ops']+0.2*(base_dict['mean_ops']/(0.00001+base_dict['std_ops']))
                base_dict['ngames'] = len(ops)
                base_dict['elig_pos'] = base_dict['POS'].split(',')
                base_dict['is_c'] = 'C' in base_dict['elig_pos']
                base_dict['is_1'] = '1B' in base_dict['elig_pos']
                base_dict['is_2'] = '2B' in base_dict['elig_pos']
                base_dict['is_ss'] = 'SS' in base_dict['elig_pos']
                base_dict['is_3'] = '3B' in base_dict['elig_pos']
                base_dict['is_OF'] = len(set(['RF','CF','LF']).intersection(base_dict['elig_pos'])) > 0
                plys.append(base_dict)
                #            else:
                #print 'only one game?!?'
        else:
            print 'no games this year?!?'
    #Now, put in the sort order by both median_ops by category, and OPS by category
    positions = ['is_c','is_1','is_2','is_ss','is_3','is_OF']
    for p in positions:
        plys = sorted(plys,key=lambda k: k['OPS']*(1 if k[p] else 0),reverse=True)
        for i,x in enumerate(plys):
            x[p+'_OPS_sort'] = i
        plys = sorted(plys,key=lambda k: k['median_ops']*(1 if k[p] else 0),reverse=True)
        for i,x in enumerate(plys):
            x[p+'_median_sort'] = i
        plys = sorted(plys,key=lambda k: k['ops_pred']*(1 if k[p] else 0),reverse=True)
        for i,x in enumerate(plys):
            x[p+'_pred_sort'] = i
    return plys
        
            

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
   fnames_for_scoring = ['team','pts_total']
                         
   tsc = copy.deepcopy(ts)
   vsc = []
   for tsii in tsc:
      tsii['total'] = 0
   for lab  in fnames_for_scoring[1:len(fnames_for_scoring)-1]:
      nteams = len(tsc)
      for tt in range(0,nteams):
         dascore = scoreSingle([x[lab] for x in ts],tt)
         tsc[tt][lab] = dascore
         tsc[tt]['total'] = tsc[tt]['total'] + dascore
   return tsc

def lookupPlayer2(name,ps):
    cands = [[x['PLAYER'],x['MLB_ID']] for x in ps if name in x['PLAYER']]
    return cands

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

def makeTeamDict(tname,hit_teams,pit_teams,offset,m1,m2,m3):
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

def addOPS(hitstats):
    if hitstats['ab'] == 0:
        hitstats['slg'] = 0
    else:
        hitstats['slg'] = (float(hitstats['tb']/float(hitstats['ab'])))
    if (hitstats['ab']+hitstats['bb']+hitstats['sf']+hitstats['hbp']) == 0:   
        hitstats['obp'] = 0
    else:
        hitstats['obp'] = float(hitstats['hits']+hitstats['bb']+hitstats['hbp'])/float(hitstats['ab']+hitstats['bb']+hitstats['sf']+hitstats['hbp'])
    hitstats['ops'] = round(hitstats['slg'] + hitstats['obp'],5)    
   
def getFilledTeams(date1,date2):
    ts = getTeams()
    (bress,press) = CompileRangeGames(date1,date2)
    mysum=lambda players,label,llist:sum([int(x[label]) for x in llist if int(x['id']) in players])
    hitlabels = ['ab','tb','bb','hits','hbp','sf']
    daycodes = set([x['daycode'] for x in bress])
    #am here for fixing up for rest of whiskey ball
    #Ok -- task here is different.   We want ab,bb,tb,hits,hbp,sf for each day, by team.  
    for t in ts:
        t['days'] = []
        t['pts_total'] = 0
    for dc in daycodes:
        daygames = [b for b in bress if dc == b['daycode']]
        for t in ts:
            bats = [b for b in t['batters']]
            t['tmp_ops'] = 0
            hitstats = {}
            for label in hitlabels:
                hitstats[label] = mysum(bats,label,daygames)
            daybats = [b for b in daygames if int(b['id']) in bats]
            hitstats['daycode'] = dc
            addOPS(hitstats)
            t['days'].append({'daycode':dc,'ops':hitstats['ops'],'hitstats':hitstats,'daybats':daybats})
        #Now, get the victory score by team
        todayscores = [x['days'][-1]['ops'] for x in ts]
        for tt in range(0,len(ts)):
            dascore = scoreSingle(todayscores,tt)
            ts[tt]['days'][-1]['pts'] = dascore
            ts[tt]['pts_total'] = ts[tt]['pts_total'] + dascore
    return ts,bress

def writeTeamInfo_wb4m5(ff,ts):
    for t in ts:
        ff.write('For ' + t['team_name'] +':\n')
        sdays = sorted(t['days'],key=lambda t:int(t['daycode']))        
        for d in sdays:
            ff.write('For day ' + str(d['daycode'])+'\n')
            for p in d['daybats']:
                ff.write(p['name'] + ', ab:'+str(p['ab'])+', hits:'+str(p['hits'])+', bb:'+str(p['bb'])+', hbp:'+str(p['hbp'])+', sf:'+str(p['sf'])+', tb:'+str(p['tb'])+'\n')
            ff.write('>> ops:'+str(d['ops'])+', pts:'+str(d['pts'])+'\n\n')
        ff.write('pts_total: '+str(t['pts_total'])+'\n\n')
   

def printTeamInfo_wb4m5(ts):
    for t in ts:
        print 'For ' + t['team_name'] +':'
        for d in t['days']:
            print 'For day ' + str(d['daycode'])
            for p in d['daybats']:
                print p['name'] + ', ab:'+str(p['ab'])+', hits:'+str(p['hits'])+', bb:'+str(p['bb'])+', hbp:'+str(p['hbp'])+', sf:'+str(p['sf'])+', tb:'+str(p['tb'])
            print 'ops:'+str(d['ops'])+', pts:'+str(d['pts'])
        print 'pts_total: '+str(t['pts_total'])
            


def printFilesForTeams(ts,press,bress):
   for t in ts:
      bff = open('/home/eddie7/code/wb4m4/' + t['team_name'].replace(" ","") + '_batters.csv','wb')
      pff = open('/home/eddie7/code/wb4m4/' + t['team_name'].replace(" ","") + '_pitchers.csv','wb')
      bre = getBattingRawEvents(bress,t)
      pre = getPitchingRawEvents(press,t)
      printDictListCSV(bff,bre)
      printDictListCSV(pff,pre)
      bff.close()
      pff.close()

def getPitchingRawEvents(press, t, onlywin=True):
   pits = [p['id'] for p in t['pitchers']]
   actives = [x for x in press if int(x['id']) in pits and (x['wasawin'] or not onlywin)]
   players = pickle.load(open('/home/eddie7/code/players_wb4m4.p','rb'))   
   for a in actives:
      a['player_name'] = players[a['id']]['name']
   return actives
      
def getBattingRawEvents(bress, t, onlywin=True):
   bats = [b['id'] for b in t['batters']]
   actives = [x for x in bress if int(x['id']) in bats and (x['wasawin'] or not onlywin)]
   players = pickle.load(open('/home/eddie7/code/players_wb4m4.p','rb'))      
   for a in actives:
      a['player_name'] = players[a['id']]['name']
   return actives
   
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

def printTeamPlayers(ts,bress):
    for t in ts:
        print ''
        print 'for Team: ' + t['team_name']
        for b in t['batters']:
            matches = [x for x in bress if b==int(x['id'])]
            if (len(matches)>0):
                print matches[0]['name'] + ' ' + str(matches[0]['id'])
            else:
                print 'no match found for ' + str(b)

def getTeams():
    team_names = ['Detroit Tednugents','No-Talent Ass Clowns', 'Portlandia Misfits', 'The Rube', 'Paly Players', 'Dr. Watson', 'Buena Vista Bottoms', 'Damnedest of the Nice']

    m1 = [4,5.5,5.5,3,  1,  7,  2,  8]
    m2 = [4,  1,  4,2,  6,7.5,  4,7.5, ]
    m3 = [3,  7,5.5,8,  2,  1,5.5,  4, ]
    m4 = [8, 5, 4, 7, 3, 1, 6, 2]
    
    #players = pickle.load(open('/home/eddie7/code/players_wb4m4.p','rb'))

    batters = [];
    batters.append([518735,120074,435522,571448,425509,592178,547180,624577])#brad
    batters.append([460026,458015,450314,572761,453064,493316,452254,594809])#brent
    batters.append([431145,518614,572821,518626,621043,502110,458731,467827])#scott
    batters.append([457763,405395,622110,592518,543063,443558,488726,444482])#john
    batters.append([456078,407893,429664,628356,520471,466320,471865,461314])#jesse
    batters.append([518595,502671,435079,476704,543685,457705,460075,592835])#dave
    batters.append([430832,408314,502374,453211,134181,543401,475100,547989])#martin
    batters.append([593934,545361,656941,519203,605412,571771,456715,430945])#tom

    teams = []
    i=0
    for team_name in team_names:
       fbs = [];
       fps = [];
       teams.append({'team_name':team_name, 'batters':batters[i], 'm1':m1[i],'m2':m2[i],'m3':m3[i],'m4':m4[i],'mtotal':m1[i]+m2[i]+m3[i]+m4[i]})
       i=i+1
    return teams

def OLDprintTeams():
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
      print 'huh?'
      return None                               #

def makePitcherDict(pp,p_atbats,wasawin,gid):
   pit = {}
   pit['id'] = pp['id']
   pit['wasawin'] = wasawin
   if 'note' in pp.keys() and '(H' in pp['note']:
      pit['holds'] = 1
   else:
      pit['holds'] = 0
   pit['bb'] = pp['bb']
   pit['ab'] = atbatsFromAtBats(pp['id'],p_atbats)
   pit['hits'] = pp['h']
   pit['k'] = pp['so']
   pit['outs'] = pp['out']
   pit['gid'] = gid
   return pit
   
def makeBatterDict(bb,gid):
   bat = {}
   bat['id'] = int(bb['id'])
   bat['hits'] = int(bb['h'])
   bat['doubles'] = int(bb['d'])
   bat['triples'] = int(bb['t'])
   bat['hr'] = int(bb['hr'])
   bat['bb'] = int(bb['bb'])
   bat['hbp'] = int(bb['hbp'])
   bat['ab'] = int(bb['ab'])
   bat['sf'] = int(bb['sf'])
   bat['gid'] = gid
   dt = datetime.strptime(gid[0:10],'%Y/%m/%d').date()
   bat['year'] = dt.year
   bat['month'] = dt.month
   bat['day'] = dt.day
   bat['daycode'] = dt.year*10000 + dt.month*100 + dt.day
   bat['name'] = bb['name_display_first_last']
   bat['tb'] = bat['hits']+bat['doubles']+bat['triples']*2+bat['hr']*3
   if bat['ab'] == 0:
       bat['slg'] = 0
   else:
       bat['slg'] = (float(bat['tb']/float(bat['ab'])))
   if (bat['ab']+bat['bb']+bat['sf']+bat['hbp']) == 0:   
       bat['obp'] = 0
   else:
       bat['obp'] = float(bat['hits']+bat['bb']+bat['hbp'])/float(bat['ab']+bat['bb']+bat['sf']+bat['hbp'])
   bat['ops'] = round(bat['slg'] + bat['obp'],5)

   return bat

def ExtractPlayerInfo(gg):
   batters = []
   
   try:
      status = gg['data']['boxscore']['status_ind'] 
      if not(status == 'DR'): 
         date = gg['data']['boxscore']['date']
         game_time = datetime.strptime(date, '%B %d, %Y')
         now = datetime.now()
         dt = now-game_time
         if (dt.days < 1 or status=='F'):
            bats = gg['data']['boxscore']['batting']
            gid = gg['data']['boxscore']['game_id']
            bh = [b for b in bats if b['team_flag']=='home']
            ba = [b for b in bats if b['team_flag']=='away']
            hbats = bh[0]['batter']
            abats =ba[0]['batter']
         
            hbats2 = [makeBatterDict(bb,gid) for bb in hbats]
            abats2 = [makeBatterDict(bb,gid) for bb in abats]
         
            batters.extend(hbats2)
            batters.extend(abats2)
   except:
      print 'no game yet'
   return batters

      
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
   if year=='2015' and month=='07' and day=='14':
      return []
   else:
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

def printwb4m5_preds(ps):
    ff = open('/Users/dandre/code/wb4m5_preds.csv','wb')
    printDictListCSV(ff,ps,['PLAYER','$$$','AB','MLB_ID','PA','TEAM','is_1','is_2','is_ss','is_3','is_c','is_OF','ops_pred','OPS','mean_ops','median_ops','ngames','std_ops'])
    ff.close()
    
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
   print len(dlist)
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

def printVerboseTable(ff,ts):
   tss = sorted(ts,key=lambda t:t['pts_total'],reverse=True)
   sorted_ts0_days = sorted(ts[0]['days'],key=lambda t:int(t['daycode']))
   days = [x['daycode'] for x in sorted_ts0_days]
   tnames = [t['team_name'] for t in ts]
   tlens = [len(t) for t in tnames]
   ff.write('<table><tr>')
   ff.write('<th></th>')
   for d in days:
      ff.write('<th>AUG '+str(d)[6:8]+'</th>')
   ff.write('<th>tot</th></tr><br>')
   for t in tss:
      ff.write('<tr><td>'+t['team_name']+'</td>')
      i=0
      sorted_days = sorted(t['days'],key=lambda t:int(t['daycode']))
      for d in sorted_days:
         ff.write('<td>'+'{0:.3f}'.format(d['ops']) +' ('+str(round(d['pts'],1))+')</td>')
      ff.write('<td>'+str(t['pts_total'])+'</td></tr>')
   ff.write('</table>')

def printConciseTable(ff,ts):
   tss = sorted(ts,key=lambda t:t['pts_total'],reverse=True)
   sorted_ts0_days = sorted(ts[0]['days'],key=lambda t:int(t['daycode']))
   days = [x['daycode'] for x in sorted_ts0_days]
   tnames = [t['team_name'] for t in ts]
   tlens = [len(t) for t in tnames]
   ff.write('<table><tr>')
   ff.write('<th></th>')
   for d in days:
      ff.write('<th>'+str(d)[6:8]+'</th>')
   ff.write('<th>tot</th></tr><br>')
   for t in tss:
      ff.write('<tr><td>'+t['team_name']+'</td>')
      i=0
      sorted_days = sorted(t['days'],key=lambda t:int(t['daycode']))
      for d in sorted_days:
         ff.write('<td>'+str(int(d['pts']))+'</td>')
      ff.write('<td>'+str(int(t['pts_total']))+'</td></tr>')
   ff.write('</table>')



def OutputTablesToFile(filename,ts,bress):
   tls = ts
   vps = getVictoryPoints(ts)
   svps = sorted(vps,key=lambda k: k['pts_total'],reverse=True)
   sts = [x for (x,y) in sorted(zip(ts,vps),key=lambda k: k[1]['pts_total'],reverse=True)]   
   #stsToday = [x for (x,y) in sorted(zip(tsToday,vps),key=lambda k: k[1]['total'],reverse=True)]

   ii = 0
   for svi in svps:
      m5s = scoreSingle([x['pts_total'] for x in svps],ii)      
      svi['through_five'] = svi['mtotal'] + m5s
      svi['m5'] = m5s
      ii = ii+1
   ff = open(filename,'wb')
   #   ff.write('teams<br>')
   #   printDictList(ff,sts,['team_name','runs_for_team','runs_against_team','error_team'])
   #   ff.flush()
   ff.write('<BR><BR>Stats<BR>')

   printVerboseTable(ff,ts)
   ff.write('<BR><BR>Concise Stats<BR>')
   printConciseTable(ff,ts)

   #ff.write('<BR><BR>Total Day Points<BR>')
   #printDictList(ff,sts,['team_name','pts_total'])
                         
   #ff.flush()
   #ff.write('<BR><BR>Monthly Points<BR>')
   #printDictList(ff,svps,['team_name','pts_total'])

#   ff.write('<BR><BR>Today Stats<BR>')
#   printDictList(ff,stsToday,['team_name','tb','runs','sb','sacsf','bb','qs','runs-a','saves','holds','so'])

   ff.write('<BR><BR>Season scores As of Today:<BR>')

   ssvps = sorted(svps,key=lambda k: k['through_five'],reverse=True)
   printDictList(ff,ssvps,['team_name','m1','m2','m3','m4','m5','through_five'])
   ff.write('<BR>Detailed Results:<BR>')
   ff.write("<a href='all.txt'> here </a><BR><BR>")

   ff.write(str(datetime.now()))

   ff.close()
   #printFilesForTeams(ts,press,bress)
   ff = open('/home/eddie7/code/wb4m5/all.txt','wb')
   writeTeamInfo_wb4m5(ff,ts)
   ff.close()
#   printDictListCSV(ff,ress,['team','game_id','runs_for','h','d','t','hr','tb','bb','sb','sac','sf','sacsf','runs_against','qs','so','saves','holds','batting_team','pitching_team'])
#   printDictListCSV(ff,ress)
#   ff.close()


def d2s(d):
   return datetime.strftime(d,'%Y_%m_%d')


def DoTheDay():
   today = datetime.now()
   today = today.date()
   start_date = date(2015,8,3)
   end_date = date(2015,8,31)
   end_date = min(end_date,today)
   ts,bress = getFilledTeams(d2s(start_date),d2s(end_date))
#   tsToday,rignore = getFilledTeams(d2s(end_date),d2s(end_date))
   OutputTablesToFile('/home/eddie7/code/wb5m1/stats_wb5m1.html',ts,bress)

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

def AtBatHasRISP(ab):
   runners = ab.findall('runner')
   if len(runners) < 1:
      return False
   risps = [r for r in runners if r.attrib['start'] == '2B' or r.attrib['start'] == '3B']
   return len(risps) > 0


def ExtractPitcherABinfo(gg):
   try:
      root= gg.getroot()
   except:
      return []
   atbats = [atbat for atbat in root.iter('atbat')]
   pitcher_info = [{'id':x.attrib['pitcher'],'event':x.attrib['event']} for x in atbats]
   return pitcher_info

def hitsFromAtBats(player,atbats):
   hitstrings = ['Single','Double','Triple','Home Run']
   hitlist = [x for x in atbats if player==x['id'] and x['event'] in hitstrings]
   return len(hitlist)

def atbatsFromAtBats(player,atbats):
   notab = ['Walk','Intent Walk', 'Catcher Interference','Sac Fly','Hit By Pitch','Sac Bunt','Sac Fly DP','Runner Out','Sacrifice Bunt DP']
   ablist = [x for x in atbats if player==x['id'] and x['event'] not in notab]
   return len(ablist)

def ExtractBatterRISPInfo(gg):
   try:
      root= gg.getroot()
   except:
      return []
   atbats = [atbat for atbat in root.iter('atbat')]
   abrisp = [x for x in atbats if AtBatHasRISP(x)]
   batter_info = [{'id':x.attrib['batter'],'event':x.attrib['event']} for x in abrisp]
   return batter_info

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
   batters = []
   gameids = DateGames(date)
   for g in gameids:
      print 'Doing game ' + g
      jsonbox = GetGameBoxScoreJson(g)
      if not jsonbox is None:
         bs = ExtractPlayerInfo(jsonbox)
         if (len(bs) >0):
            batters.extend(bs)
   return batters

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
   bres = []
   pdate1 = datetime.strptime(date1,'%Y_%m_%d').date()
   pdate2 = datetime.strptime(date2,'%Y_%m_%d').date()
   if pdate2 < pdate1:
      raise Exception('date2 must be at or after date1')
   oneday = timedelta(1)
   thedate = pdate1
   while thedate <=pdate2:
      print 'Doing games for date ' + str(thedate)
      bs = CompileDayGames(thedate.strftime('%Y_%m_%d'))
      if len(bs) > 0:
         bres.extend(bs)
      thedate = thedate+oneday
   return bres

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

