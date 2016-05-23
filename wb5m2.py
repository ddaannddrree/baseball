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
from gd2functions import *
from wbhelpers import *

#codehome = "/home/eddie7/code/"
codehome = "/Users/martin/Baseball/WhiskeyBall/Code/"
monthfolder = "wb5m2/"

def getVictoryPoints(ts):
   #return a list of dictonaries with the season-point scores
   #PA, BB%-K%, wOBA, wSB
   #IP, K%-BB%, FIP, LOB%
   fnames_for_scoring = ['team','pa','bbnk','woba','wsb','def','ip','knbb','fip','lob','sd-md','total']

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

def getFilledTeams(date1,date2):
    ts = getTeams()
    (press,bress) = CompileRangeGames(date1,date2) 
    for t in ts:
        #print 'doing', t['team_name']
        
        pits = [p['id'] for p in t['pitchers']]
        bats = [b['id'] for b in t['batters']]
                
        mysum=lambda players,label,llist:sum([int(x[label]) for x in llist if int(x['id']) in players])
        myrepsum=lambda id,label,llist,start,end:sum([int(x[label]) for x in llist if id == int(x['id']) and GameInRange(x['gid'],start,end)])
        hitlabels = [x for x in bress[0].keys() if x not in ['id','gid']]
        pitlabels = [x for x in press[0].keys() if x not in ['id','gid']]
        hitstats = {}
        pitstats = {}
        
        # get player stats
        for label in hitlabels:
            hitstats[label] = mysum(bats,label,bress)
        for label in pitlabels:
            pitstats[label] = mysum(pits,label,press)
        
        # add replacement stats
        for rep in t['replacements']:
            repend = rep['end'] if 'end' in rep else date.today().strftime('%Y/%m/%d')
            for label in hitlabels:
                hitstats[label] += myrepsum(rep['id'],label,bress,rep['start'],repend)
        
        t['pitstats'] = pitstats
        t['hitstats'] = hitstats
        
        #Now make the actual stats
        hs = hitstats
        ps = pitstats
        hs['singles'] = hs['hits'] - hs['hr'] - hs['triples'] - hs['doubles']
        
        # get def diffs
        defense = 0.0
        batnames = [b['name'] for b in t['batters']]  
        repnames = [r['name'] for r in t['replacements']]
        
        # get current def info from fangraphs using very specific url
        url = "http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,199&season=2016&month=33&season1=2016&ind=0&team=0&rost=0&age=0&filter=&players=6195,4810,3516,8370,5038,10847,1887,7287,3410,10199,11368,9166,9776,639,3531,9847,4949,11477,13624,5000,9218,8203,15429,17182,9272,2434,4940,2151,7870,1908,7435,11493,6310,13611,8347,9077,7739,15676,9810,8090,12161,6184,13110,4727,5361,3256,1744,12282,9368,12916,10155,7859,9241,5209,7007,3473,5417,9777,14162,12701,8252,4106,11205,7304,4314,3269,13836,5343,11579,12856,4062,16376,13510,3395,13807,6073&page=1_80"
        soup = BeautifulSoup(urllib2.urlopen(url), "html.parser")
        table = soup.find("table", id="LeaderBoard1_dg1_ctl00")
        body = table.find("tbody")
        rows = body.find_all("tr")
        
        # make defBatters list of dictionaries
        defBatters = []
        for row in rows:
            data = row.find_all("td")
            defBatters.append({'name':data[1].a.string,'def':float(data[-1].string)})
            
        # calculate Def difference from base Defs
        for batter in defBatters:
            if batter['name'] in batnames:
                defense += batter['def'] - [x['basedef'] for x in t['batters'] if x['name'] == batter['name']][0]
                defense = round(defense, 1)
            # not an else because player could be both starter and replacement
            if batter['name'] in repnames:
                defense += batter['def'] - [x['basedef'] for x in t['replacements'] if x['name'] == batter['name']][0]
                defense = round(defense, 1)
         
        # set the stat       
        t['def'] = defense      
        
        # hitting stats
        t['pa'] = hs['pa']
        if float(hs['pa']) == 0:
            t['bbnk'] = -100
        else:
            t['bbnk'] = round((hs['bb'] - hs['so']) / float(hs['pa']), 5)
        if hs['ab'] + hs['bb'] - hs['ibb'] + hs['sf'] + hs['hbp'] == 0:
            t['woba'] = 0
        else:
            t['woba'] = round((0.689 * (hs['bb'] - hs['ibb']) + 0.721 * hs['hbp'] + 0.884 * hs['singles'] + 1.261 * hs['doubles'] + 
            1.6 * hs['triples'] + 2.073 * hs['hr']) / float(hs['ab'] + hs['bb'] - hs['ibb'] + hs['sf'] + hs['hbp']), 5)
        t['wsb'] = round(0.2 * hs['sb'] - 0.391 * hs['cs'] - 0.00122 * (hs['singles'] + hs['bb'] + hs['hbp'] - hs['ibb']), 5)
        
        # pitching stats
        t['ip'] = round(int(ps['out']) / 3.0, 3)
        if ps['bf'] == 0:
            t['knbb'] = -100
        else:
            t['knbb'] = round((ps['so'] - ps['bb']) / float(ps['bf']), 5)
        if ps['out'] == 0:
            t['fip'] = -30
        else:
            t['fip'] = -round((13 * ps['hr'] + 3 * (ps['bb'] + ps['hbp']) - 2 * ps['so']) / float(t['ip']) + 3.059, 5)
        if ps['ha'] + ps['bb'] + ps['hbp'] - 1.4 * ps['hr'] == 0:
            t['lob'] = 0
        else:
            t['lob'] = round((ps['ha'] + ps['bb'] + ps['hbp'] - ps['ra']) / float(ps['ha'] + ps['bb'] + ps['hbp'] - 1.4 * ps['hr']), 5)
        t['sd-md'] = ps['sd'] - ps['md']

    #print ts
    return ts,press,bress

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

def getPitchingRawEvents(press, t):
   pits = [p['id'] for p in t['pitchers']]
   actives = [x for x in press if int(x['id']) in pits]
   players = loadCSVDict(codehome + 'players2016.csv')
   for a in actives:
      a['player_name'] = players[a['id']]['mlb_name']
   return actives
      
def getBattingRawEvents(bress, t):
   bats = [b['id'] for b in t['batters']]
   reps = [r['id'] for r in t['replacements']]
   actives = [x for x in bress if int(x['id']) in bats or int(x['id']) in reps]
   players = loadCSVDict(codehome + 'players2016.csv')
   for a in actives:
      a['player_name'] = players[a['id']]['mlb_name']
   return actives

def getTeams():
    team_names = ['Drumpfallacious','No-Talent Ass Clowns', 'Portlandia Misfits', 'The Rube', 'Paly Players', 'Dr. Watson', 'Buena Vista Bottoms', 'Damnedest of the Nice']
    players = loadCSVDict(codehome + 'players2016.csv')

    pitchers = [];
    pitchers.append([453562, 607067, 544931, 502154, 519326, 467008])#brad
    pitchers.append([518516, 543037, 605228, 518553, 606965, 453192])#brent
    pitchers.append([592789, 592826, 594798, 501789, 593576, 444468])#scott
    pitchers.append([425844, 452657, 519242, 476454, 547973, 502085])#John
    pitchers.append([430935, 518774, 433587, 451584, 573109, 474521])#jesse
    pitchers.append([477132, 500779, 425794, 592102, 521230, 503285])#dave
    pitchers.append([446372, 453286, 547888, 445276, 518886, 572096])#martin
    pitchers.append([502042, 572971, 456034, 544727, 453343, 434718])#tom

    batters = [];
    batters.append([456078,408234,596059,446334,596019,453568,516782,545361,460086])#brad
    batters.append([425877,519203,514888,571448,621043,488726,542993,452254,594809])#brent
    batters.append([521692,458015,429664,622110,543063,451594,547180,543807,624424])#scott
    batters.append([435263,543333,456030,518626,592743,430832,460075,471865,571740])#john
    batters.append([519390,502671,543829,592178,628356,443558,448801,518792,429665])#jesse
    batters.append([518735,457763,543401,134181,453064,457705,519317,592885,608369])#dave
    batters.append([518960,408236,450314,592518,444876,605141,456715,452655,435079])#martin
    batters.append([518595,547989,572821,572761,593428,493316,453056,502110,518692])#tom
    
    # keep track of replacements here - better in a csv file?
    replacements = []
    replacements.append([])#brad
    replacements.append([{'id':608070,'name':'Jose Ramirez','basedef':1.9,'start':'2016/05/10'}])#brent
    replacements.append([])#scott
    replacements.append([{'id':460060,'name':'Cliff Pennington','basedef':1.3,'start':'2016/05/09'},{'id':453895,'name':'Brendan Ryan','basedef':0.1,'start':'2016/05/13'}])#john
    replacements.append([])#jesse
    replacements.append([])#dave
    replacements.append([])#martin
    replacements.append([{'id':608700,'name':'Kevin Plawecki','basedef':2.0,'start':'2016/05/07'}])#tom
    
    # Def values from 5/7, when wb2 started, for def calculation
    basedefs = []
    basedefs.append([1.7,0.9,0.3,1.5,2.4,1.5,2.4,2.3,1.8])#brad
    basedefs.append([1.9,0.3,0.8,5.0,-3.3,0.5,0.3,-6.1,9.5])#brent
    basedefs.append([5.8,-1.9,2.1,2.1,6.8,1.9,1.2,1.2,-1.4])#scott
    basedefs.append([-0.4,-4.6,1.7,-0.8,5.3,-4.7,-5.6,-2.6,4.0])#john
    basedefs.append([1.2,-1.4,1.5,5.0,0,-2.6,-1.8,3.2,-3.3])#jesse
    basedefs.append([0.9,2.5,2.0,4.2,3.1,-2.0,-5.3,-3.2,3.6])#dave
    basedefs.append([-0.5,-3.8,0.5,4.0,0.5,-0.8,4.3,-4.5,0.4])#martin
    basedefs.append([0.0,-3.8,-1.7,-0.2,4.1,-1.0,0.3,-5.6,-2.7])#tom
    
    # points from month 1
    mtotals = [7,3.5,3.5,5,1,2,6,8]

    teams = []
    i=0
    for team_name in team_names:
       fbs = [];
       fps = [];
       j=0
       for b in batters[i]:
          player = players[str(b)]
          fbs.append({'name':player['mlb_name'],'id':b,'basedef':basedefs[i][j]})
          j+=1
       for p in pitchers[i]:
          player = players[str(p)]
          fps.append({'name':player['mlb_name'],'id':p})
       teams.append({'team_name':team_name, 'batters':fbs, 'pitchers':fps, 'replacements':replacements[i], 'm1':mtotals[i], 'mtotal':mtotals[i]})
       i=i+1
    return teams

def makePitcherDict(pp,p_hrhbp,pitcher_mdsd,gid):
   pit = {}
   pit['id'] = pp['id']
   pit['out'] = pp['out']
   pit['bf'] = pp['bf']
   pit['bb'] = pp['bb']
   pit['so'] = pp['so']
   pit['ha'] = pp['h']
   pit['ra'] = pp['r']
   pit['hr'] = len([x for x in p_hrhbp if x['id'] == pp['id'] and x['hr'] > 0])
   pit['hbp'] = len([x for x in p_hrhbp if x['id'] == pp['id'] and x['hbp'] > 0])
   #pit['sd'] = pitcher_mdsd[0][pp['name_display_first_last']] if pp['name_display_first_last'] in pitcher_mdsd[0] else 0
   pit['sd'] = 1 if pp['name_display_first_last'] in pitcher_mdsd[0] else 0
   #pit['md'] = pitcher_mdsd[1][pp['name_display_first_last']] if pp['name_display_first_last'] in pitcher_mdsd[1] else 0
   pit['md'] = 1 if pp['name_display_first_last'] in pitcher_mdsd[1] else 0
   pit['gid'] = gid
   return pit
   
def makeBatterDict(bb,batter_ibb,gid):
   bat = {}
   bat['id'] = bb['id']
   bat['pa'] = int(bb['ab']) + int(bb['bb']) + int(bb['hbp']) + int(bb['sf']) + int(bb['sac'])
   bat['ab'] = bb['ab']
   bat['bb'] = bb['bb']
   bat['so'] = bb['so']
   bat['hbp'] = bb['hbp']
   bat['hits'] = bb['h']
   bat['doubles'] = bb['d']
   bat['triples'] = bb['t']
   bat['hr'] = bb['hr']
   bat['sf'] = bb['sf']
   bat['sac'] = bb['sac']
   bat['sb'] = bb['sb']
   bat['cs'] = bb['cs']
   bat['ibb'] = len([x for x in batter_ibb if x == bb['id']])
   bat['gid'] = gid
   return bat

def ExtractPlayerInfo(gg,batter_ibb,p_hrhbp,pitcher_mdsd):
    batters = []
    pitchers = []
    # F[x] after game that counts, I during game
    # Anything starting with F is a final.  Since I want a live update, I'm including I, which is presumable In Progress
    # The stats value of O seems to be in between I and F, maybe for Over, before everything is finalized.
    if gg['data']['boxscore']['status_ind'].startswith('F') or gg['data']['boxscore']['status_ind'] == 'I' or gg['data']['boxscore']['status_ind'] == 'O':
        bats = gg['data']['boxscore']['batting']
        bh = [b for b in bats if b['team_flag']=='home']
        ba = [b for b in bats if b['team_flag']=='away']
        hbats = bh[0]['batter']
        abats = ba[0]['batter']
        gid = gg['data']['boxscore']['game_id']
        h_batters = [makeBatterDict(bb,batter_ibb,gid) for bb in hbats]
        a_batters = [makeBatterDict(bb,batter_ibb,gid) for bb in abats]

        batters.extend(h_batters)
        batters.extend(a_batters)
      
        pits = gg['data']['boxscore']['pitching']
        ph = [p for p in pits if p['team_flag']=='home']
        pa = [p for p in pits if p['team_flag']=='away']
        hpits = ph[0]['pitcher']
        if type(hpits) is dict:
            hpits= [hpits]
        apits = pa[0]['pitcher']
        if type(apits) is dict:
            apits= [apits]

        h_pitchers = [makePitcherDict(pp,p_hrhbp,pitcher_mdsd,gid) for pp in hpits]
        a_pitchers = [makePitcherDict(pp,p_hrhbp,pitcher_mdsd,gid) for pp in apits]

        pitchers.extend(h_pitchers)
        pitchers.extend(a_pitchers)

    return (pitchers,batters)

def OutputTablesToFile(filename,ts,bress,press):
   tls = ts
   vps = getVictoryPoints(ts)
   svps = sorted(vps,key=lambda k: k['total'],reverse=True)
   sts = [x for (x,y) in sorted(zip(ts,vps),key=lambda k: k[1]['total'],reverse=True)]   
   #stsToday = [x for (x,y) in sorted(zip(tsToday,vps),key=lambda k: k[1]['total'],reverse=True)]

   ii = 0
   for svi in svps:
      m2s = scoreSingle([x['total'] for x in svps],ii)      
      svi['through_two'] = svi['mtotal'] + m2s
      svi['m2'] = m2s
      ii = ii+1
   ff = open(filename,'wb')
   ff.write('<BR><BR>Stats<BR><tt>')
   printDictList(ff,sts,['team_name','pa','bbnk','woba','wsb','def','ip','knbb','fip','lob','sd-md'])
   ff.write('</tt>')
   ff.flush()
   ff.write('<BR><BR>Points<BR>')
   printDictList(ff,svps,['team_name','pa','bbnk','woba','wsb','def','ip','knbb','fip','lob','sd-md','total'])

   ff.write('<BR><BR>Season scores As of Today:<BR>')

   ssvps = sorted(svps,key=lambda k: k['through_two'],reverse=True)
   printDictList(ff,ssvps,['team_name','m1','m2','through_two'])
   ff.write('<BR><BR>')
   #ff.write("<a href='all.csv'> all.csv </a><BR><BR>")
   
   # provide links to all teams' batter and pitcher stat files
   ff.write("<a href='BuenaVistaBottoms_batters.csv'> BVBD batters </a><BR>")
   ff.write("<a href='BuenaVistaBottoms_pitchers.csv'> BVBD pitchers </a><BR>")
   ff.write("<a href='DamnedestoftheNice_batters.csv'> NOD batters </a><BR>")
   ff.write("<a href='DamnedestoftheNice_pitchers.csv'> NOD pitchers </a><BR>")
   ff.write("<a href='Dr.Watson_batters.csv'> Watson batters </a><BR>")
   ff.write("<a href='Dr.Watson_pitchers.csv'> Watson pitchers </a><BR>")
   ff.write("<a href='Drumpfalicious_batters.csv'> Trumpies batters </a><BR>")
   ff.write("<a href='Drumpfalicious_pitchers.csv'> Trumpies pitchers </a><BR>")
   ff.write("<a href='No-TalentAssClowns_batters.csv'> Ass Clowns batters </a><BR>")
   ff.write("<a href='No-TalentAssClowns_pitchers.csv'> Ass Clowns pitchers </a><BR>")
   ff.write("<a href='PalyPlayers_batters.csv'> Players batters </a><BR>")
   ff.write("<a href='PalyPlayers_pitchers.csv'> Players pitchers </a><BR>")
   ff.write("<a href='PortlandiaMisfits_batters.csv'> Misfits pitchers </a><BR>")
   ff.write("<a href='PortlandiaMisfits_pitchers.csv'> Misfits pitchers </a><BR>")
   ff.write("<a href='TheRube_batters.csv'> Rube batters </a><BR>")
   ff.write("<a href='TheRube_pitchers.csv'> Rube pitchers </a><BR>")

   ff.write('<BR><BR>')
   ff.write(str(datetime.now()))

   ff.close()
   printFilesForTeams(ts,press,bress)
   
   #ff = open(codehome + monthfolder + 'all.csv','wb')
   #printDictListCSV(ff,ress,['team','game_id','runs_for','h','d','t','hr','tb','bb','sb','sac','sf','sacsf','runs_against','qs','so','saves','holds','batting_team','pitching_team'])
   #printDictListCSV(ff,ress)
   #ff.close()
      
def getHRandHBPfromAB(ab):
    hr = 1 if "Home Run" in ab.attrib['event'] else 0
    hbp = 1 if "Hit By Pitch" in ab.attrib['event'] else 0
    if hr>0 or hbp>0:
        return {'id':ab.attrib['pitcher'],'hr':hr,'hbp':hbp}
    else:
        return None
        
def getFullTeamName(teamcode):
    teamMapping = {'ana':'Angels', 'ari':'Diamondbacks', 'atl':'Braves', 'bal':'Orioles', 'bos':'Red Sox', 'cha':'White Sox',
                    'chn':'Cubs', 'cin':'Reds', 'cle':'Indians', 'col':'Rockies', 'det':'Tigers', 'hou':'Astros', 'kca':'Royals',
                    'lan':'Dodgers', 'mia':'Marlins', 'mil':'Brewers', 'min':'Twins', 'nya':'Yankees', 'nyn':'Mets', 'oak':'Athletics',
                    'phi':'Phillies', 'pit':'Pirates', 'sdn':'Padres', 'sea':'Mariners', 'sfn':'Giants', 'sln':'Cardinals', 'tba':'Rays',
                    'tex':'Rangers', 'tor':'Blue Jays', 'was':'Nationals'}
    return teamMapping[teamcode]
    
def ExtractMDSD(curdate,g):
    mdsd = []
    sdd = []
    mdd = []
    urldate = curdate.replace('_','-')
    # can get both team's results from one page
    team = urllib.quote(getFullTeamName(g[11:14]))
    gamenum = g[-1:]
    dh = "0" if gamenum == "1" else "2"
    url = "http://www.fangraphs.com/liveboxscore.aspx?date=%s&team=%s&dh=%s&season=2016" % (urldate, team, dh)
    try:
        page = urllib2.urlopen(url)
    except:
        print "couldn't open", url
        sys.stdout.flush()
        return [[],[]]
    soup = BeautifulSoup(page, "html.parser")
    if soup.head.title.string[3:8] == "Error":
        # maybe it's the first game of a double header
        newurl = url.replace("dh=0", "dh=1")
        try:
            page = urllib2.urlopen(newurl)
            soup = BeautifulSoup(page, "html.parser")
            if soup.head.title.string[3:8] == "Error":
                print "Error page:", url
                sys.stdout.flush()
                return [[],[]]
        except:
            print "couldn't open", url, newurl
            sys.stdout.flush()
            return [[],[]]
    tables = soup.find_all("table", id=re.compile('LiveBox1_dg6[ha]p_ctl00'))
    if len(tables) == 0:
        tables = soup.find_all("table", id=re.compile('WinsBox1_dg6[ha]p_ctl00'))
    for table in tables:
        body = table.find("tbody")
        rows = body.find_all("tr")
        for row in rows:
            data = row.find_all("td")
            if data[0].string == "Total":
                break
            # sometimes there's no link
            if data[0].a is None:
                name = data[0].string
            else:
                name = data[0].a.string
            sd = int(data[-2].string)
            md = int(data[-1].string)                
            if sd > 0:
                sdd.append(name)
            if md > 0:
                mdd.append(name)
    mdsd.append(sdd)
    mdsd.append(mdd)
    return mdsd
   
def ExtractBatterIBB(gg):
    try:
        root = gg.getroot()
    except:
        return []
    atbats = [atbat for atbat in root.iter('atbat')]
    batter_info = [x.attrib['batter'] for x in atbats if "Intent Walk" in x.attrib['event']]
    return batter_info
   
def ExtractPitcherABHBP(gg):
    try:
        root= gg.getroot()
    except:
        return []
    atbats = [atbat for atbat in root.iter('atbat')]
    pitcher_info = [getHRandHBPfromAB(x) for x in atbats if getHRandHBPfromAB(x) is not None]
    return pitcher_info
    
def addMDSDToCSV(date,key,sd,md):
    fieldnames = ['date', 'key', 'name']
    with open(codehome + 'sd.csv', 'ab+') as csvfile:
        sdwriter = csv.DictWriter(csvfile, delimiter = ',', fieldnames=fieldnames)
        if csvfile.tell() == 0:
            sdwriter.writeheader()
        for pitcher in sd:
            sdwriter.writerow({'date':date,'key':key,'name':pitcher})
    with open(codehome + 'md.csv', 'ab+') as csvfile:
        mdwriter = csv.DictWriter(csvfile, delimiter = ',', fieldnames=fieldnames)
        if csvfile.tell() == 0:
            mdwriter.writeheader()
        for pitcher in md:
            mdwriter.writerow({'date':date,'key':key,'name':pitcher})

def CompileDayGames(curdate):
    batters = []
    pitchers = []
    
    sd = loadCSV(codehome + 'sd.csv')
    md = loadCSV(codehome + 'md.csv')
    maxdate = 0
    if len(sd) > 0:
        maxdate = max([x['date'] for x in sd])    
    today = date.today().strftime('%Y_%m_%d')
        
    gameids = DateGames(curdate)
    for g in gameids:
        print 'Doing game ' + g
        sys.stdout.flush()
        jsonbox = GetGameBoxScoreJson(g)
        if not jsonbox is None:
            sdd = [x['name'] for x in sd if x['date'] == curdate and x['key'] == g]
            mdd = [x['name'] for x in md if x['date'] == curdate and x['key'] == g]
            innings_all = GetGame(g)
            batter_ibb = ExtractBatterIBB(innings_all)
            p_hrhbp = ExtractPitcherABHBP(innings_all)
            
            if curdate <= maxdate:
                pitcher_mdsd = [sdd,mdd]
            else:
                pitcher_mdsd = ExtractMDSD(curdate,g)
         
            (ps,bs) = ExtractPlayerInfo(jsonbox,batter_ibb,p_hrhbp,pitcher_mdsd)
            if (len(ps) > 0):
                pitchers.extend(ps)
            if (len(bs) > 0):
                batters.extend(bs)
            
            if curdate < today and curdate > maxdate:
                addMDSDToCSV(curdate, g, pitcher_mdsd[0], pitcher_mdsd[1])
            
    return (pitchers,batters)

def CompileRangeGames(date1,date2):
    pres = []
    bres = []
    pdate1 = datetime.strptime(date1,'%Y_%m_%d').date()
    pdate2 = datetime.strptime(date2,'%Y_%m_%d').date()
    if pdate2 < pdate1:
        raise Exception('date2 must be at or after date1')
    oneday = timedelta(1)
    thedate = pdate1
    while thedate <= pdate2:
        print 'Doing games for date ' + str(thedate)
        sys.stdout.flush()
        (ps,bs) = CompileDayGames(thedate.strftime('%Y_%m_%d'))
        if len(ps) > 0:
            pres.extend(ps)
        if len(bs) > 0:
            bres.extend(bs)
        thedate = thedate+oneday
    return (pres,bres)  

def DoTheDay():
    today = datetime.now()
    today = today.date()
    start_date = date(2016,5,7)
    end_date = date(2016,6,6)
    #end_date = date(2016,5,10)
    end_date = min(end_date,today)
    ts,press,bress = getFilledTeams(d2s(start_date),d2s(end_date))
    OutputTablesToFile(codehome + monthfolder + 'stats_wb5m2.html',ts,bress,press)