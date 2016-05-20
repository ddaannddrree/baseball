#!/usr/bin/python

import csv
from datetime import datetime

def d2s(d):
   return datetime.strftime(d,'%Y_%m_%d')

def scoreSingle(v,i):
   x = v[i]
   res = 0.5 + sum( [float(x > y) for y in v]) + 0.5*sum([float(x==y) for y in v])
   return res

def loadCSV(filename):
    try:
        with open(filename,'rU') as csvfile:
            reader = csv.DictReader(csvfile)
            kept2 = [row for row in reader]    
        return kept2
    except:
        return []

def loadCSVDict(filename):
   the_list = loadCSV(filename)
   my_dict = {x['mlb_id']:x for x in the_list}
   return my_dict

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
   #print len(dlist)
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
