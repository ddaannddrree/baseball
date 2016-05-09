import wb4m4
import wb4m4_all
import os

wb4m4.DoTheDay()
wb4m4_all.DoTheDay()
#Now cp stuff to my web page

os.system('sshpass -p f4m1n3G4m3 scp -o User=dandre -o StrictHostKeyChecking=no /home/eddie7/code/wb4m4/* shinteki.com:public_html/davidandre/wb/')
