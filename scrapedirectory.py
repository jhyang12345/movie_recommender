#-*- coding: utf-8 -*-

import requests, codecs, urllib, re
import urllib.request
from bs4 import BeautifulSoup
from pymongo import MongoClient

testurl = 'http://movie.naver.com/movie/sdb/browsing/bmovie.nhn?open=2016&nation=KR&page=14'
browseurl = 'http://movie.naver.com/movie/sdb/browsing/bmovie.nhn?'
baseurl = 'http://movie.naver.com'

banlist = ['TV시리즈', 'TV영화', '단편영화', '비디오영화', '옴니버스영화', '뮤직비디오', '옴니버스영화', '웹드라마', '인터넷영화']

def getparams():
    years = open('years.txt', 'r')
    countries = open('countries.txt', 'r')
    years = years.read().split()
    countries = countries.read().split()
    ret = []
    for year in years:
        for country in countries:
            for page in range(1, 40):
                ret.append(urllib.parse.urlencode((('open', str(year)), ('nation', str(country)), ('page', str(page)))))
    print(ret)
    return ret


def getmovies(url, dbh):
    try:
        with urllib.request.urlopen(url) as response:
            htmlcode = response.read().decode(response.headers.get_content_charset(), errors='replace')
            #print(htmlcode)
            soup = BeautifulSoup(htmlcode, 'html.parser')

            movielist = soup.findAll("ul", {"class": "directory_list"})[0].findAll('a', class_=lambda x: x != 'green')
            #print(movielist)

            movieul = soup.findAll("ul", {"class": "directory_list"})[0]

            for li in movieul.children:
                soup = BeautifulSoup(str(li), 'html.parser')
                movie = soup.findAll('a', class_=lambda x: x != 'green')
                if movie != []:
                    movie = movie[0]
                    title = movie.text
                    link = baseurl + movie['href']
                    code = link[link.index('=') + 1:]
                    movieitem = {'title': title, 'link': link, 'code': code}
                    #print(movieitem)
                    if dbh.movielist.find({'code': code}).count() < 1:
                        dbh.movielist.insert_one(movieitem)
                        print("Inserting movie: " + title)
                    elif dbh.movielist.find({'code': code}).count() == 1 and '단팥빵' in str(soup):
                        print(soup)
                        seen = False
                        for ban in banlist:
                            if ban in str(soup):
                                seen = True
                                break
                        if seen:
                            dbh.movielist.update_one({'code': code}, {'$set': {'valid': False}})
                            print("Invalid movie!")
                            #print(soup)
                    #else if dbh.movielist.find({'code': code}).count() == 1:
                #print(movie)

            """
            for movie in movielist:
                try:
                    title = movie.text
                    link = baseurl + movie['href']
                    code = link[link.index('=') + 1:]
                    movieitem = {'title': title, 'link': link, 'code': code}
                    #print(movieitem)
                    if dbh.movielist.find({'code': code}).count() < 1:
                        dbh.movielist.insert_one(movieitem)
                        print("Inserting movie: " + title)
                    #else if dbh.movielist.find({'code': code}).count() == 1:

                except Exception as inst:
                    print(inst)
                    #print("Unable to add movie:" + title)
                    continue
            """
    except Exception as inst:
        print(inst)
        print("URL NOT FOUND!")

def getgenres(movie, dbh):
    baseurl = 'http://movie.naver.com/movie/bi/mi/basic.nhn?code='
    ret = []
    with urllib.request.urlopen(baseurl + movie['code']) as response:
        htmlcode = response.read().decode(response.headers.get_content_charset(), errors='replace')
        soup = BeautifulSoup(htmlcode, 'html.parser')
        #print(soup.prettify())
        links = soup.findAll('a')
        for link in links:
            try:
                if 'movie/sdb/browsing/bmovie.nhn?genre=' in str(link):
                    ret.append(link.text)

            except Exception as inst:
                print(inst)
                print("Error with something!")
                continue
    #    dbh.movielist.update_one({'_id': movie['_id']}, {'$set': {'genre': []}})
        for genre in ret:
            dbh.movielist.update_one({'_id': movie['_id']}, {'$addToSet': {'genre': genre}})
        print(ret)
    #movies = BeautifulSoup(soup.findAll("ul", {"class": "directory_list"}), 'lxml')

def main():
    try:
        c = MongoClient(host="localhost", port=27018)
        dbh = c['moviedb']
    except:
        print("Error connecting to database!")
        return

    params = getparams()

#start with fresh palette
#    dbh.movielist.delete_many({})


    for param in params:
        getmovies(browseurl + param, dbh)
#        getgenres(browseurl + param, dbh)
    movielist = list(dbh.movielist.find({'valid': True}))
#    for movie in movielist:
#        getgenres(movie, dbh)


if __name__ == '__main__':
    main()
