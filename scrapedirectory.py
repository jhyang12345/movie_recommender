#-*- coding: utf-8 -*-

import requests, codecs, urllib, re
import urllib.request
from bs4 import BeautifulSoup
from pymongo import MongoClient

testurl = 'http://movie.naver.com/movie/sdb/browsing/bmovie.nhn?open=2016&nation=KR&page=14'
browseurl = 'http://movie.naver.com/movie/sdb/browsing/bmovie.nhn?'
baseurl = 'http://movie.naver.com'

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
                except Exception as inst:
                    print(inst)
                    #print("Unable to add movie:" + title)
                    continue
    except Exception as inst:
        print(inst)
        print("URL NOT FOUND!")

def getgenres(url, dbh):
    with urllib.request.urlopen(url) as response:
        htmlcode = response.read().decode(response.headers.get_content_charset(), errors='replace')
        soup = BeautifulSoup(htmlcode, 'html.parser')
        soup = BeautifulSoup(str(soup.find("ul", {"class": "directory_list"})))
        #print(soup.prettify())
        movies = soup.ul.findAll('li',  recursive=False)
        for movie in movies:
            try:
                newsoup = BeautifulSoup(str(movie), 'html.parser')
                print(newsoup)
                titleholder = newsoup.findAll('a', class_=lambda x: x != 'green')
                print(titleholder)
                title = titleholder[0].text
                link = baseurl + titleholder[0]['href']
                code = link[link.index('=') + 1:]

                print(title)
                for a in newsoup.findAll('a'):
                    if 'genre' in str(a):
                        print(a.text.split('/'))
                movieitem = {'title': title, 'link': link, 'code': code, 'genre': a.text.split('/')}
                if dbh.movielist.find({'code': code}).count() < 1:
                    dbh.movielist.insert_one(movieitem)
            except Exception as inst:
                print(inst)
                print("Error with something!")
                continue

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
#        getmovies(browseurl + param, dbh)
        getgenres(browseurl + param, dbh)


if __name__ == '__main__':
    main()
