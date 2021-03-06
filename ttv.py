PLAYLIST_LOAD_URL = "http://91.92.66.82/trash/ttv-list/as.all.tag.player.m3u"
TEMPLATE_SAVE_PATH = "/opt/etc/ttv/template.txt"
FAVORITES_LOAD_PATH = "/opt/etc/ttv/favorites.txt"
PLAYLIST_SAVE_PATH = "/opt/etc/ttv/playlist.m3u"
LOGOS_URL = ""
#LOGOS_URL = "https://raw.githubusercontent.com/Kyrie1965/ttv/master/logos/{}"
#LOGOS_URL = "{}"
STREAM_URL = "http://127.0.0.1:6878/ace/getstream?id={}&.mp4"
#STREAM_URL = "acestream://{}"
EPG_LINKS = "https://teleguide.info/download/new3/xmltv.xml.gz"
#EPG_LINKS = "https://teleguide.info/download/new3/xmltv.xml.gz,http://programtv.ru/xmltv.xml.gz,http://api.torrent-tv.ru/ttv.xmltv.xml.gz"

import re
import urllib.request
import os
from operator import itemgetter as i
from functools import cmp_to_key
from urllib.parse import urlencode
import gzip

def cmp(a, b):
	return (a > b) - (a < b) 
	
def multikeysort(items, columns):
	comparers = [
		((i(col[1:].strip()), -1) if col.startswith('-') else (i(col.strip()), 1))
		for col in columns
	]
	def comparer(left, right):
		comparer_iter = (
			cmp(fn(left), fn(right)) * mult
			for fn, mult in comparers
		)
		return next((result for result in comparer_iter if result), 0)
	return sorted(items, key=cmp_to_key(comparer))
	
def loadChannels(content):
	lines = content.splitlines()
	
	returnChannels = {}
	
	pattern = re.compile("group-title=\"(.*?)\"")
	pattern2 = re.compile("tvg-logo=\"(.*?)\"")
	channelName = ""
	channelGroup = ""
	channelLogoLink = ""
	channelStreamID = ""
	waitURI = False
	
	for line in lines:
		if line.startswith("acestream"):
			if waitURI:
				channelStreamID = line[12:]
				HD = False
				if ("HD" in channelName) or ("UHD" in channelName) or ("4K" in channelName):
					HD = True
				tmpDict = {"name": channelName, "group": channelGroup, "stream": channelStreamID, "hd": HD, "logolink": channelLogoLink}
				returnChannels[channelName.upper()] = tmpDict
				waitURI = False
		elif line.startswith("#EXTINF"):
			index = line.rfind("\",")
			if (index == -1):
				continue
			channelName = line[index+2:]
			match = pattern.search(line)
			if match:
				channelGroup = match.group(1)
			else:
				channelGroup = "Общие"
			match = pattern2.search(line)
			if match:
				channelLogoLink = match.group(1)
			else:
				channelLogoLink = ""
			waitURI = True
	return returnChannels
	
def saveTemplate(content, channels, path):
	lines = content.splitlines()
	pattern = re.compile("group-title=\"(.*?)\"")
	
	waitURI = False
	
	channelName = ""
	channelReplace = ""
	channelNewName = ""
	channelEPG = ""
	channelGroup = ""
	channelStreamID = ""
	groupDict = {}
	currentGroup = 1
	template=""
	for line in lines:
		if line.startswith("acestream"):
			if waitURI:
				channelStreamID = line[12:]
				template += channelName
				template += "/"
				template += channelReplace
				template += "/"
				template += channelNewName
				template += "/"
				template += channelEPG
				template += "/"
				template += channelName + ".png"
				template += "/"
				template += channelGroup
				template += "\n"
				waitURI = False
		elif line.startswith("#EXTINF"):
			x = line.split("\",")
			if (len(x) != 2):
				continue
			channelName = x[1]
			channelNewName = x[1]
			channelEPG = x[1]
			if (channels.get(channelName.upper() + " HD") != None):
				channelReplace = channelName + " HD"
			else:
				channelReplace = "-"
			match = pattern.search(x[0])
			if match:
				channelGroup = match.group(1)
				if (groupDict.get(channelGroup)):
					channelGroup = groupDict.get(channelGroup)
				else:
					newGroupName = "{:02d}_{}".format(currentGroup, channelGroup)
					currentGroup += 1
					groupDict[channelGroup] = newGroupName
					channelGroup = newGroupName
			else:
				channelGroup = "00_Unsigned"
			waitURI = True
	file = open(path,'w', encoding='utf-8')
	file.write(template)
	file.close()
	return

def loadFavorites(content):
	returnChannels = {}
	lines = content.splitlines()
	for line in lines:
		parts = line.split('/')
		if len(parts) == 6:
			tmpDict = {"name": parts[0], "replace": parts[1], "newName": parts[2], "EPG": parts[3], "logo": parts[4], "group": parts[5]}
			returnChannels[parts[0].upper()] = tmpDict
		elif len(parts) == 5: #совместимость с предыдущим вариантом
			tmpDict = {"name": parts[0], "replace": parts[1], "newName": parts[2], "EPG": parts[3], "group": parts[4], "logo": parts[0] + ".png"}
			returnChannels[parts[0].upper()] = tmpDict
	return returnChannels

def savePlaylist(channels, favorites, path):
	returnChannels = []
	currentChannels = set()
	for key, chDict in favorites.items():
		if chDict["replace"] != "-":
			if favorites.get(chDict["replace"].upper()) != None and channels.get(chDict["replace"].upper()) != None:
				currentChannels.add(chDict["replace"])
			elif channels.get(chDict["name"].upper()) != None:
				currentChannels.add(chDict["name"])
		elif channels.get(chDict["name"].upper()) != None:
			currentChannels.add(chDict["name"])
	for ch in currentChannels:
		chFromFavorites = favorites.get(ch.upper())
		chFromChannels = channels.get(ch.upper())
		tmpDict = {"name": chFromFavorites.get("newName"), "oldName": chFromFavorites.get("name"), "EPG": chFromFavorites.get("EPG"), "group": chFromFavorites.get("group"), "logof": chFromFavorites.get("logo"), "logoc": chFromChannels.get("logolink"), "stream": chFromChannels.get("stream"), "hd": chFromChannels.get("hd")}
		returnChannels.append(tmpDict)
	result = multikeysort(returnChannels, ['group', '-hd', 'name'])
	template=""
	template += "#EXTM3U url-tvg="
	template += "\""
	template += EPG_LINKS
	template += "\""
	template += "\n"
	for n in result:
		group = n.get("group")
		if group.find("_", 2, 3) != -1:
			group = group[3:]
		if len(LOGOS_URL) > 0:
			template += "#EXTINF:-1 tvg-name=\"{}\" tvg-logo=\"{}\" group-title=\"{}\",{}".format(n.get("EPG"), LOGOS_URL.format(urllib.parse.quote(n.get("logof"))), group, n.get("name"))
		else:
			template += "#EXTINF:-1 tvg-name=\"{}\" tvg-logo=\"{}\" group-title=\"{}\",{}".format(n.get("EPG"), n.get("logoc"), group, n.get("name"))
		template += "\n"
		template += STREAM_URL.format(n.get("stream"))
		template += "\n"
	file = open(path,'w', encoding='utf-8')
	file.write(template)
	file.close()
	return result
	
#response = urllib.request.urlopen(PLAYLIST_LOAD_URL)
#content = response.read().decode("utf-8")
#channels = loadChannels(content)
content = ""
request = urllib.request.Request(PLAYLIST_LOAD_URL)
request.add_header('Accept-encoding', 'gzip')
response = urllib.request.urlopen(request)
if response.info().get('Content-Encoding') == 'gzip':
	gzipFile = gzip.GzipFile(fileobj=response)
	content = gzipFile.read().decode("utf-8")
else:
	content = response.read().decode("utf-8")
channels = loadChannels(content)

if channels == None or (len(channels.keys()) == 0):
	exit()

saveTemplate(content, channels, TEMPLATE_SAVE_PATH)

exists = os.path.isfile(FAVORITES_LOAD_PATH)

if exists:
	file = open(FAVORITES_LOAD_PATH,'r', encoding='utf-8')
	content = file.read()
	favorites = loadFavorites(content)
	savePlaylist(channels, favorites, PLAYLIST_SAVE_PATH)
