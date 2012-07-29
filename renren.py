"""
Created on Jul 20, 2012

@author: latifrons88@gmail.com
"""
import re
import lxml.html as H

class Album():
	"""
	Album info.
	"""

	def __init__(self, albumName, albumID, albumURL, coverURL, picCount,ownerID,ownerName):
		self.albumName = albumName
		self.albumID = albumID
		self.albumURL = albumURL
		self.coverURL = coverURL
		self.picCount = picCount
		self.ownerID = ownerID
		self.ownerName = ownerName


class Photo():
	def __init__(self, photoSeq, photoID, photoURL,photoOriginalURL, album):
		self.photoSeq = photoSeq
		self.photoID = photoID
		self.photoURL = photoURL
		self.album = album
		self.photoOriginalURL=photoOriginalURL



reAlbums = ['/(?P<id>\\d+)/profile',
            '/profile\\.do\\?id=(?P<id>\\d+)',
            '/photo/(?P<id>\\d+)/album/relatives',
            '^(?P<id>\\d+)$']
reAlbum = ['/photo/(?P<uid>\\d+)/album-(?P<aid>\\d+)']

rePhotoInfo = 'album.+?(?P<albumid>\\d+).+?photo.+?(?P<photoid>\\d+).+?position.+?(?P<position>\\d+)'
reAlbumSize = '\\((?P<picc>\\d+).+\\)'
reLarge = "large:'(?P<url>.+?)',"
reWash = '[\\\\/:\\*\?"<>|\\n\\r\\t]'

def clean(path):
	return re.sub(reWash,'',path)

def getUserInfoFromURL(userURL):
	"""
	Given a userURL, return the userid
	"""
	for s in reAlbums:
		m = re.search(s, userURL)
		if m:
			uid = m.groupdict()['id']
			return uid

def getAlbumListURL(userURL):
	"""
	Given a userURL, return the URL of his/her album list
	"""
	uid = getUserInfoFromURL(userURL)

	if uid is None:
		return uid
	else:
		return ''.join(['http://photo.renren.com/photo/', uid, '/album/relatives'])

def getAlbumInfoFromURL(albumURL):
	"""
	Given an albums URL, return the tuple of userid and albumid
	"""
	for s in reAlbum:
		m = re.search(s,albumURL)
		if m:
			dict = m.groupdict()
			return  dict['uid'], dict['aid']

	return None

def getPhotoListURL(albumURL):
	"""
	Given an album URL, return the re-formatted photo list URL, or None if the address is not recognizable
	"""
	abInfo = getAlbumInfoFromURL(albumURL)
	if abInfo is None:
		return None
	else:
		return ''.join(['http://photo.renren.com/photo/',abInfo[0],'/album-',abInfo[1]])


def getAlbums(albumListHTML):
	"""
	Given an album list HTML, return the list of Album objects
	"""
	doc = H.document_fromstring(albumListHTML)
	userURL = doc.xpath('//ul[contains(@class,"nav-tabs")]/li/a')[0].attrib['href']
	userid = getUserInfoFromURL(userURL)
	userName =clean(doc.xpath('//ul[contains(@class,"nav-tabs")]/li/a/strong')[0].text)

	albumNodes = doc.xpath('//div[contains(@class,"album-list")]//li')
	albums = []
	for albumNode in albumNodes:
		coverNode = albumNode.find('.//img[@data-src]')
		if coverNode is None:
			continue
		coverURL = coverNode.attrib['data-src']

		abname = clean(''.join(albumNode.xpath('.//span[contains(@class,"album-name")]//text()')))
		aburl = albumNode.find('.//a').attrib['href']
		abInfo = getAlbumInfoFromURL(aburl)
		aid = abInfo[1]
		picc = int(clean(albumNode.xpath('.//div[contains(@class,"photo-num")]')[0].text))

		albums.append(Album(albumName=abname, albumID=aid, albumURL=aburl, coverURL=coverURL, picCount=picc,ownerID = userid,ownerName=userName))
		print albumNode.find('.//a').attrib['href']

	return albums

def getAlbumInfo(albumURL,albumHTML):
	doc = H.document_fromstring(albumHTML)

	abname = clean(doc.xpath('.//div[contains(@class,"ablum-infor")]//h1')[0].text)
	abInfo = getAlbumInfoFromURL(albumURL)
	picct = clean(doc.xpath('//span[contains(@class,"num")]')[0].text)
	picc = int(re.search(reAlbumSize,picct).groupdict()['picc'])
	userURL = doc.xpath('//ul[contains(@class,"nav-tabs")]/li/a')[0].attrib['href']
	userid = getUserInfoFromURL(userURL)
	userName =clean(doc.xpath('//ul[contains(@class,"nav-tabs")]/li/a/strong')[0].text)

	return Album(albumName=abname, albumID=abInfo[1], albumURL=albumURL, coverURL=None, picCount=picc,ownerID = userid,ownerName=userName)

def getPhotos(album,photoListHTML):
	doc = H.document_fromstring(photoListHTML)
	photoNodes = doc.xpath('//div[contains(@class,"photo-list")]//li')
	photos = []
	for photoNode in photoNodes:
		dataInfoStr = photoNode.attrib['data-info']
		dataInfo = re.search(rePhotoInfo,dataInfoStr).groupdict()

		seq = dataInfo['position']
		pid = dataInfo['photoid']
		dataPhoto = photoNode.find('.//img').attrib['data-photo']
		purl = re.search(reLarge,dataPhoto).groupdict()['url']
		pourl = purl.replace('large','original')

		photos.append(Photo(photoSeq=seq,photoID=pid,photoURL=purl,photoOriginalURL=pourl,album=album))
	return photos
