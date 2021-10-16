__title__ = 'DSRP PERU'
__author__ = 'Alejandro Hurtado Chacñama'
__license__ = 'BSD'
__copyright__ = 'copyleft 2020'

"""Prueba de concepto con fines educativos,
extracion de los últimos 19 posts de paginas públiacas fb
"""

import requests
from lxml import html
from bs4 import BeautifulSoup
import urllib
from urllib.parse import urlparse, parse_qs
import json
from newspaper import Article, Config
from newspaper.article import ArticleException, ArticleDownloadState
from datetime import datetime, timezone

def save_data_local(data):
    """
    Almacenamos todos log en archivo, para tener como referencia de todo el trazado del proceso de descarga   
    """
    f = open('data-posts-fb.json', 'a')
    f.write('\n' + str(data))
    f.close()
    return
def config_newspaper():
    ''''
    proxy : random
    languaje : es,
    user_agent: random
    return Config[]
    '''
    config = Config()
    config.language = 'es'
    config.request_timeout = 12
    return config

def downloadLink(link):
    """Descarga el contenido del link"""
    intento = 0
    urlDescargado = False
    result = {}
    result['link_title'] = ''
    result['link_summary'] = ''
    result['link_text'] = ''
    result['link_canonical'] = ''
    while True:
        if(intento == 10):
            #   print('IMPOSIBLE DE DESCARGAR LA URL: ',self.link)
            urlDescargado = False
            break
        try:
            article = Article(url=link, config=config_newspaper())
            article.download()
            urlDescargado = True
        except Exception as e:
            print ("Ocurrio error en descarga de datos con newspaper:", e)
            pass
        #   print('NO SE PUDO DESCAGAR LA URL',self.link,' VOLVIENDO A INTENTENTAR')
        #   print(e)
            # por seguridad volvemos a optener proxy
        if(article.download_state == ArticleDownloadState.SUCCESS):
            break
        intento = intento + 1
        #print('reintento numero:',intento,' para la URL:',self.link)

    if(urlDescargado):
        article.parse()
        result['link_title'] = article.title
        result['link_summary'] = article.summary
        result['link_text'] = article.text
        result['link_canonical'] = article.canonical_link
    return result

def extract_content_post(wrapper):
    """Extraccion del contenido de cada posts de fb feed"""
    flagRegisterFeedHistory = False
    try:
        timesTamp = None
        texto = wrapper.xpath(
            "*//div[contains(@class,'userContent')]//text()")
        texto = (''.join(texto))

        if(texto == ''):
            texto = wrapper.xpath("*//p//text()")
            texto = (''.join(texto))

        for bad in wrapper.xpath("*//div[contains(@class,'userContent')]"):
            bad.getparent().remove(bad)
        # print(texto)
        timesTamp = wrapper.xpath(
            "*//span[contains(@class,'z_c3pyo1brp')]/span/a/abbr/@data-utime")
        if(len(timesTamp) == 0):
            timesTamp = wrapper.xpath(
                "*//span[contains(@class,'z_c3pyo1brp')]/span/abbr/@data-utime")
            #print('ingreso timesTamp')
        if timesTamp:
            timesTamp = timesTamp[0]
        typePost = ''
        video = wrapper.xpath("*//video")
        hr = wrapper.xpath(
            "*//span[contains(@class, 'z_c3pyo1brp')]/span/a/@href")

        if len(hr) == 0:
            hr = wrapper.xpath("*//span[contains(@class, 'z_c3pyo1brp')]/span/a/@href")
        #print("el hr, ts y video", hr, timesTamp, video)
        if(len(hr) == 0):
            hr = wrapper.xpath("*//h5/span/span/a/@href")
            print("el hr2", hr)
            parsehr = urlparse(hr[0])
            qre = parse_qs(parsehr.query)
            # print ("QRE:", qre.get('set'))
            if qre.get('set') or timesTamp:
                hr = user_name+'/posts/'+qre.get('set')[0].replace('a.', '')
            else:
                print ("POSIBLEMENTE el post es una publicacion PATROCINADO")
                f = open('log-scraping_fb.txt', 'a')
                mensaje = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ') + " : Usuario :" \
                + "user_name" + " : id_page :" + "id_page" + ": Error : " + \
                    " : POSIBLEMENTE el post es una publicacion PATROCINADO que no contiene fecha de publicacion o url"
                f.write('\n' + mensaje)
                f.close()
                return

        else:
            hr = hr[0]
            #hr = wrapper.xpath("*//span[contains(@class, 'z_c3pyo1brp')]/span/a/@href")
        try:
            id_page = video = wrapper.xpath("//meta[@property='al:ios:url']/@content")[0].split('=')[1]
        except Exception as e:
            print('Error id page:', e)
    

        linkPost = urllib.parse.urljoin(
            'https://www.facebook.com/', hr)
        # print(linkPost)

        if(linkPost.find('permalink.php') >= 0):
            # 'https://www.facebook.com/permalink.php?story_fbid=1628077893945014&id=882801821805962'
            parseTemp = urlparse(linkPost)
            b = parse_qs(parseTemp.query)
            linkPost = 'https://www.facebook.com/' + \
                id_page+'/posts/'+b.get('story_fbid')[0]
            # print(linkPost)
            # exit()
        parseLinkPost = urlparse(linkPost)
        pathLinkPost = parseLinkPost.path.split('/')
        if(parseLinkPost.path[len(parseLinkPost.path)-1:len(parseLinkPost.path)] == '/'):
            idFeed = pathLinkPost[len(pathLinkPost)-2]
        else:
            idFeed = pathLinkPost[len(pathLinkPost)-1]
        id = id_page+'_'+idFeed
        
        urlImg = ''
        imgs = wrapper.xpath("*//img")
        mayorTamanio = 0
        if(len(video) > 0):
            typePost = 'video'
        for img in imgs:
            w = img.xpath('@width')
            h = img.xpath('@height')
            if(len(w) == 0):
                w = 0
            else:
                w = int(w[0])
            if(len(h) == 0):
                h = 0
            else:
                h = int(h[0])
            style = img.xpath('@style')
            xpathImg = img.xpath('@src')[0]
            if(len(video) > 0 and len(style) > 0 and style[0].find('background-image: url(') >= 0):
                urlImg = style[0].replace(
                    "background-image: url('", '')
                xpathImg = urlImg.replace("');", '')
                xpathImg = urllib.parse.quote(xpathImg)
                xpathImg = xpathImg.replace('%5C3a%20', ':').replace(
                    '%3F', '?').replace('%5C3d%20', '=').replace('%5C26%20', '&')
                w = 1000
                h = 1000
            tamanio = w*h
            if(mayorTamanio < tamanio):
                mayorTamanio = tamanio
                urlImg = xpathImg
            pass

        urlLink = ''
        urls = wrapper.xpath("*//a[contains(@target,'_blank')]")
        for url in urls:
            url = (url.xpath('@href')[0])
            if(url.find('https://l.facebook.com/l.php') >= 0):
                a = urlparse(url)
                b = parse_qs(a.query)
                urlLink = b.get('u')[0]
                typePost = 'link'
            pass

        if(typePost == ''):
            # print(pathLinkPost)
            if(pathLinkPost[2] == 'photos'):
                typePost = 'photo'
            else:
                if(pathLinkPost[2] == 'posts'):
                    typePost = 'status'
        result = {}
        result['id'] = id
        result['id_page'] = id.split('_')[0]
        result['message'] = texto
        # result['timesTamp']=timesTamp
        result['created_time'] = datetime.utcfromtimestamp(
            int(timesTamp)).strftime('%Y-%m-%dT%H:%M:%SZ')
        if(flagRegisterFeedHistory == False):
            result['date_register'] = datetime.utcfromtimestamp(
                int(timesTamp)).strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            result['date_register'] = datetime.utcnow().strftime(
                '%Y-%m-%dT%H:%M:%SZ')
        # result['link_post']=linkPost
        result['permalink_url'] = 'https://www.facebook.com/' + \
            id_page+'/posts/'+idFeed
        result['id_feed'] = idFeed
        result['picture'] = urlImg
        result['full_picture'] = urlImg
        result['type'] = typePost

        if(urlLink == ''):
            result['link'] = linkPost
        else:
            result['link'] = urlLink

        if(typePost == 'link'):
            result.update(downloadLink(urlLink))

        if(result['type'] == "" and linkPost.find('/notes/') >= 0):
            typePost = 'note'
            note = None
            try:
                note = Article(result['link'])
                note.download()
                note.parse()
            except Exception as e:
                print("Error de descaga Nota", e)
                f = open('log/log-scraping_web.txt', 'a')
                mensaje = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ') + " : Url : " + \
                    result['link'] + " : No se puedo descargar la Nota" + \
                f.write('\n' + mensaje)
                f.close()
            if note:
                texto = note.title+' '+note.text
                result['type'] = typePost
                result['message'] = texto
            else:
                texto = ""
                result['type'] = typePost
                result['message'] = texto
        # si no se encuenta TYPE
        if result['type'] == ''or result['type'] == None:
            result['type'] = "status"
            print("POSIBLEMENTE NO TIENE TYPE")
            print(result['permalink_url'])

        return result
    except Exception as e:
        print ("Error de extraccion de contenido del post:", e)

def scraping_fb(user_name):
    """"Scraping de los primeros 19 posts fb"""
    print ("user_name:", user_name)
    url = 'https://www.facebook.com/pg/'+user_name+'/posts/'
    print('iniciando:', url)
    response = None
    try:
        print("descargando html--->", url)
        response = requests.get(url)
    except Exception as e:
        print("Erro al visitar a fb ----------->", e)

    if response:
        tree = html.fromstring(response.text)

        wrappers = tree.xpath(
            "//div[contains(@class,'userContentWrapper')]")
        resultFeeds = []

        dobleUserContentWrapper = tree.xpath(
            "//div[contains(@class,'userContentWrapper')]/*//div[contains(@class,'userContentWrapper')]")
        print('Procesando extración de posts...')
        for wrapper in wrappers:
            if wrapper in dobleUserContentWrapper:
                continue
            result_data_content = extract_content_post(wrapper)
            if result_data_content:
                resultFeeds.append(result_data_content)
        print ('Terminó de extraer los post..')
        print ('Guardando..')
        # print ('Guardando..', json.dumps(resultFeeds))
        save_data_local(json.dumps(resultFeeds))


scraping_fb('DataScienceResearch')
