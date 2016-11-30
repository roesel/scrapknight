#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import numpy as np
import urllib.request
import flask

def process(input):
    matches = []
    for limit in np.arange(0, 300, 30):
        url = 'http://cernyrytir.cz/index.php3?akce=3&limit='+str(limit)+'&edice_magic=KLD&poczob=100&foil=R&triditpodle=ceny&hledej_pouze_magic=1&submit=Vyhledej'
        response = urllib.request.urlopen(url)
        data = response.read()      # a `bytes` object
        text = data.decode('windows-1250') # a `str`; this step can't be used if data is binary
        #with open('input.txt', 'r', encoding="utf8") as myfile:
        #    data = myfile.read().replace('\n', '')

        matches3 = re.findall('<font style="font-weight : bolder;">([^<]*)</font></div>.*?>(\d*)&nbsp;Kč', text, re.DOTALL)
        #print(matches3)
        matches += matches3

    db = {}
    for a in matches:
        if ( (str.find(a[0], ' - lightly played') == -1) and (str.find(a[0], '- foil') == -1) ):
            #print(a[0]+" "+a[1])
            db[a[0].lower()] = {'cost': int(a[1]), 'title': a[0]}

    #print(db)

    found_all = True
    price = 0
    out = ''
    outable = []
    for row in input.splitlines():
        split = row.replace('\n', '').split(' x ')
        if ( (len(split) == 2) and (row[0] != '#') ):
            count = int(split[0])
            name = split[1]
            id = name.lower()
            
            if id in db:
                ppu = db[id]['cost']
                title = db[id]['title']
                
                out += title + " - " + str(count) + " x " + str(ppu) + " CZK" + flask.Markup('<br />')
                multiprice = count * ppu
                outable.append([title, str(count), str(ppu), str(multiprice)])
                price += multiprice
            else:
                found_all = False
                title = name
                out += name+" - "+str(count)+" x ? (card not found)"+flask.Markup('<br />')
                outable.append([title, str(count), "?", "?"])
                
    out += '----------------'+flask.Markup('<br />')
    footer = []
    success = False
    if not found_all:
        out += "Didn't find all cards!!!"+flask.Markup('<br />')
        footer.append(["Minimum price - some cards not found", "", "", str(price)+" CZK"])
    else:
        footer.append(["Full price", "", "",  str(price)+" CZK"])
        success = True
    out += "Full price: "+str(price)+" CZK."+flask.Markup('<br />')
    
    header = ["Card title", "Count", "PPU [CZK]", "Price [CZK]"]
    
    return header, outable, footer, success
