import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re
import HTMLParser
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
from elementtree.ElementTree import parse

addon = Addon('plugin.video.redlettermedia', sys.argv)
xaddon = xbmcaddon.Addon(id='plugin.video.redlettermedia')
net = Net()

##### Queries ##########
play = addon.queries.get('play', None)
mode = addon.queries['mode']
url = addon.queries.get('url', None)

print 'Mode: ' + str(mode)
print 'Play: ' + str(play)
print 'URL: ' + str(url)


################### Global Constants #################################

MainUrl = 'http://www.redlettermedia.com/'
APIPath = 'http://blip.tv/players/episode/%s?skin=api'
AddonPath = xaddon.getAddonInfo('path')
IconPath = AddonPath + "/icons/"

######################################################################


# Temporary function to grab html even when encountering an error
# Some pages on the site return 404 even though the html is there
def get_http_error(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', net._user_agent)
    try:
        response = urllib2.urlopen(req)
        html = response.read()
    except urllib2.HTTPError, error:
        html = error.read()
    
    return html


def get_url(url):
    h = HTMLParser.HTMLParser() 
    html = net.http_GET(MainUrl).content
    html = h.unescape(html)
    return html.encode('utf-8')
     
                      
if play:

    #Check if url is youtube link first
    isyoutube = re.search('youtube.com', url)
    
    if isyoutube:
        stream_url = urlresolver.HostedMediaFile(url).resolve()
    
    #Is a redlettermedia url, so need to find and parse video link
    else:
    
        html = get_http_error(url)
          
        #First check if there are multiple video parts on the page
        parts = re.compile('>([PARTart]* [1-9]):<br />').findall(html)
        
        #Page has multiple video parts
        if len(parts) > 1:
            partlist = []
            for part in parts:
                partlist.append(part)    
            
            dialog = xbmcgui.Dialog()
            index = dialog.select('Choose the video', partlist)
            
            #Take only selected part portion of the html
            if index >= 0:          
                html = re.search('>%s:<br />(.+?)</p>' % partlist[index],html,re.DOTALL).group(1)
            else:
                html = False
    
        if html:                 
        
            #Check for youtube video first
            youtube = re.search('src="(http://www.youtube.com/[v|embed]*/[0-9A-Za-z_\-]+).+?"',html)      
            springboard = re.search('src="(http://cms.springboardplatform.com/.+?)"', html)
            
            if youtube:
                stream_url = urlresolver.HostedMediaFile(url=youtube.group(1)).resolve()
            
            elif springboard:
                html = net.http_GET(springboard.group(1)).content
                stream_url = re.search('<meta property="og:video" content="(.+?)" />', html).group(1)
                
            else:
            
                video = re.search('<embed.+?src="http://[a.]{0,2}blip.tv/[^#/]*[#/]{1}([^"]*)"',html, re.DOTALL).group(1)
                api_url = APIPath % video
               
                links = []
                roles = []
                    
                tree = parse(urllib.urlopen(api_url))
                for media in tree.getiterator('media'):
                    for link in media.getiterator('link'):
                        links.append(link.get('href'))
                        roles.append(media.findtext('role'))
                    
                dialog = xbmcgui.Dialog()
                index = dialog.select('Choose a video source', roles)          
                if index >= 0:
                    stream_url = links[index]
                else:
                    stream_url = False
        else:
            stream_url = False
    
    #Play the stream
    if stream_url:
        addon.resolve_url(stream_url)  


def mainpage_links():
    addon.add_directory({'mode': 'none'}, {'title': '[COLOR blue]Recent Updates[/COLOR]'}, is_folder=False, img='')
    html = get_url(url)
    entries = re.compile('<h2 class="post-title"><a href="(.+?)"[ rel="bookmark"]* title=".+?">(.+?)</a></h2>').findall(html)
    for link, title in entries:
        addon.add_video_item({'url': link},{'title':title})


if mode == 'main': 
    addon.add_directory({'mode': 'plinkett', 'url': MainUrl}, {'title': 'Plinkett Reviews'}, img=IconPath + 'plinkett.jpg')
    addon.add_directory({'mode': 'halfbag', 'url': MainUrl + 'half-in-the-bag/'}, {'title': 'Half in the Bag'}, img=IconPath + 'halfbag.jpg')
    addon.add_directory({'mode': 'featurefilms', 'url': MainUrl + 'films/'}, {'title': 'Feature Films'})
    addon.add_directory({'mode': 'shortfilms', 'url': MainUrl + 'shorts/'}, {'title': 'Short Films'})
    mainpage_links()

elif mode == 'plinkett':
    url = addon.queries['url']
    html = get_http_error(url)
    
    r = re.search('MR. PLINKETT</a>.+?<ul class="sub-menu">(.+?)</ul>', html, re.DOTALL)
    if r:
        match = re.compile('<li.+?><a href="(.+?)">(.+?)</a></li>').findall(r.group(1))
    else:
        match = None

    # Add each link found as a directory item
    for link, name in match:
       addon.add_directory({'mode': 'plinkettreviews', 'url': link}, {'title': name})

elif mode == 'plinkettreviews':
    url = addon.queries['url']
    html = get_http_error(url)

    section = re.search('<h1 class="page-title">.+?</h1>(.+?)<script type="text/javascript">', html, re.DOTALL).group(1)
    match = re.compile('<a href="(.+?)"><img src="(.+?)">').findall(section)
    for link, thumb in match:
        name = re.search("[http://]*[a-z./-]*/(.+?)/",'/' + link).group(1).replace('-',' ').replace('/',' ').title()
        
        if re.search('http',link):
            newlink = link
        else:
            newlink = url + link
        addon.add_video_item({'url': newlink},{'title':name},img=thumb)

elif mode == 'halfbag':
    url = addon.queries['url']
    html = get_http_error(url)
    
    halfbag = re.search('<li id="menu-item-527"(.+?)</ul>', html, re.DOTALL)
    if halfbag:
        match = re.compile('<a href="(.+?)">(.+?)</a></li>').findall(halfbag.group(0))
        for link, name in match:
            addon.add_directory({'mode': 'halfbag-episodes', 'url': link}, {'title': name})


elif mode == 'halfbag-episodes':
    url = addon.queries['url']
    html = get_http_error(url)

    section = re.search('<h1 class="page-title">.+?</h1>(.+?)<script type="text/javascript">', html, re.DOTALL).group(1)
    match = re.compile('<a href="(http://[www.]*(redlettermedia|youtube)\.com/[a-zA-Z0-9-/_?=]*[/]*)"[ target=0]*><img src="(.+?jpg)"></a>', re.DOTALL).findall(section)
    for link, blank, thumb in match:
        episodenum = re.search('([0-9]+)[.]jpg', thumb)
        if episodenum:
            episode_name = 'Episode ' + str(episodenum.group(1))
        else:
            filename = re.search('[^/]+$', thumb).group(0)
            episode_name = re.search('(.+?)[.]jpg', filename).group(1).replace('_',' ').title()
        addon.add_video_item({'url': link},{'title': episode_name},img=thumb)
    
    shortmatch = re.compile('<a href="(http://www.youtube.com/.+?)" target=0><img src="(.+?)"></a>').findall(html)
    for link, thumb in shortmatch:
        filename = re.search('[^/]+$', thumb).group(0)
        episode_name = re.search('(.+?)[.]jpg', filename).group(1).replace('_',' ').title()
        addon.add_video_item({'url': link},{'title': episode_name},img=thumb)


elif mode == 'featurefilms':
    url = addon.queries['url']
    html = get_http_error(url)
    
    r = re.search('FEATURE FILMS</a>.+?<ul class="sub-menu">(.+?)</ul>', html, re.DOTALL)
    if r:
        match = re.compile('<li.+?<a href="(.+?)">(.+?)</a></li>').findall(r.group(1))
    else:
        match = None
           
    thumb = re.compile('<td><a href=".+?"><img src="(.+?)"></a></td>').findall(html)

    #Add each link found as a directory item
    i = 0
    for link, name in match:
        addon.add_directory({'mode': 'film', 'url': link}, {'title': name}, img=thumb[i])
        i += 1

elif mode == 'film':
    url = addon.queries['url']
    html = get_http_error(url)

    match = re.compile('<td><a href="(.+?)".*><img src="(.+?)".*>').findall(html)
    for link, thumb in match:
        link = url + link.replace(url,'')
        name = link.replace(url,'').replace('-',' ').replace('/',' ').title()
        addon.add_video_item({'url': link},{'title': name}, img=thumb)
   
elif mode == 'shortfilms':
    url = addon.queries['url']
    html = get_http_error(url)

    r = re.search('SHORTS AND WEB VIDEOS</a>.+?<ul class="sub-menu">(.+?)</ul>', html, re.DOTALL)
    if r:
        match = re.compile('<a href="(.+?)">(.+?)</a></li>').findall(r.group(1))
            
    # Add each link found as a directory item
    for link, name in match:
       addon.add_directory({'mode': 'shortseason', 'url': link}, {'title': name})

elif mode == 'shortseason':
    url = addon.queries['url']
    html = get_http_error(url)
    
    #Check if there are any videos embedded on the page
    if re.search('[<embed src=|youtube.com/embed]',html):
        addon.add_video_item({'url': url},{'title': 'Video'})
    else:
        match = re.compile('<td><a href="(.+?)".*><img src="(.+?)".*></a></td>').findall(html)
        
        # Add each link found as a video item
        for link, thumb in match:
            name = link.replace(url,'').replace('-',' ').replace('/',' ').title()
            link = url + link.replace(url,'')
            addon.add_video_item({'url': link},{'title': name},img=thumb)


if not play:
    addon.end_of_directory()