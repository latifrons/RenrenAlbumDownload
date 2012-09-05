"""
Created on Jul 17, 2012

@author: latifrons88@gmail.com
"""

import cookielib
import os
import urllib
import urllib2
import json
import uuid
import renren
import sys
import getpass

_cookieJar = cookielib.CookieJar()
_homeURL = 'http://www.renren.com/'
_loginURL = 'http://www.renren.com/ajaxLogin/login'
_pingURL = 'http://s.renren.com/ping?v=20110919'
_captchaURL = 'http://icode.renren.com/getcode.do?t=web_login&rnd=331'
_showcaptchaURL = 'http://www.renren.com/ajax/ShowCaptcha'
_uaHeaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/535.12 (KHTML, like Gecko) Chrome/18.0.966.0 Safari/535.12')]

_normalOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor(_cookieJar))
_normalOpener.addheaders = _uaHeaders

def touch(url):
	req = urllib2.Request(url, None)
	resp = _normalOpener.open(req,timeout=5)
	resp.close()

def fetch(url,encoding='UTF-8'):
	req = urllib2.Request(url,None)
	resp = _normalOpener.open(req,timeout=5)
	s = resp.read().decode(encoding)
	resp.close()
	return s

def fetchBin(url,filename,folder):
	req = urllib2.Request(url,None)
	resp = _normalOpener.open(req,timeout =5)
	path = os.path.join(folder,filename)
	f = open(path,'wb')
	f.write(resp.read())
	resp.close()

def buildSimpleCookie(name,value,domain,path):
	ck = cookielib.Cookie(version=0, name=name, value = value,
						port=None, port_specified=False,
						domain=domain, domain_specified=True, domain_initial_dot=True,
						path=path, path_specified=True, secure=False, expires=None, discard=True,
						comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
	return ck

def login(email,password,captcha):
	#ajax login
	postBodyMap = {'email':email,'password':password,'icode':captcha,
			'origURL':'http://www.renren.com/home',
			'domain':'renren.com','key_id':1,'captcha_type':'web_login','_rtk':'ec5d8045'}
	postBody = urllib.urlencode(postBodyMap)

	req = urllib2.Request(_loginURL, postBody)

	resp = _normalOpener.open(req,timeout =5)

	loginResult = resp.read()
	print loginResult.decode('UTF-8')
	resp.close()

	#goto homeUrl
	js = json.JSONDecoder().decode(loginResult)
	success= js['code']
	homeURL = js['homeUrl']

	touch(homeURL)

	return success

def save(url,filename,folder,overwrite):
	path = os.path.join(folder,filename)
	pic = None
	f= None
	if not overwrite and os.path.exists(path):
		print url, 'skip'
		return True
	try:
		pic = urllib2.urlopen(url,timeout=5)
		print url, pic.getcode()
		f = open(path,'wb')
		f.write(pic.read())
		return True
	except Exception as e:
		print url, e
		return False
	finally:
		if pic is not None:
			pic.close()
		if f is not None:
			f.close()


def downloadAlbum(album):
	html = fetch(album.albumURL)
	b = renren.getPhotos(album,html)
	newAlbum = renren.getAlbumInfo(album.albumURL,html)
	album.albumName = newAlbum.albumName

	#username_230654960/albumname_id/photoid.type
	path = ''.join([album.ownerName,'_',album.ownerID,'/',album.albumName,'_',album.albumID,'/'])
	if not os.path.exists(path):
		os.makedirs(path)

	success = True
	for photo in b:
		type = photo.photoURL[photo.photoURL.rfind('.'):]
		success &= save(photo.photoURL,''.join([photo.photoID,type]),path,False)
	return success

def round():
	#get user request
	url = safe_raw_input('URL,UID or quit(q):')
	if url.lower() == 'quit' or url.lower() =='q':
		return False
	if url == '':
		return True
	albums = []
	fixedURL = renren.getAlbumListURL(url)
	if fixedURL is not None:
		#fetch albums html
		html = fetch(fixedURL)
		albums = renren.getAlbums(html)
	else:
		fixedURL = renren.getPhotoListURL(url)
		if fixedURL is not None:
			html = fetch(fixedURL)
			album = renren.getAlbumInfo(fixedURL,html)
			albums.append(album)

	#download each album
	ac = safe_raw_input('You are about to download %d albums from %s (%s). Press Y to continue or others to abort.'
	%(len(albums),albums[0].ownerName,albums[0].ownerID))
	success = True
	if ac.lower() == 'y':
		for album in albums:
			print 'Downloading %s (%d)' % (encode(album.albumName),album.picCount)
			try:
				success &= downloadAlbum(album)
			except Exception as e:
				print e
				success = False
		if success:
			print 'All %d albums from %s (%s) downloaded successfully.' \
				% (len(albums),encode(albums[0].ownerName),albums[0].ownerID)
		else:
			print 'Some photos were not downloaded properly. Please recheck.'
	return True

def encode(s,encoding=sys.stdout.encoding):
	if s is not None:
		s = s.encode(encoding,'ignore')
	return s

def safe_raw_input(prompt=None):
	if prompt is not None:
		prompt = prompt.encode(sys.stdout.encoding,'ignore')
		return raw_input(prompt)

if __name__ == '__main__':
	print ('''
	=================================================
	= Renren.com Album Bulk Downloader Ver 0.1 Beta =
	=               Author: latifrons               =
	=           www.renren.com/230654960            =
	=            latifrons88@gmail.com              =
	=================================================
	''')
	success = False
	while not success:
		try:
			username = safe_raw_input('Your RenRen Account (Email):')
			password = getpass.getpass('Your RenRen Password:')

			#visit home to get anonymous id
			touch(_homeURL)

			#ping twice to get ick id
			touch(_pingURL)

			#add random uuid to cookie
			_cookieJar.set_cookie(buildSimpleCookie('ick',str(uuid.uuid4()),'.renren.com','/'))
			touch(_pingURL)

			#ajax captcha
			fetchBin(_captchaURL,'captcha.jpg','')
			postBodyMap = {'email':username,'password':'','icode':'',
			               'origURL':'http://www.renren.com/home',
			               'domain':'renren.com','key_id':1,'captcha_type':'web_login','_rtk':'ec5d8045'}
			postBody = urllib.urlencode(postBodyMap)

			req = urllib2.Request(_showcaptchaURL, postBody)

			resp = _normalOpener.open(req,timeout =5)

			result = resp.read()
			print result.decode('UTF-8')
			resp.close()



			captcha = safe_raw_input('Captcha(check your captcha.jpg):')

			success = login(username,password,captcha)
			if success:
				print "Login succeeded."
			else:
				print "Login failed."
		except Exception as e:
			print "Login failed. ",e


	c = True
	while c:
		try:
			c = round()
		except Exception as e:
			print 'Unknown Exception(Network? Permission?):',e

