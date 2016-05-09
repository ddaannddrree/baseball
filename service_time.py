import urllib2
from urllib2 import urlopen
import xml.etree.ElementTree as ET
import datetime
from bs4 import BeautifulSoup
import re
import csv
import time
from datetime import date
import pytz
import gspread 

def getServiceTime(bref_str):
    print bref_str
    url = 'http://www.baseball-reference.com/players/' + bref_str[0] + '/' + bref_str + '.shtml'
    soup = BeautifulSoup(urlopen(url))
    st = soup.find(text=re.compile('Service Time'))
    if st is not None:
        x = st.next_element.next_element.next_element
        return float(x[2:-2])
    else:
        return -1
    

def getRookieYear(bref_str):
    print bref_str
    url = 'http://www.baseball-reference.com/players/' + bref_str[0] + '/' + bref_str + '.shtml'
    soup = BeautifulSoup(urlopen(url))
    st = soup.find(text=re.compile('Rookie Status'))
    if st == None:
        return 0
    strs = st.next_element.next_element.split(' ')
    if (strs[1] == 'Exceeded'):
        year = int(strs[5])
        years_since = 2015-year
    else:
        years_since = 0
    return years_since

def loadCSV(filename):
    with open(filename,'rU') as csvfile:
        reader = csv.DictReader(csvfile)
        kept2 = [row for row in reader]    
    return kept2

def getSBA():
    teams = ['Pierzinskis Misspelled D-Bags','No-Talent Ass Clowns', 'Portlandia Misfits', 'The Rube', 'Paly Players', 'Dr. Watson', 'Buena Vista Bridesmaids', 'Damnedest of the Nice']

    pitchers =[];
    pitchers.append([['Cody','Allen'],['Grant','Balfour'],['Glen','Perkins'],['Fernando','Rodney'],['Chris','Sale'],['Max','Scherzer']])
    pitchers.append([['Steve','Cishek'],['Johnny','Cueto'],['Clayton','Kershaw'],['Cliff','Lee'],['Jeff','Samardzija'],['Rafael','Soriano']])
    pitchers.append([['Dillon','Gee'],['Craig','Kimbrel'],['Addison','Reed'],['Francisco','Rodriguez'],['Alfredo','Simon'],['Huston','Street']])
    pitchers.append([['Madison','Bumgarner'],['Gerrit','Cole'],['Jose','Fernandez'],['Zack','Greinke'],['Hector','Rondon'],['Michael','Wacha']])
    pitchers.append([['Felix','Hernandez'],['Greg','Holland'],['Phil','Hughes'],['Justin','Masterson'],['Joe','Nathan'],['Joakim','Soria']])
    pitchers.append([['Kenley','Jansen'],['Ian','Kennedy'],['Mike','Minor'],['Stephen','Strasburg'],['Adam','Wainwright'],['Travis','Wood']])
    pitchers.append([['Steve','Delabar'],['Danny','Farquhar'],['Luke','Gregerson'],['Tommy','Hunter'],['Matt','Lindstrom'],['Koji','Uehara']])
    pitchers.append([['John','Axford'],['David','Price'],['David','Robertson'],['James','Shields'],['Justin','Verlander'],['C.J.','Wilson']])
    

    n = datetime.datetime.now()
    startdate = datetime.datetime(2014,5,6)
    td = n-startdate
    
    baseURL = 'http://www.baseball-reference.com/leagues/daily.cgi?user_team=&bust_cache=&type=p&dates=lastndays&lastndays='   #set URL beginning
    
    fullURL = baseURL + str(td.days) + '&level=mlb&franch=&stat=b%3ASB&stat_value=1#daily::none' #construct full URL for the query

    print 'Using ndays ' + str(td.days)
    
    soup = BeautifulSoup(urllib2.urlopen(fullURL))
    table = soup.find('table');
    # find the header info
    th = table.find_all("th")
    datastats = [h['data-stat'] for h in th]
    player_index = datastats.index('player')
    sb_index = datastats.index('SB')
    # get the players and sbas
    rows = table.find_all('tr')
    players = [tds[player_index].get_text() for tds in [row.find_all('td') for row in rows[1:]] if len(tds) > 0]
    sbas = [tds[sb_index].get_text() for tds in [row.find_all('td') for row in rows[1:]] if len(tds) > 0]

    #now, loop over teams, loop over players,update to the spreadsheet...


    gs = gspread.login('dandreauto@gmail.com','841Melissa5814')
    spreadsheet = gs.open('sba')
    pworksheet = spreadsheet.worksheet('players')
    tworksheet = spreadsheet.worksheet('teams')

    rows = pworksheet.row_count
    cols = pworksheet.col_count

#    for row in range(1,rows+1):
#        for col in range(1,3):
#            pworksheet.update_cell(row,col,'')    
    pworksheet.update_cell(1,1,'player')
    pworksheet.update_cell(1,2,'sba')
    pworksheet.update_cell(1,3,'today')
    pworksheet.update_cell(2,3, n.strftime('%a %b %d %H:%M:%S'))
    pworksheet.update_cell(1,4,'ndays used in query')
    pworksheet.update_cell(2,4,str(td.days))


    rows = 10
    cols = tworksheet.col_count
#    for row in range(1,rows+1):
#        for col in range(1,3):
#            tworksheet.update_cell(row,col,'')    
    tworksheet.update_cell(1,1,'team')
    tworksheet.update_cell(1,2,'sba')
    tworksheet.update_cell(1,3,'now')
    tworksheet.update_cell(2,3, n.strftime('%a %b %d %H:%M:%S'))
    tworksheet.update_cell(1,4,'ndays used in query')
    tworksheet.update_cell(2,4,str(td.days))


    prow=2
    trow=2
    for team,ps in zip(teams,pitchers):
        sba_count = 0;
        for p in ps:
            try:
                sba_x = int(sbas[players.index(p[0]+' '+p[1])])
            except:
                sba_x = 0
                print 'Not in list'
            sba_count = sba_count+sba_x
            pworksheet.update_cell(prow,1,p[0]+' '+p[1])
            pworksheet.update_cell(prow,2,sba_x)
            prow = prow+1
            print 'player '+p[0]+' '+p[1]+' sba: '+str(sba_x)
        tworksheet.update_cell(trow,1,team)
        tworksheet.update_cell(trow,2,sba_count)
        print 'team '+team+' '+str(sba_count)
        trow= trow+1

def updateRecord(d):
    brefid = d['bref_id']
    if len(brefid) < 2:
        st = 0;
    else:
        st = getServiceTime(brefid)
        if (st < 0 or st > 30): 
            ry = getRookieYear(brefid)
            if (ry < 0 or ry > 30):
                ry = 0;
                st = ry
    d['wb_years'] = st
    return d


    
def main():
    dadata = loadCSV('master.csv')
    newdata = [updateRecord(d) for d in dadata]
    
    fieldnames = newdata[0].keys()
    with open('master_wb.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames,extrasaction='ignore')
        writer.writeheader()    
        for d in newdata:
            writer.writerow(d)

if __name__ == "__main__":
    main()
