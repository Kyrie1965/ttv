PLAYLIST_LOAD_URL = "http://91.92.66.82/trash/ttv-list/ttv.all.tag.player.m3u"
TEMPLATE_SAVE_PATH = "/opt/etc/ttv/template.txt"
FAVORITES_LOAD_PATH = "/opt/etc/ttv/favorites.txt"
PLAYLIST_SAVE_PATH = "/opt/etc/ttv/playlist.m3u"
LOGOS_URL = "https://raw.githubusercontent.com/Kyrie1965/ttv/master/logos/{}.png"
#LOGOS_URL = "{}.png"
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
	channelName = ""
	channelGroup = ""
	channelStreamID = ""
	waitURI = False
	
	for line in lines:
		if line.startswith("acestream"):
			if waitURI:
				channelStreamID = line[12:]
				HD = False
				if "HD" in channelName:
					HD = True
				tmpDict = {"name": channelName, "group": channelGroup, "stream": channelStreamID, "hd": HD}
				returnChannels[channelName] = tmpDict
				waitURI = False
		elif line.startswith("#EXTINF"):
			x = line.split("\",")
			if (len(x) != 2):
				continue
			channelName = x[1]
			match = pattern.search(x[0])
			if match:
				channelGroup = match.group(1)
			else:
				channelGroup = "Общие"
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
			if (channels.get(channelName + " HD") != None):
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
		if len(parts) == 5:
			tmpDict = {"name": parts[0], "replace": parts[1], "newName": parts[2], "EPG": parts[3], "group": parts[4]}
			returnChannels[parts[0]] = tmpDict
	return returnChannels

def savePlaylist(channels, favorites, path):
	returnChannels = []
	currentChannels = set()
	for key, chDict in favorites.items():
		if chDict["replace"] != "-":
			if favorites.get(chDict["replace"]) != None and channels.get(chDict["replace"]) != None:
				currentChannels.add(chDict["replace"])
			elif channels.get(chDict["name"]) != None:
				currentChannels.add(chDict["name"])
		elif channels.get(chDict["name"]) != None:
			currentChannels.add(chDict["name"])
	for ch in currentChannels:
		chFromFavorites = favorites.get(ch)
		chFromChannels = channels.get(ch)
		tmpDict = {"name": chFromFavorites.get("newName"), "oldName": chFromFavorites.get("name"), "EPG": chFromFavorites.get("EPG"), "group": chFromFavorites.get("group"), "stream": chFromChannels.get("stream"), "hd": chFromChannels.get("hd")}
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
		template += "#EXTINF:-1 tvg-name=\"{}\" tvg-logo=\"{}\" group-title=\"{}\" ,{}".format(n.get("EPG"), LOGOS_URL.format(urllib.parse.quote(n.get("oldName"))), group, n.get("name"))
		template += "\n"
		template += STREAM_URL.format(n.get("stream"))
		template += "\n"
	file = open(path,'w', encoding='utf-8')
	file.write(template)
	file.close()
	return result
	
response = urllib.request.urlopen(PLAYLIST_LOAD_URL)
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
#else:
#	file = open(PLAYLIST_SAVE_PATH,'w', encoding='utf-8')
#	file.write(content)
#	file.close()

