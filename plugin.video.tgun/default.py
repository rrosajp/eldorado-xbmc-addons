import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib2
import re, string
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net

try:
    import json
except:
    import simplejson as json

addon = Addon('plugin.video.tgun', sys.argv)
xaddon = xbmcaddon.Addon(id='plugin.video.tgun')
net = Net()

##### Queries ##########
play = addon.queries.get('play', None)
mode = addon.queries['mode']
section = addon.queries.get('section', None)
url = addon.queries.get('url', None)

print 'Mode: ' + str(mode)
print 'Play: ' + str(play)
print 'URL: ' + str(url)
print 'Section: ' + str(section)

################### Global Constants #################################

main_url = 'http://www.tgun.tv/'
shows_url = main_url + 'shows/'
showlist_url_1 = shows_url + 'chmm.php'
showlist_url_2 = shows_url + 'chmm2.php'
classic_url = main_url + 'classic/chm%s.php'
addon_path = xaddon.getAddonInfo('path')
icon_path = addon_path + "/icons/"

######################################################################

def getSwfUrl(channel_name):
        """Helper method to grab the swf url, resolving HTTP 301/302 along the way"""
        base_url = 'http://www.justin.tv/widgets/live_embed_player.swf?channel=%s' % channel_name
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://www.justin.tv/'+channel_name}
        req = urllib2.Request(base_url, None, headers)
        response = urllib2.urlopen(req)
        return response.geturl()


def justintv(embedcode):

    channel = re.search('data="(.+?)"', embedcode, re.DOTALL).group(1)  
    channel_name = re.search('http://www.justin.tv/widgets/.+?\?channel=(.+)', channel).group(1)
    
    api_url = 'http://usher.justin.tv/find/%s.json?type=live' % channel_name
    html = net.http_GET(api_url).content
    
    data = json.loads(html)
    jtv_token = ' jtv='+data[0]['token'].replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
    rtmp = data[0]['connect']+'/'+data[0]['play']
    swf = ' swfUrl=%s swfVfy=1' % getSwfUrl(channel_name)
    page_url = ' Pageurl=http://www.justin.tv/' + channel_name
    final_url = rtmp + jtv_token + swf + page_url
    return final_url


def get_blogspot(embedcode):
    print 'blogspot'
    return ''


def sawlive(embedcode):
    url = re.search("<script type='text/javascript'> swidth='600', sheight='530';</script><script type='text/javascript' src='(.+?)'></script>", embedcode, re.DOTALL).group(1)
    data = {'referer': main_url}
    html = net.http_POST(url, data).content
    html = net.http_GET(url, data).content
    aa1 = re.search('var aa1 = "(.+?)";', html).group(1)
    zz1 = re.search('var zz1 = "(.+?)";', html).group(1)
    embed_url = re.search('src="(.+?)\'', html).group(1) + aa1 + zz1
    html = net.http_GET(embed_url).content
    
    print html
    swfPlayer = re.search('flashplayer\': "(.+?)"', html).group(1)
    playPath = re.search('\'file\': \'(.+?)\'', html).group(1)
    streamer = re.search('\'streamer\': \'(.+?)\'', html).group(1)
    appUrl = re.search('rtmp[e]*://.+?/(.+?)\'', html).group(1)
    rtmpUrl = ''.join([streamer,
       ' playpath=', playPath,
       ' app=', appUrl,
       ' pageURL=', url,
       ' swfUrl=', swfPlayer,
       ' live=true'])
    print rtmpUrl
    return rtmpUrl
    

if play:

    html = net.http_GET(url).content
    embedcode = re.search("(<object type=\"application/x-shockwave-flash\"|<!-- start embed -->|<!-- BEGIN PLAYER CODE.+?-->|<!-- START PLAYER CODE &ac=270 kayakcon11-->)(.+?)<!-- END PLAYER CODE -->", html, re.DOTALL).group(2)
    
    if re.search('justin.tv', embedcode):
        stream_url = justintv(embedcode)
    elif re.search('sawlive', embedcode):
        stream_url = sawlive(embedcode)

    #Play the stream
    if stream_url:
        addon.resolve_url(stream_url)


if mode == 'main2':
    first_channel = 1
    addon.add_directory({'mode': 'channels', 'url': showlist_url_1}, {'title': 'TV Shows'}, img=icon_path + 'newtv.jpg')
    addon.add_directory({'mode': 'channels', 'url': classic_url % first_channel}, {'title': 'Classic TV'}, img=icon_path + 'retrotv.jpg')


elif mode == 'main':
    if not url:
        url = showlist_url_1
    html = net.http_GET(url).content
    
    match = re.compile('<a[ A-Za-z0-9\"=]* Title[ ]*="(.+?)"[ A-Za-z0-9\"=]* href="(.+?)"><img border="0" src="(.+?)" style=.+?</a>').findall(html)
    for name, link, thumb in match:
        if not re.search('http://', thumb):
            thumb = main_url + thumb
        addon.add_video_item({'mode': 'channel', 'url': shows_url + link}, {'title': name}, img=thumb)
    addon.add_directory({'mode': 'main', 'url': showlist_url_2}, {'title': 'Next Page'})


elif mode == 'resolver_settings':
    urlresolver.display_settings()


if not play:
    addon.end_of_directory()