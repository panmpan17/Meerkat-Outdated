 # p_format = "你可以獲得 {xp} 需要 {count} 隻 還剩下 {candy} 顆糖果"

 # def count(n, d):
 #  a = 0
 #  while n >= d:
 #      i = n // d
 #      a += i
 #      n = (n % d) + i
 #  return a, n

 # l = [
 #  # (24, 12), # caterpie
 #  # (81, 12), # weedle
 #  (289, 12), # pidgey
 #  # (273, 25), # rattata
 #  # (99, 50), # venonat
 #  # (60, 50), # Krabby
 #  # (25, 25), # eevee

 # ]

 # xp_total = 0
 # for i in l:
 #  r = count(i[0], i[1])
 #  print(p_format.format(xp=r[0] * 1000, count=r[0], candy=r[1]))
 #  xp_total += r[0] * 1000

 # print("總共 %i 經驗" % xp_total)



#from queue import Queue
#from thrading import Thread
#from time import sleep

#num_thread = 2
#q = Queue()

#url = ""

import requests
import sys
import argparse

def get_all_url(html):
    link_s = html.find("<a ")
    e_urls = []
    while link_s > -1:
        link_e = html.find("</a>", link_s + 1)
        link = html[link_s:link_e]

        url_s = link.find("href=\"")
        url_e = link.find("\"", url_s + 6)
        if (url_s == -1):
            link_s = html.find("<a ", link_e)
            continue
        url = link[url_s + 6: url_e]

        #print("get_all_url:", url)
        e_urls.append(url)
        link_s = html.find("<a ", link_e)
    return e_urls

def crawl(urls):
    opened_url = {}
    num_url = 0

    while len(urls) != 0:
        if num_url == 100:
            num_url = 0
            print("%i url left" % len(urls))
            ask_keep = input("Do You want to keep going? (Y/N)").lower()
            if ask_keep == "n":
                break

        url = urls[0]
        try:
            urls = urls[1:]
        except:
            urls.pop()

        if url in opened_url:
            continue

        print(url)
        num_url += 1
        try:
            r = requests.get(url)
        except:
            opened_url[url] = ""
            continue
        if r.status_code < 400:
            read = r.text
            opened_url[url] = read

            e_urls = get_all_url(read)
            for i in e_urls:
                if len(i) > 1:
                    if i[0] == "/" and i[1] != "/":
                        i = url + i
                    urls.append(i)
        else:
            opened_url[url] = ""

if __name__ == "__main__":
    #class dumy:
    #    pass

    #psr = argparse.ArgumentParser(description="Url you want to Crawl")
    #psr.add_argument("-url"):
    #psr.parse_args(sys.argv[1])
    urls = ["http://pymotw.com/2/Queue/"]
    crawl(urls)





