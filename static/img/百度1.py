from urllib.request import *
from bs4 import BeautifulSoup
import re
#url = input('pls type a url:')
#if url == '':
#url = "http://image.baidu.com/search/index?tn=baiduimage&ipn=r&ct=201326592&cl=2&lm=-1&st=-1&fm=index&fr=&sf=1&fmq=&pv=&ic=0&nc=1&z=&se=1&showtab=0&fb=0&width=&height=&face=0&istype=2&ie=utf-8&word=%E7%BE%8E%E5%A5%B3&oq=%E7%BE%8E%E5%A5%B3&rsp=-1#z=0&pn=&ic=0&st=-1&face=0&s=0&lm=-1"
url = input('请输入你要爬取的图片链接：')
html = urlopen(url)
#obj = BeautifulSoup(html.read(),'html.parser')
obj = html.read().decode()
#urls = re.findall(r'"objURL":"(.*?)"',str(obj))
urls = re.findall(r'"objURL":"(.*?)"',obj)
index = 0
for url in urls:
	if index <=6:
		try:
			print('Downloading...%d'%(index))
			urlretrieve(url,str(index)+'.png')
			index += 1
		except Exception:
			print('Downloading Failed%d'%(index))
		finally:
			print('Downloading Complete')
	else:
		break
