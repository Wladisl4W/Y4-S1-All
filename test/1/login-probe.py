import requests
from bs4 import BeautifulSoup
u='https://the-internet.herokuapp.com/login'
r=requests.get(u,timeout=15);s=BeautifulSoup(r.text,'html.parser')
print('URL',r.url,'HTTP',r.status_code)
for name in ['username','password']:
 e=s.select_one(f'input[name="{name}"]')
 print(name,'present',bool(e),'type',e.get('type') if e else None)
print('login button',bool(s.select_one('button[type="submit"]')))
print('forgot password link',bool(s.select_one('a[href*="forgot"]')))
