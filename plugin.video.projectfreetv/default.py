import xbmc, xbmcgui, xbmcplugin
import urllib
import re, string
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
import urlresolver
from metahandler import metahandlers

addon = Addon('plugin.video.projectfreetv', sys.argv)
net = Net()

#Common Cache
import xbmcvfs
dbg = False # Set to false if you don't want debugging

#Common Cache
try:
  import StorageServer
except:
  import storageserverdummy as StorageServer
cache = StorageServer.StorageServer('plugin.video.projectfreetv')


##### Queries ##########
play = addon.queries.get('play', '')
mode = addon.queries['mode']
video_type = addon.queries.get('video_type', '')
section = addon.queries.get('section', '')
url = addon.queries.get('url', '')
title = addon.queries.get('title', '')
name = addon.queries.get('name', '')
imdb_id = addon.queries.get('imdb_id', '')
season = addon.queries.get('season', '')
episode = addon.queries.get('episode', '')

print '---------------------------------------------------------------'
print '--- Mode: ' + str(mode)
print '--- Play: ' + str(play)
print '--- URL: ' + str(url)
print '--- Video Type: ' + str(video_type)
print '--- Section: ' + str(section)
print '--- Title: ' + str(title)
print '--- Name: ' + str(name)
print '--- IMDB: ' + str(imdb_id)
print '--- Season: ' + str(season)
print '--- Episode: ' + str(episode)
print '---------------------------------------------------------------'

################### Global Constants #################################

#URLS
MainUrl = 'http://www.free-tv-video-online.me/'
SearchUrl = MainUrl + 'search/?q=%s&md=%s'
MovieUrl = MainUrl + "movies/"
TVUrl = MainUrl + "internet/"

#PATHS
AddonPath = addon.get_path()
IconPath = AddonPath + "/icons/"

#VARIABLES
SearchMovies = 'movies'
SearchTV = 'shows'
SearchAll = 'all'

VideoType_Movies = 'movie'
VideoType_TV = 'tvshow'
VideoType_Season = 'season'
VideoType_Episode = 'episode'


#################### Addon Settings ##################################

#Helper function to convert strings to boolean values
def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")
  
meta_setting = str2bool(addon.get_setting('use-meta'))

######################################################################

def Notify(typeq, title, message, times, line2='', line3=''):
     if title == '':
          title='PTV Notification'
     if typeq == 'small':
          if times == '':
               times='5000'
          smallicon= IconPath + 'icon.png'
          xbmc.executebuiltin("XBMC.Notification("+title+","+message+","+times+","+smallicon+")")
     elif typeq == 'big':
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ', line2, line3)
     else:
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')


def setView(content, viewType):
    
    # set content type so library shows more views and info
    if content:
        xbmcplugin.setContent(int(sys.argv[1]), content)
    if addon.get_setting('auto-view') == 'true':
        xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.get_setting(viewType) )
    
    # set sort methods - probably we don't need all of them
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )


def add_favourite():
    saved_favs = cache.get('favourites_' + video_type)
    favs = []
    
    if saved_favs:
        favs = eval(saved_favs)
        if favs:
            if (title, name, imdb_id, season, episode, url) in favs:
                Notify('small', 'Favourite Already Exists', name.title() + ' already exists in your PTV favourites','')
                return

    favs.append((title, name, imdb_id, season, episode, url))
    cache.set('favourites_' + video_type, str(favs))
    Notify('small', 'Added to favourites', name.title() + ' added to your PTV favourites','')


def remove_favourite():
    saved_favs = cache.get('favourites_' + video_type)
    if saved_favs:
        favs = eval(saved_favs)
        favs.remove((title, name, imdb_id, season, episode, url))
        cache.set('favourites_' + video_type, str(favs))
        xbmc.executebuiltin("XBMC.Container.Refresh")


def refresh_movie(vidtitle, year=''):

    metaget=metahandlers.MetaData()
    search_meta = metaget.search_movies(vidtitle)
    
    if search_meta:
        movie_list = []
        for movie in search_meta:
            movie_list.append(movie['title'] + ' (' + str(movie['year']) + ')')
        dialog = xbmcgui.Dialog()
        index = dialog.select('Choose', movie_list)
        
        if index > -1:
            new_imdb_id = search_meta[index]['imdb_id']
            new_tmdb_id = search_meta[index]['tmdb_id']       
            meta = metaget.update_meta('movie', vidtitle, imdb_id=imdb_id, new_imdb_id=new_imdb_id, new_tmdb_id=new_tmdb_id, year=year)   
            xbmc.executebuiltin("Container.Refresh")
    else:
        msg = ['No matches found']
        addon.show_ok_dialog(msg, 'Refresh Results')


def episode_refresh(vidname, imdb, season_num, episode_num):
    #refresh info for an episode   

    metaget=metahandlers.MetaData()
    metaget.update_episode_meta(vidname, imdb, season_num, episode_num)
    xbmc.executebuiltin("XBMC.Container.Refresh")


def season_refresh(vidname, imdb, season_num):

    metaget=metahandlers.MetaData()          	
    metaget.update_season(vidname, imdb, season_num)
    xbmc.executebuiltin("XBMC.Container.Refresh")


def get_metadata(video_type, vidtitle, vidname='', year='', imdb='', season_list=None, season_num=0, episode_num=0):
    
    if meta_setting:
        #Get Meta settings
        movie_covers = addon.get_setting('movie-covers')
        tv_banners = addon.get_setting('tv-banners')
        tv_posters = addon.get_setting('tv-posters')
        
        movie_fanart = addon.get_setting('movie-fanart')
        tv_fanart = addon.get_setting('tv-fanart')
            
        metaget=metahandlers.MetaData()
    
        if video_type in (VideoType_Movies, VideoType_TV):
            meta = metaget.get_meta(video_type, vidtitle, year=year)
    
        if video_type == VideoType_Season:
            returnlist = True
            if not season_list:
                season_list = []
                season_list.append(season_num)
                returnlist = False
            meta = metaget.get_seasons(vidtitle, imdb, season_list)
            if not returnlist:
                meta = meta[0]
    
        if video_type == VideoType_Episode:
            meta=metaget.get_episode_meta(vidname, imdb, season_num, episode_num)
        
        #Check for and blank out covers if option disabled
        if video_type==VideoType_Movies and movie_covers == 'false':
            meta['cover_url'] = ''
        elif video_type==VideoType_TV and tv_banners == 'false':
            meta['cover_url'] = ''
    
        #Check for banners vs posters setting    
        if video_type == VideoType_TV and tv_banners == 'true' and tv_posters == 'false':
            meta['cover_url'] = meta['banner_url']
        
        #Check for and blank out fanart if option disabled
        if video_type==VideoType_Movies and movie_fanart == 'false':
            meta['backdrop_url'] = ''
        elif video_type in (VideoType_TV, VideoType_Episode) and tv_fanart == 'false':
            meta['backdrop_url'] = ''

    else:
        meta = {}
        meta['title'] = vidname
        meta['cover_url'] = ''
        meta['imdb_id'] = imdb
        meta['backdrop_url'] = ''
        meta['year'] = year
        if video_type in (VideoType_TV, VideoType_Episode):
            meta['TVShowTitle'] = vidtitle

    return meta


def add_contextmenu(use_meta, video_type, link, vidtitle, vidname, favourite, watched='', imdb='', year='', season_num=0, episode_num=0):
    
    contextMenuItems = []
    contextMenuItems.append(('Info', 'XBMC.Action(Info)'))

    #Check if we are listing items in the Favourites list
    if favourite:
        contextMenuItems.append(('Delete from Favourites', 'XBMC.RunPlugin(%s?mode=del_fav&video_type=%s&title=%s&name=%s&url=%s&imdb_id=%s&season=%s&episode=%s)' % (sys.argv[0], video_type, vidtitle.encode('utf-8'), vidname.encode('utf-8'), link, imdb, season_num, episode_num)))
    else:
        contextMenuItems.append(('Add to Favourites', 'XBMC.RunPlugin(%s?mode=add_fav&video_type=%s&title=%s&name=%s&url=%s&imdb_id=%s&season=%s&episode=%s)' % (sys.argv[0], video_type, vidtitle.encode('utf-8'), vidname.encode('utf-8'), link, imdb, season_num, episode_num)))

    #Meta is turned on so enable extra context menu options
    if use_meta:
        if watched == 6:
            watched_mark = 'Mark as Watched'
        else:
            watched_mark = 'Mark as Unwatched'

        contextMenuItems.append((watched_mark, 'XBMC.RunPlugin(%s?mode=watch_mark&video_type=%s&title=%s&imdb_id=%s&season=%s&episode=%s)' % (sys.argv[0], video_type, vidtitle, imdb, season_num, episode_num)))
        contextMenuItems.append(('Refresh Metadata', 'XBMC.RunPlugin(%s?mode=refresh_meta&video_type=%s&title=%s&year=%s&season=%s&episode=%s)' % (sys.argv[0], video_type, vidtitle, year, season_num, episode_num)))
        
        #if video_type == VideoType_Movies:
            #contextMenuItems.append(('Search for trailer', 'XBMC.RunPlugin(%s?mode=trailer_search&vidname=%s&url=%s)' % (sys.argv[0], title, link)))                        

    return contextMenuItems


def add_video_directory(mode, video_type, link, vidtitle, vidname, imdb='', year='', season_num=0, totalitems=0, favourite=False):

    meta = get_metadata(video_type, vidtitle, year=year, imdb=imdb, season_num=season_num)
    contextMenuItems = add_contextmenu(meta_setting, video_type, link, vidtitle, vidname, favourite, watched=meta['overlay'], imdb=meta['imdb_id'], year=year, season_num=season_num)

    meta['title'] = vidname
    addon.add_directory({'mode': mode, 'url': link, 'video_type': VideoType_Season, 'imdb_id': meta['imdb_id'], 'title': vidtitle, 'name': vidname, 'season': season_num}, meta, contextMenuItems, context_replace=True, img=meta['cover_url'], fanart=meta['backdrop_url'], total_items=totalitems)


def add_video_item(video_type, section, link, vidtitle, vidname, year='', imdb='', season_num=0, episode_num=0, totalitems=0, favourite=False):

    meta = get_metadata(video_type, vidtitle, vidname, year, imdb=imdb, season_num=season_num, episode_num=episode_num)
    if video_type == VideoType_Movies:
        contextMenuItems = add_contextmenu(meta_setting, video_type, link, vidtitle, meta['title'], favourite, watched=meta['overlay'], imdb=meta['imdb_id'], year=meta['year'])
    else:
        contextMenuItems = add_contextmenu(meta_setting, video_type, link, vidtitle, meta['title'], favourite, watched=meta['overlay'], imdb=meta['imdb_id'], season_num=season_num, episode_num=episode_num)
    
    if video_type == VideoType_Movies:
        addon.add_video_item({'url': link, 'video_type': video_type, 'section': section, 'title': vidtitle, 'name': vidname}, meta, contextMenuItems, context_replace=True, img=meta['cover_url'], fanart=meta['backdrop_url'], total_items=totalitems)
    elif video_type == VideoType_Episode:
        addon.add_video_item({'url': link, 'video_type': video_type, 'section': section, 'title': vidtitle, 'name': vidname}, meta, contextMenuItems, context_replace=True, img=meta['cover_url'], fanart=meta['backdrop_url'], total_items=totalitems)


# Create A-Z Menu
def AZ_Menu(type, url):
     
    addon.add_directory({'mode': type, 
                         'url': url + 'numeric.html', 'letter': '#'},{'title': '#'},
                         img=IconPath + "numeric.png")
    for l in string.uppercase:
        addon.add_directory({'mode': type, 
                             'url': url + str(l.lower()) + '.html', 'letter': l}, {'title': l},
                             img=IconPath + l + ".png")


# Get List of Movies from given URL
def GetMovieList(url):

    html = net.http_GET(url).content
    match = re.compile('<td width="97%" class="mnlcategorylist"><a href="(.+?)"><b>(.+?)[ (]*([0-9]{0,4})[)]*</b></a>(.+?)<').findall(html)

    for link, vidname, year, numlinks in match:
       if re.search("../",link) is not None:
          link = link.strip('\n').replace("../","")
          newUrl = MovieUrl + link
       else:
          newUrl = url + "/" + link
       add_video_item(VideoType_Movies, VideoType_Movies, newUrl, vidname, vidname, totalitems=len(match))
    setView('movies', 'movie-view')

if play:

    sources = []
    html = net.http_GET(url).content
           
    if section == 'movies':
        
        #Check for trailers
        match = re.compile('<a target="_blank" style="font-size:9pt" class="mnlcategorylist" href=".+?id=(.+?)">(.+?)</a>&nbsp;&nbsp;&nbsp;').findall(html)
        for linkid, vidname in match:      
            media = urlresolver.HostedMediaFile(host='youtube', media_id=linkid, title=vidname)
            sources.append(media)        
     
    elif section == 'latestmovies':
        #Search within HTML to only get portion of links specific to movie name
        # TO DO - currently does not return enough of the header for the first link
        r = re.search('<div>%s</div>(.+?)(<div>(?!%s)|<p align="center">)' % (title, title), html, re.DOTALL)
        if r:
            html = r.group(0)
        else:
            html = ''
    
    elif section in ('tvshows', 'episode'):
        #Search within HTML to only get portion of links specific to episode requested
        r = re.search('<td class="episode"><a name=".+?"></a><b>%s</b>(.+?)(<a name=|<p align="center">)' % name, html, re.DOTALL)
        if r:
            html = r.group(1)
        else:
            html = ''   
        
    #Now Add video source links
    match = re.compile('''<a onclick=.+? href=".+?id=(.+?)" target=.+?<div>.+?(|part [0-9]* of [0-9]*)</div>.+?<span class='.*?'>(.*?)</span>.+?Host: (.+?)<br/>.+?class="report">.+?([0-9]*[0-9]%) Said Work''',re.DOTALL).findall(html)
    for linkid, vidname, load, host, working in match:
        if vidname:
           vidname = vidname.title()
        else:
           vidname = 'Full'
        media = urlresolver.HostedMediaFile(host=host, media_id=linkid, title=vidname + ' - ' + host + ' - ' + load + ' - ' + working)
        sources.append(media)
    
    source = urlresolver.choose_source(sources)
    if source:
        stream_url = source.resolve()
    else:
        stream_url = False
      
    #Play the stream
    if stream_url:
        addon.resolve_url(stream_url)


if mode == 'main': 
    addon.add_directory({'mode': 'movies', 'section': 'movies'}, {'title':  'Movies'}, img=IconPath + 'Movies.png')
    addon.add_directory({'mode': 'tv', 'section': 'tv'}, {'title': 'TV Shows'})
    addon.add_directory({'mode': 'search', 'section': SearchAll}, {'title': 'Search All'})
    addon.add_directory({'mode': 'resolver_settings'}, {'title':  'Resolver Settings'}, is_folder=False, img=IconPath + 'Resolver_Settings.png')
    setView(None, 'default-view')

elif mode == 'movies':
    addon.add_directory({'mode': 'moviesaz', 'section': 'moviesaz'}, {'title': 'A-Z'}, img=IconPath + "AZ.png")
    addon.add_directory({'mode': 'moviespopular', 'section': 'moviespopular'}, {'title': 'Popular'})
    addon.add_directory({'mode': 'favourites', 'video_type': VideoType_Movies}, {'title': 'Favourites'})
    addon.add_directory({'mode': 'search', 'section': SearchMovies}, {'title': 'Search'})
    addon.add_directory({'mode': 'movieslatest', 'section': 'movieslatest'}, {'title': 'Latest Added Links'})
    addon.add_directory({'mode': 'moviesgenre', 'section': 'moviesgenre'}, {'title': 'Genre'}, img=IconPath + 'Genre.png')
    addon.add_directory({'mode': 'moviesyear', 'section': 'moviesyear'}, {'title': 'Year'})
    setView(None, 'default-view')

elif mode == 'moviesaz':
    AZ_Menu('movieslist', MovieUrl + 'browse/')
    setView(None, 'default-view')


elif mode == 'moviesgenre':
    url = MovieUrl
    html = net.http_GET(url).content
    match = re.compile('<a class ="genre" href="/(.+?)"><b>(.+?)</b></a><b>').findall(html)

    # Add each link found as a directory item
    for link, genre in match:
        addon.add_directory({'mode': 'movieslist', 'url': MainUrl + link, 'section': 'movies'}, {'title': genre})
    setView(None, 'default-view')


elif mode == 'movieslatest':
    latestlist = []
    url = MovieUrl
    html = net.http_GET(url).content
        
    match = re.compile('''<a onclick='visited.+?' href=".+?" target=.+?<div>(.+?)</div>''',re.DOTALL).findall(html)
    for vidname in match:
        latestlist.append(vidname)

    #convert list to a set which removes duplicates, then back to a list
    latestlist = list(set(latestlist))

    for movie in latestlist:
        add_video_item(VideoType_Movies, 'latestmovies', url, movie, movie, totalitems=len(match))
    setView('movies', 'movie-view')


elif mode == 'moviespopular':
    url = MainUrl
    html = net.http_GET(url).content
    match = re.compile('''<td align="center"><a href="(.+?)">(.+?)</a></td>''',re.DOTALL).findall(html)

    # Add each link found as a directory item
    for link, vidname in match:
       is_movie = re.search('/movies/', link)
       if vidname != "...more" and is_movie:
          add_video_item(VideoType_Movies, VideoType_Movies, link, vidname, vidname, totalitems=len(match))
    setView('movies', 'movie-view')


elif mode == 'moviesyear':
    url = MovieUrl
    html = net.http_GET(url).content
    match = re.compile('''<td width="97%" nowrap="true" class="mnlcategorylist"><a href="(.+?)"><b>(.+?)</b></a></td>''').findall(html)

    # Add each link found as a directory item
    for link, year in match:
       addon.add_directory({'mode': 'movieslist', 'url': url + urllib.quote(link), 'section': 'movies'}, {'title': year})
    setView(None, 'default-view')


elif mode == 'movieslist':
   GetMovieList(url)


elif mode == 'tv':
    addon.add_directory({'mode': 'tvaz', 'section': 'tvaz'}, {'title': 'A-Z'}, img=IconPath + "AZ.png")
    addon.add_directory({'mode': 'tvpopular', 'section': 'tvpopular'}, {'title': 'Popular'})
    #addon.add_directory({'mode': 'tvlatest', 'section': 'tvlatest'}, 'Latest')
    addon.add_directory({'mode': 'favourites', 'video_type': VideoType_TV}, {'title': 'Favourites'})
    addon.add_directory({'mode': 'search', 'section': SearchTV}, {'title': 'Search'})    	
    addon.add_directory({'mode': 'tvlastadded', 'section': 'tv24hours', 'url': TVUrl + 'index_last.html'}, {'title': 'Last 24 Hours'})
    addon.add_directory({'mode': 'tvlastadded', 'section': 'tv3days', 'url': TVUrl + 'index_last_3_days.html'}, {'title': 'Last 3 Days'})
    addon.add_directory({'mode': 'tvlastadded', 'section': 'tv7days', 'url': TVUrl + 'index_last_7_days.html'}, {'title': 'Last 7 Days'})
    addon.add_directory({'mode': 'tvlastadded', 'section': 'tvmonth', 'url': TVUrl + 'index_last_30_days.html'}, {'title': 'This Month'})
    addon.add_directory({'mode': 'tvlastadded', 'section': 'tv90days', 'url': TVUrl + 'index_last_365_days.html'}, {'title': 'Last 90 Days'})
    setView(None, 'default-view')

elif mode == 'tvaz':
    AZ_Menu('tvseries-az',TVUrl)
    setView(None, 'default-view')

elif mode == 'tvseries-az':
    url = TVUrl
    letter = addon.queries['letter']
    
    html = net.http_GET(url).content
    r = re.search('<a name="%s">(.+?)(<a name=|</table>)' % letter, html, re.DOTALL)
    
    if r:
        match = re.compile('class="mnlcategorylist"><a href="(.+?)"><b>(.+?)</b></a> (<sub>New Episode!</sub>|)</td>').findall(r.group(1))
        for link, vidtitle, newep in match:
            vidname = vidtitle
            if newep:
                vidname = vidtitle + ' [COLOR red]New Episode![/COLOR]'
            add_video_directory('tvseasons', VideoType_TV, TVUrl + link, vidtitle, vidname, totalitems=len(match))
    setView('tvshows', 'tvshow-view')


elif mode == 'tvlastadded':
    html = net.http_GET(url).content
    full_match = re.compile('class="mnlcategorylist"><a href="(.+?)#.+?"><b>((.+?) - Season ([0-9]+) Episode ([0-9]+)) <').findall(html)
    match = re.compile('<a name="(.+?)"></a>(.+?)(<td colspan="2">|</table>)', re.DOTALL).findall(html)
    for added_date, inside_html, endtag in match:
        addon.add_directory({'mode': 'none'}, {'title': '[COLOR blue]' + added_date + '[/COLOR]'}, is_folder=False, img='')
        inside_match = re.compile('class="mnlcategorylist"><a href="(.+?)#.+?"><b>((.+?) [\(]*([0-9]{0,4})[\) ]*- Season ([0-9]+) Episode ([0-9]+)) <').findall(inside_html)
        for link, vidname, vidtitle, year, season_num, episode_num in inside_match:

            #Since we are getting season level items, try to grab the imdb_id of the TV Show first to make meta get easier
            if meta_setting:
                meta = get_metadata(VideoType_TV, vidtitle, year=year)
                imdb = meta['imdb_id']
            else:
                imdb = ''

            add_video_directory('tvepisodes', VideoType_Season, TVUrl + link, vidtitle, vidname, imdb=imdb, season_num=season_num, totalitems=len(full_match))
    setView('seasons', 'season-view')


elif mode == 'tvpopular':
    url = MainUrl
    html = net.http_GET(url).content
    match = re.compile('<td align="center"><a href="(.+?)">(.+?)</a></td>').findall(html)
    for link, vidname in match:
        is_tv = re.search('/internet/', link)
        if vidname != "...more" and is_tv:
            add_video_directory('tvseasons', VideoType_TV, link, vidname, vidname, totalitems=len(match))
    setView('tvshows', 'tvshow-view')


elif mode == 'tvseasons':
    html = net.http_GET(url).content
    match = re.compile('class="mnlcategorylist"><a href="(.+?)"><b>(.+?)</b></a>(.+?)<').findall(html)
    seasons = re.compile('class="mnlcategorylist"><a href=".+?"><b>Season ([0-9]+)</b></a>.+?<').findall(html)
    #seasons = list(xrange(len(match)))
    
    #If we have more matches than seasons found then we might have an extra 'special' season, add it as Season '0'
    if len(match) > len(seasons):
        seasons.insert(0,'0')

    season_meta = {}    
    if meta_setting:
        season_meta = get_metadata(video_type, title, imdb=imdb_id, season_list=seasons)
    else:
        meta = {}
        meta['TVShowTitle'] = title
        meta['cover_url'] = ''
        meta['imdb_id'] = ''
        meta['backdrop_url'] = ''
        meta['overlay'] = 0
        
    num = 0
    for link, season_num, episodes in match:
        if season_meta:
            meta = season_meta[num]
        meta['title'] = season_num + episodes
        link = url + '/' + link
        contextMenuItems = add_contextmenu(meta_setting, video_type, link, title, meta['title'], favourite=False, watched=meta['overlay'], imdb=meta['imdb_id'], season_num=seasons[num])
        addon.add_directory({'mode': 'tvepisodes', 'url': link, 'video_type': VideoType_Season, 'imdb_id': meta['imdb_id'], 'title': title, 'name': meta['title'], 'season': seasons[num]}, meta, contextMenuItems, context_replace=True, img=meta['cover_url'], fanart=meta['backdrop_url'], total_items=len(match))
        num = num + 1
    setView('seasons', 'season-view')


elif mode == 'tvepisodes':
    html = net.http_GET(url).content.encode('utf-8')
    match = re.compile('<td class="episode"><a name=".+?"></a>(.*?)<b>(.+?)</b></td>[\r\n\t]*(<td align="right".+?;Air Date: (.+?)</div>)*', re.DOTALL).findall(html)
    for next_episode, vidname, empty, next_air in match:
        episode_num = re.search('([0-9]{0,2})\.', vidname)
        if episode_num:
            episode_num = episode_num.group(1)
        else:
            episode_num = 0
        if not next_episode:
            add_video_item(VideoType_Episode, VideoType_Episode, url, title, vidname, imdb=imdb_id, season_num=season, episode_num=episode_num, totalitems=len(match))
        else:
            meta = get_metadata(VideoType_Episode, title, vidname, imdb=imdb_id, season_num=season, episode_num=episode_num)
            meta['title'] = '[COLOR blue]Next Episode: %s - %s[/COLOR]' % (next_air, vidname)
            addon.add_directory({'mode': 'none'}, meta, is_folder=False, img=meta['cover_url'], fanart=meta['backdrop_url'])            
    setView('episodes', 'episode-view')
    

elif mode == 'search':

    #First check and retrieve previous searches
    search_text = cache.get('search_' + section)
    
    kb = xbmc.Keyboard(search_text, 'Search Project Free TV - %s' % section.capitalize(), False)
    kb.doModal()
    if (kb.isConfirmed()):                   
        search_text = kb.getText()
        if search_text:
            cache.set('search_' + section, search_text)
            search_quoted = urllib.quote(search_text)
            url = SearchUrl % (search_quoted, section)
            html = net.http_GET(url).content    
            
            match = re.compile('<td width="97%" class="mnlcategorylist">[\r\n\t]*<a href="(.+?)">[\r\n\t]*<b>(.+?)[ (]*([0-9]{0,4})[)]*</b>').findall(html)
            for link, vidname, year in match:
                link = MainUrl + link
                if re.search('/movies/', link):
                    add_video_item(VideoType_Movies, VideoType_Movies, link, vidname, vidname, year, totalitems=len(match))
                else:
                    add_video_directory('tvseasons', VideoType_TV, link, vidname, vidname, year=year, totalitems=len(match))
    setView(None, 'default-view')


elif mode == 'favourites':

    #Add Season/Episode sub folders
    if video_type == VideoType_TV:
        addon.add_directory({'mode': 'favourites', 'video_type': VideoType_Season}, {'title': '[COLOR blue]Seasons[/COLOR]'})
        addon.add_directory({'mode': 'favourites', 'video_type': VideoType_Episode}, {'title': '[COLOR blue]Episodes[/COLOR]'})

    #Grab saved favourites from DB and populate list
    saved_favs = cache.get('favourites_' + video_type)
    if saved_favs:
        favs = sorted(eval(saved_favs), key=lambda fav: fav[1])
        for fav in favs:
            if video_type in (VideoType_Movies, VideoType_Episode):
                add_video_item(video_type, video_type, fav[5], fav[0].title(), fav[1].title(), imdb=fav[2], season_num=fav[3], episode_num=fav[4], totalitems=len(favs), favourite=True)
            elif video_type == VideoType_TV:
                add_video_directory('tvseasons', video_type, fav[5], fav[0].title(), fav[1].title(), imdb=fav[2], season_num=fav[3], totalitems=len(favs), favourite=True)
            elif video_type == VideoType_Season:
                add_video_directory('tvepisodes', video_type, fav[5], fav[0].title(), fav[1].title(), imdb=fav[2], season_num=fav[3], totalitems=len(favs), favourite=True)
    setView(video_type +'s', video_type + '-view')


elif mode == 'add_fav':
    add_favourite()


elif mode == 'del_fav':
    remove_favourite()


elif mode == 'refresh_meta':
    if video_type == VideoType_Movies:
        refresh_movie(title)

    elif video_type == VideoType_TV:
        Notify('small', 'Refresh TV Show', 'Feature not yet implemented','')
    elif video_type == VideoType_Season:
        season_refresh(title, imdb_id, season)
    elif video_type == VideoType_Episode:
        episode_refresh(title, imdb_id, season, episode)


elif mode == 'watch_mark':
    metaget=metahandlers.MetaData()
    metaget.change_watched(video_type, title, imdb_id, season=season, episode=episode)
    xbmc.executebuiltin("Container.Refresh")


elif mode == 'resolver_settings':
    urlresolver.display_settings()


if not play:
    addon.end_of_directory()