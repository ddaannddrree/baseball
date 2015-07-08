import daily_gameday
import os

daily_gameday.DoTheDay()
#Now cp stuff to my web page

os.system('sshpass -p m4k31tB3tt3r scp -o User=dandre -o StrictHostKeyChecking=no /home/eddie7/code/wb3m4/all.csv shinteki.com:public_html/davidandre/wb/')
os.system('sshpass -p m4k31tB3tt3r scp -o User=dandre -o StrictHostKeyChecking=no /home/eddie7/code/wb3m4/stats.html shinteki.com:public_html/davidandre/wb/')
