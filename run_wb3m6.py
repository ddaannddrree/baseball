import wb3m6
import os

wb3m6.DoTheDay()
#Now cp stuff to my web page

os.system('sshpass -p m4k31tB3tt3r scp -o User=dandre -o StrictHostKeyChecking=no /home/eddie7/code/wb3m6/stats_wb3m6.html shinteki.com:public_html/davidandre/wb/')
