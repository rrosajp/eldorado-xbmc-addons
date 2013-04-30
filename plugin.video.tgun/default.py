import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib2
import re, string
import os
from urlparse import urlparse
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
net = Net()

try:
    import json
except:
    import simplejson as json


##### XBMC  ##########
addon = Addon('plugin.video.tgun', sys.argv)
xaddon = xbmcaddon.Addon(id='plugin.video.tgun')
datapath = addon.get_profile()


##### Paths ##########
cookie_path = os.path.join(datapath, 'cookies')
cookie_jar = os.path.join(cookie_path, "cookiejar.lwp")
if os.path.exists(cookie_path) == False:
    os.makedirs(cookie_path)

##### Queries ##########
play = addon.queries.get('play', None)
mode = addon.queries['mode']
page_num = addon.queries.get('page_num', None)
url = addon.queries.get('url', None)

print 'Mode: ' + str(mode)
print 'Play: ' + str(play)
print 'URL: ' + str(url)
print 'Page: ' + str(page_num)

################### Global Constants #################################

main_url = 'http://www.tgun.tv/'
shows_url = main_url + 'shows/'
#showlist_url_1 = shows_url + 'chmm.php'
showlist_url_1 = "http://www.tgun.tv/menus/shows/chmenu.php"
showlist_url_2 = shows_url + 'chmm2.php'
classic_url = main_url + 'classic/'
classic_shows_url = classic_url + 'chm%s.php'
livetv_url = main_url + 'usa/'
livetv_pages = livetv_url + 'chmtv%s.php'
addon_path = xaddon.getAddonInfo('path')
icon_path = addon_path + "/icons/"
par = ''

######################################################################

def Notify(typeq, title, message, times, line2='', line3=''):
     #simplified way to call notifications. common notifications here.
     if title == '':
          title='TGUN Notification'
     if typeq == 'small':
          if times == '':
               times='5000'
          smallicon= icon_path + 'tgun.png'
          xbmc.executebuiltin("XBMC.Notification("+title+","+message+","+times+","+smallicon+")")
     elif typeq == 'big':
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ', line2, line3)
     else:
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')


def sys_exit():
    xbmc.executebuiltin("XBMC.Container.Update(addons://sources/video/plugin.video.tgun?mode=main,replace)")
    return


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
    
    channel_name = par
    
    api_url = 'http://usher.justin.tv/find/%s.json?type=live' % channel_name
    print 'Retrieving: %s' % api_url
    html = net.http_GET(api_url).content
    
    data = json.loads(html)
    try:
        jtv_token = ' jtv='+data[0]['token'].replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
    except:
        Notify('small','Offline', 'Channel is currently offline','')
        return None
    rtmp = data[0]['connect']+'/'+data[0]['play']
    swf = ' swfUrl=%s swfVfy=1' % getSwfUrl(channel_name)
    page_url = ' Pageurl=http://www.justin.tv/' + channel_name
    final_url = rtmp + jtv_token + swf + page_url
    return final_url


def get_blogspot(embedcode):
    print 'blogspot'
    return ''


def sawlive(embedcode, ref_url):
    url = re.search("<script type='text/javascript'> swidth='[0-9%]+', sheight='[0-9%]+';</script><script type='text/javascript' src='(.+?)'></script>", embedcode, re.DOTALL).group(1)
    ref_data = {'Referer': ref_url}

    try:
        ## Current SawLive resolving technique - always try to fix first
        html = net.http_GET(url,ref_data).content
        link = re.search('src="(http://sawlive.tv/embed/watch/[A-Za-z0-9_/]+)">', html).group(1)
        print link

    except Exception, e:
        ## Use if first section does not work - last resort which returns compiled javascript
        print 'SawLive resolving failed, attempting jsunpack.jeek.org, msg: %s' % e
        Notify('small','SawLive', 'Resolve Failed. Using jsunpack','')
        
        jsunpackurl = 'http://jsunpack.jeek.org'
        data = {'urlin': url}
        html = net.http_POST(jsunpackurl, data).content
        link = re.search('src="(http://sawlive.tv/embed/watch/[A-Za-z0-9]+[/][A-Za-z0-9_]+)"',html).group(1)
        print link

    html = net.http_GET(link, ref_data).content
    
    swfPlayer = re.search('SWFObject\(\'(.+?)\'', html).group(1)
    playPath = re.search('\'file\', \'(.+?)\'', html).group(1)
    streamer = re.search('\'streamer\', \'(.+?)\'', html).group(1)
    appUrl = re.search('rtmp[e]*://.+?/(.+?)\'', html).group(1)
    rtmpUrl = ''.join([streamer,
       ' playpath=', playPath,
       ' app=', appUrl,
       ' pageURL=', url,
       ' swfUrl=', swfPlayer,
       ' live=true'])
    print rtmpUrl
    return rtmpUrl


def mediaplayer(embedcode):
    url = re.search('<embed type="application/x-mplayer2" .+? src="(.+?)"></embed>', embedcode).group(1)
    print 'Retrieving: %s' % url
    html = net.http_GET(url).content
    
    matches = re.findall('<Ref href = "(.+?)"/>', html)
    url = matches[1]
    
    print 'Retrieving: %s' % url
    html = net.http_GET(url).content
    print html
    
    return re.search('Ref1=(.+?.asf)', html).group(1)


def ilive(embedcode):
    
    #channel = re.search('<script type="text/javascript" src="http://www.ilive.to/embed/(.+?)&width=.+?"></script>', embedcode)
    channel = par
    
    if channel:
        #url = 'http://www.ilive.to/embedplayer.php?channel=%s' % channel.group(1)
        url = 'http://www.ilive.to/embedplayer.php?channel=%s' % channel
        print 'Retrieving: %s' % url
        html = net.http_GET(url).content
        filename = re.search('file: "([^&]+).flv"', html).group(1)
        rtmp = re.search('streamer: "(.+?)",', html).group(1)
    else:
        filename = re.search('streamer=rtmp://live.ilive.to/edge&file=(.+?)&autostart=true&controlbar=bottom"', embedcode).group(1)
        url = 'http://www.ilive.to/embedplayer.php'

    swf = 'http://player.ilive.to/ilive-plugin.swf'
    return rtmp + ' playPath=' + filename + ' swfUrl=' + swf + ' swfVfy=true live=true pageUrl=' + url


def embedrtmp(embedcode):
    stream = re.search('<embed src="(.+?)".*?;file=(.+?)&amp;streamer=(.+?)&amp;.*?>', embedcode)
    print stream.group(3)
    app = re.search('rtmp[e]*://.+?/(.+?/)', stream.group(3)).group(1)
    return stream.group(3) + ' app=' + app + ' playpath=' + stream.group(2) + ' swfUrl=' + stream.group(1) + ' live=true'


def castto(embedcode, url):
    data = {'Referer': url}
    
    parms = re.search('<script type="text/javascript"> fid="(.+?)"; v_width=.+; .+ src=".+castto.+"></script>', embedcode)
    
    link = 'http://static.castto.me/embed.php?channel=%s' % parms.group(1)
    html = net.http_GET(link, data).content
    swfPlayer = re.search('SWFObject\(\'(.+?)\'', html).group(1)
    playPath = re.search('\'file\',\'(.+?)\'', html).group(1)
    streamer = re.search('\'streamer\',\'(.+?)\'', html).group(1)
    rtmpUrl = ''.join([streamer,
       ' playpath=', playPath,
       ' pageURL=', 'http://static.castto.me',
       ' swfUrl=', swfPlayer,
       ' live=true',
       ' token=#ed%h0#w@1'])
    print rtmpUrl
    return rtmpUrl


def owncast(embedcode, url):
    data = {'Referer': url}
    
    parms = re.search('<script type="text/javascript"> fid="(.+?)"; v_width=(.+?); v_height=(.+?);</script><script type="text/javascript" src="(.+?)"></script>', embedcode)
    
    link = 'http://www.owncast.me/embed.php?channel=%s&vw=%s&vh=%s&domain=www.tgun.tv' % (parms.group(1), parms.group(2), parms.group(3))
    #html = net.http_GET(link, data).content
    referrer = url
    USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
    req = urllib2.Request(link)
    req.add_header('User-Agent', USER_AGENT)
    req.add_header('Referer', referrer)
    response = urllib2.urlopen(req)
    html = response.read()
    swfPlayer = re.search('SWFObject\(\'(.+?)\'', html).group(1)
    rtmpjson = re.search('getJSON\("(.+?)",', html).group(1)
    
    data = {'referer': link}
    rtmplink = net.http_GET(rtmpjson, data).content
    streamer = re.search('"rtmp":"(.+?)"', rtmplink).group(1)
    playPath = re.search('"streamname":"(.+?)"', rtmplink).group(1)
    
    
    if not re.search('http://www.owncast.me', swfPlayer):
        swfPlayer = 'http://www.owncast.me' + swfPlayer
    #playPath = re.search('\'file\',\'(.+?)\'', html).group(1)
    #streamer = re.search('\'streamer\',\'(.+?)\'', html).group(1)
    rtmpUrl = ''.join([streamer,
       ' playpath=', playPath,
       ' pageURL=', link,
       ' swfUrl=', swfPlayer,
       ' live=true'])
    print rtmpUrl
    return rtmpUrl


def playerindex(embedcode):
    link = re.search('iframe src="(.+?)"', embedcode).group(1)
    link = urllib2.unquote(urllib2.unquote(link))
    html = net.http_GET('http://www.tgun.tv/shows/' + link).content
    return html


def get_embed(html):
    #embedtext = "(<object type=\"application/x-shockwave-flash\"|<!--[0-9]* start embed [0-9]*-->|<!-- BEGIN PLAYER CODE.+?-->|<!-- Begin PLAYER CODE.+?-->|<!--[ ]*START PLAYER CODE [&ac=270 kayakcon11]*-->|)(.+?)<!-- END PLAYER CODE [A-Za-z0-9]*-->"
    embedtext = "-->(.+?)<!-- start Ad Code 2 -->"
    #embedcode = re.search(embedtext, html, re.DOTALL).group(2)
    embedcode = re.search(embedtext, html, re.DOTALL).group(1)
    
    #Remove any commented out sources to we don't try to use them
    embedcode = re.sub('(?s)<!--.*?-->', '', embedcode).strip()
    return embedcode


def determine_stream(embedcode, url):
    if re.search('justin.tv', embedcode):
        stream_url = justintv(embedcode)
    elif re.search('castto', embedcode):
        stream_url = castto(embedcode, url)
    elif re.search('owncast', embedcode):
        stream_url = owncast(embedcode, url)
    elif re.search('sawlive', embedcode):
        stream_url = sawlive(embedcode, url)
    elif re.search('ilive.to', embedcode):
        stream_url = ilive(embedcode)	
    elif re.search('MediaPlayer', embedcode):
        stream_url = mediaplayer(embedcode)
    elif re.search('rtmp', embedcode):
        stream_url = embedrtmp(embedcode)
    else:
        stream_url = None
    return stream_url


if play:

    #Check for channel name at the end of url
    global par
    par = urlparse(url).query
    
    html = net.http_GET(url).content
    embedcode = get_embed(html)

    if re.search('playerindex.php', embedcode):
        channel = urllib2.unquote(re.search('src="playerindex.php\?(.+?)"', embedcode).group(1))
        html = playerindex(embedcode)
        embedcode = ''

    if re.search('http://tgun.tv/embed/', embedcode):
        link = re.search('src="(.+?)"', embedcode).group(1)
        embedcode = net.http_GET(link).content      
        embedcode = re.sub('(?s)<!--.*?-->', '', embedcode).strip()

    stream_url = determine_stream(embedcode, url)

    if not stream_url:
        #If can't find anything lets do a quick check for escaped html for hidden links
        if not embedcode or re.search('document.write\(unescape', html):
            escaped = re.findall('document.write\(unescape\(\'(.+?)\'\)\);', html)
            if escaped:
                for escape in escaped:
                    embedcode = urllib2.unquote(urllib2.unquote(escape))
                    if re.search('streamer', embedcode):
                        stream = re.search('streamer=(.+?)&file=(.+?)&skin=.+?src="(.+?)"', embedcode)
                        
                        if stream:
                            if '+' in stream.group(2):
                                playpath = channel
                            else:
                                playpath = stream.group(2)
                            stream_url = stream.group(1) + ' playpath=' + playpath + ' swfUrl=http://www.tgun.tv' + stream.group(3) + ' live=true'                        
                        else:
                            swfPlayer = re.search('SWFObject\(\'(.+?)\'', embedcode).group(1)
                            streamer = re.search('\'streamer\',\'(.+?)\'', embedcode).group(1)
                            playPath = channel
                            stream_url = ''.join([streamer,
                                           ' playpath=', playPath,
                                           ' pageURL=', url,
                                           ' swfUrl=', 'http://www.tgun.tv' + swfPlayer,
                                           ' live=true'])
                        print stream_url
                    elif re.search('http://tgun.tv/embed', embedcode):
                        link = re.search('src="(.+?)"', html)
                        if link:
                            html = net.http_GET(link.group(1)).content
                            html = re.sub('(?s)<!--.*?-->', '', html).strip()
                            stream_url = determine_stream(html, link.group(1))
                        else:
                            stream_url = None
        else:
            Notify('small','Undefined Stream', 'Channel is using an unknown stream type','')
            stream_url = None

    #Play the stream
    if stream_url:
        addon.resolve_url(stream_url)


def tvchannels(turl = url, tpage = page_num):
    print 'Retrieving: %s' % turl
    html = net.http_GET(turl).content

    tpage = int(tpage) 
    if tpage > 1:
        addon.add_directory({'mode': 'mainexit'}, {'title': '[COLOR red]Back to Main Menu[/COLOR]'}, img=icon_path + 'back_arrow.png')

    if tpage < 2:
        tpage = tpage +  1
        addon.add_directory({'mode': 'tvchannels', 'url': showlist_url_2, 'page_num': tpage}, {'title': '[COLOR blue]Next Page[/COLOR]'}, img=icon_path + 'next_arrow.png')

    #Remove any commented out sources to we don't try to use them
    html = re.sub('(?s)<!--.*?-->', '', html).strip()
    
    match = re.compile('<a Title="(.+?)" href="(.+?)" target="vid_z"><img src="(.+?)" border="1" width=120 height=90 /></a>').findall(html)
    for name, link, thumb in match:
        if not re.search('http://', thumb):
            thumb = main_url + thumb
        if not re.search('veetle', link):
            addon.add_video_item({'mode': 'channel', 'url': link}, {'title': name}, img=thumb)
            	
    
def mainmenu():
    turl = showlist_url_1
    tvchannels(turl, 1)
    #addon.add_directory({'mode': 'tvchannels', 'url': showlist_url_1, 'page_num': page}, {'title': 'Live TV Shows & Movies'}, img=icon_path + 'newtv.png')
    #addon.add_directory({'mode': 'classics', 'url': classic_shows_url % page, 'page_num': page}, {'title': 'Classic TV Shows'}, img=icon_path + 'retrotv.png')
    #addon.add_directory({'mode': 'livetv', 'url': livetv_pages % '', 'page_num': page}, {'title': 'Live TV Channels'}, img=icon_path + 'retrotv.png')


if mode == 'main':
    mainmenu()


elif mode == 'mainexit':
    sys_exit()
    mainmenu()


elif mode == 'tvchannels':
    tvchannels()


elif mode == 'classics':
    print 'Retrieving: %s' % url
    html = net.http_GET(url).content

    page = int(page_num)    
    if page > 1:
        addon.add_directory({'mode': 'mainexit'}, {'title': '[COLOR red]Back to Main Menu[/COLOR]'}, img=icon_path + 'back_arrow.png')

    if page < 6:
        page = page +  1
        addon.add_directory({'mode': 'classics', 'url': classic_shows_url % page, 'page_num': page}, {'title': '[COLOR blue]Next Page[/COLOR]'}, img=icon_path + 'next_arrow.png')

    match = re.compile('<td width=110><a href="(.+?)"><img src="(.+?)" border="0" width=100 height=60 />(.+?)</a>').findall(html)
    for link, thumb, name in match:
        if not re.search('http://', thumb):
            thumb = main_url + thumb
        addon.add_video_item({'mode': 'channel', 'url': classic_url + link}, {'title': name}, img=thumb)


elif mode == 'livetv':
    print 'Retrieving: %s' % url
    html = net.http_GET(url).content

    page = int(page_num)    
    if page > 1:
        addon.add_directory({'mode': 'mainexit'}, {'title': '[COLOR red]Back to Main Menu[/COLOR]'}, img=icon_path + 'back_arrow.png')

    if page < 7:
        page = page +  1
        addon.add_directory({'mode': 'livetv', 'url': livetv_pages % page, 'page_num': page}, {'title': '[COLOR blue]Next Page[/COLOR]'}, img=icon_path + 'next_arrow.png')

    match = re.compile('<td width="100%" .+? href="(.+?)"><img border="0" src="(.+?)" style=.+?></a>(.+?)</td>').findall(html)
    for link, thumb, name in match:
        if not re.search('http://', thumb):
            thumb = main_url + thumb
        addon.add_video_item({'mode': 'channel', 'url': livetv_url + link}, {'title': name}, img=thumb)

    
elif mode == 'exit':
    sys_exit()


if not play:
    addon.end_of_directory()