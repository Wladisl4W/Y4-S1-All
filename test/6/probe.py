import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
root='https://demowebshop.tricentis.com'
s=requests.Session()
for path in ['/','/books','/search?q=Computing']:
 r=s.get(root+path,timeout=15)
 soup=BeautifulSoup(r.text,'html.parser')
 title=soup.select_one('title')
 print('PAGE',path,'HTTP',r.status_code,'TITLE',title.get_text(' ',strip=True) if title else '?')
 if path=='/books':
  links=[a for a in soup.select('.product-title a') if a.get('href')]
  print('PRODUCTS',len(links))
  if links:
   a=links[0];u=urljoin(root,a['href']);d=s.get(u,timeout=15);ds=BeautifulSoup(d.text,'html.parser')
   print('FIRST PRODUCT',a.get_text(' ',strip=True),'URL',u,'HTTP',d.status_code)
   print('PRICE',ds.select_one('.product-price').get_text(' ',strip=True) if ds.select_one('.product-price') else 'not found')
 if path.startswith('/search'):
  print('SEARCH PRODUCTS',len(soup.select('.product-title a')))
  print('NAMES',[a.get_text(' ',strip=True) for a in soup.select('.product-title a')[:5]])
