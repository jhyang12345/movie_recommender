from pymongo import MongoClient
import sys, codecs, re
import urllib.request
from bs4 import BeautifulSoup
from multithreading import multithreading

baseurl = 'http://movie.naver.com'

def getmainactors(movie, dbh):
    baseurl = 'http://movie.naver.com/movie/bi/mi/detail.nhn?code='
    try:
        print("Retrieving main actors.")
        ret = []
        with urllib.request.urlopen(baseurl + movie['code']) as page:
            page = page.read().decode(page.headers.get_content_charset(), errors='replace')
            soup = BeautifulSoup(page, 'html.parser')
            actors = soup.findAll('div', {'class': 'p_info'})
            for actor in actors:
                if '주연' in str(actor):
                    actoritem = {}
                    name = actor.find('a').text
                    link = baseurl + actor.find('a')['href']
                    code = link[link.index('=') + 1:]
                    actoritem = {'name': name, 'link': link, 'code': code}
                    ret.append(actoritem)
                    if dbh.actorlist.find({'code': code}).count() < 1:
                        dbh.actorlist.insert_one(actoritem)
                        print("Inserting:", name)
            return ret
    except Exception as inst:
        print("Invalid movie!")
        print(inst)
        return

def gettraits(movie, dbh):
    link = movie['link']
    title = movie['title']
#    dbh.movielist.update({'_id': movie['_id']}, {'$set': {"valid": True}})
    try:
        with urllib.request.urlopen(link) as page:
            page = page.read().decode(page.headers.get_content_charset(), errors='replace')
            soup = BeautifulSoup(page, 'html.parser')
            print(link)
            audrating = 0
            netrating = 0
            audraters = 0
            netraters = 0

            #actualPointCountWide
            #pointNetizenCountBasic

            scoreholder = soup.find_all('a', class_='ntz_score')
        #    print(scoreholder)
            if scoreholder != []:
                ratingsoup = BeautifulSoup(str(scoreholder[0]), 'html.parser')
                widthcode = ratingsoup.find('span', class_='st_on')['style']
                audrating = float(widthcode[widthcode.index(':') + 1: widthcode.index('%')])
                #dbh.movielist.update({'_id': movie['_id']}, {'$set': {"rating": rating}})
            else:
                #dbh.movielist.update({'_id': movie['_id']}, {'$set': {"valid": False}})
                #print("Invalid movie: no rating")
                audrating = 0
                #return

            netscoreholder = soup.findAll('a', {'id': 'pointNetizenPersentBasic'})
            if netscoreholder != None:
                ratingsoup = BeautifulSoup(str(netscoreholder), 'html.parser')
                widthcode = ratingsoup.find('span', class_='st_on')['style']
                netrating = float(widthcode[widthcode.index(':') + 1: widthcode.index('%')])

            if soup.find('div', {'id': 'actualPointCountWide'}) != None:
                audraters = int(BeautifulSoup(str(soup.find('div', {'id': 'actualPointCountWide'})), 'html.parser').find('em').text.replace(',', ''))
                print(audraters)

            if soup.find('div', {'id': 'pointNetizenCountBasic'}) != None:
                netraters = int(BeautifulSoup(str(soup.find('div', {'id': 'pointNetizenCountBasic'})), 'html.parser').find('em').text.replace(',', ''))
                print(netraters)

            if (audrating != 0.0 or netrating != 0.0) and (netraters > 30 or audraters > 30):
                if netraters > audraters:
                    dbh.movielist.update({'_id': movie['_id']}, {'$set': {"rating": netrating}})
                    dbh.movielist.update({'_id': movie['_id']}, {'$set': {"raters": netraters}})
                    print("Updated rating as:", netrating)
                else:
                    dbh.movielist.update({'_id': movie['_id']}, {'$set': {"rating": audrating}})
                    dbh.movielist.update({'_id': movie['_id']}, {'$set': {"raters": audraters}})
                    print("Updated rating as:", audrating)
            else:
                dbh.movielist.update({'_id': movie['_id']}, {'$set': {"valid": False}})
                print("Invalid movie: no rating!")

            director = ''
            infospec = soup.find('dl', {'class': 'info_spec'})

            newsoup = BeautifulSoup(str(infospec), 'html.parser')

            director = newsoup.find('dt', {'class': 'step2'})
            #print(newsoup)

            #retrieve the director
            if director != None:
                holder = director.find_next_siblings()[0]
                if holder.find('a') != None:
                    directorname = holder.find('a').text
                    directorlink = holder.find('a')['href']
                    directorcode = directorlink[directorlink.index('=') + 1:]
                    directoritem = {'name': directorname, 'link': directorlink, 'code': directorcode}
                    if dbh.directorlist.find({'code': directorcode}).count() < 1:
                        dbh.directorlist.insert_one(directoritem)
                    dbh.movielist.update({'_id': movie['_id']}, {'$set': {'director': directoritem}})
                    print(directorname, directorcode)
                else:
                    dbh.movielist.update({'_id': movie['_id']}, {'$set': {"valid": False}})
                    print("Invalid movie!")
                    print("Not found!")
                    return
            else:
                dbh.movielist.update({'_id': movie['_id']}, {'$set': {"valid": False}})
                print("Invalid movie!")
                print("Not found!")
                return
            mainactors = getmainactors(movie, dbh)
            if mainactors:
                dbh.movielist.update({'_id': movie['_id']}, {'$set': {'actors': getmainactors(movie, dbh)}})
            else:
                dbh.movielist.update({'_id': movie['_id']}, {'$set': {'valid': False}})

    except Exception as inst:
        print(str(inst))
        print("Invalid movie!")
        dbh.movielist.update({'_id': movie['_id']}, {'$set': {"valid": False}})
        return



def main():
    try:
        c = MongoClient(host='localhost', port=27018)
        dbh = c['moviedb']
    except:
        print("Unable to reach database!")
        sys.exit(1)
    movies = list(dbh.movielist.find({}))
    multithreading(gettraits, [[movie, dbh] for movie in movies])


if __name__ == '__main__':
    main()
