from pymongo import MongoClient
import random

def choosegenre(genre, dbh, seen, cands=10):
    thisgenre = dbh.genrecounts.find_one({'type': genre})
    counter = {}
    total = 0

    originalgenre = genre
    for genre in thisgenre:
        if genre != '_id' and genre != 'type':
            counter[genre] = thisgenre[genre]
            total += counter[genre]
    counter[originalgenre] = total * 2 // 3
    total = total + counter[genre]
    keys = list(counter.keys())
    #print(keys)
    ranges = [0]
    for i in range(len(keys)):
        ranges.append(ranges[i] + counter[keys[i]])
        #print(counter[key])

    genrecands = {}
    for key in counter:
        if counter[key] != 0:
            genrecands[key] = []
            for movie in dbh.movielist.find({'valid': True, 'genre': {'$in': [key]}}).sort('rating', -1)[:cands]:
                genrecands[key].append(movie)
            random.shuffle(genrecands[key])
    ret = []
    genrespicked = []
    for _ in range(cands):
        val = random.random() * total
        found = 0
        for i in range(len(keys)):
            if ranges[i] < val < ranges[i + 1] and counter[keys[i]] != 0:
                found = i
                ret.append(genrecands[keys[i]].pop())
                genrespicked.append(keys[i])
                break
    print(genrespicked)
    return ret


def main():
    try:
        c = MongoClient(host='localhost', port=27018)
        dbh = c['moviedb']
    except:
        print("Failed to connect to db!")
    with open('movieseen.txt', 'r') as movieseen:
        movieseen = movieseen.read().split()
        ret = []
        for movie in movieseen:
            genres = dbh.movielist.find_one({'code': movie})['genre']
        #    print(genres)
            for genre in genres:
                ret = ret + choosegenre(genre, dbh, movieseen)

        ret = list(set([code['code'] for code in ret]))
        ret.sort(key=lambda x: dbh.movielist.find_one({'code': x})['rating'])
        for movie in ret[:10]:
            print(dbh.movielist.find_one({'code': movie})['title'])


if __name__ == '__main__':
    main()
