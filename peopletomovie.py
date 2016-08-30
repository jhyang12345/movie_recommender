from pymongo import MongoClient
import urllib.request, datetime
from bs4 import BeautifulSoup


def releasedate(movie, dbh):
    baseurl = 'http://movie.naver.com/movie/bi/mi/detail.nhn?code='
    try:
        dbh.movielist.update_one({'_id': movie['_id']}, {'$set': {'date': datetime.datetime(1980, 1, 1)}})
        with urllib.request.urlopen(baseurl + movie['code']) as page:
            page = page.read().decode(page.headers.get_content_charset(), errors='replace')
            soup = BeautifulSoup(page, 'html.parser')
            for link in soup.findAll('a'):
                if '/movie/sdb/browsing/bmovie.nhn?open=' in str(link):
                    if len(link['href'][str(link['href']).index('=') + 1:]) > 4:
                        datestring = link['href'][link['href'].index('=') + 1:]
                        link = str(link)
                        year = int(datestring[:4])
                        month = int(datestring[4:6])
                        day = int(datestring[6:])
                        print(datetime.datetime(year, month, day))
                        dbh.movielist.update_one({'_id': movie['_id']}, {'$set': {'date': datetime.datetime(year, month, day)}})

    except Exception as inst:
        print(repr(inst))
        print(movie['code'], movie['title'])

def main():
    try:
        c = MongoClient(host='localhost', port=27018)
        dbh = c['moviedb']
    except:
        print("Unable to reach database!")
        sys.exit(1)
#    for movie in list(dbh.movielist.find({'valid': True})):
#        releasedate(movie, dbh)
    for movie in dbh.movielist.find({'valid': True, 'rating': {'$ne': 0.0}}):
        director  = movie['director']
        print(director)
    #    dbh.directorlist.update_one({'code': director['code']}, {'$addToSet': {'movies': movie['code']}})
        actors = movie['actors']
        print(actors)
        if actors != None:
            for actor in actors:
                dbh.actorlist.update_one({'code': actor['code']}, {'$addToSet': {'movies': movie['code']}})


if __name__ == '__main__':
    main()
