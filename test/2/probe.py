import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
s=requests.Session(); root='https://the-internet.herokuapp.com'
for path in ['/broken_images','/status_codes/500','/typos']:
 try:
  r=s.get(root+path,timeout=12)
  print(path, 'HTTP',r.status_code,'URL',r.url)
  soup=BeautifulSoup(r.text,'html.parser')
  if path=='/broken_images':
   for i,img in enumerate(soup.select('img'),1):
    u=urljoin(r.url,img.get('src',''));x=s.get(u,timeout=12)
    print('image',i,u,'HTTP',x.status_code,'type',x.headers.get('content-type'))
  if path=='/typos':
   for p in soup.select('p'): print('paragraph',p.get_text(' ',strip=True))
 except Exception as e: print(path,type(e).__name__,str(e))
