#!/usr/bin/env python
# -*- coding: cp1251 -*-

from __future__ import print_function

import os
import time
import argparse
import logging
import re
import tempfile
import shutil
import hashlib
import configparser
from geopy import distance, geocoders
from geopy.exc import GeocoderTimedOut, GeocoderQuotaExceeded

try:
    # For Python 3.0 and later
    from urllib.request import urlopen, HTTPError
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, HTTPError

reInt = [re.compile(r'[\s>]*(\d+)[\s<]*')]
reSqm = [re.compile(r'Квадратура: (\d+) кв.м'),
         re.compile(r'(\d+) sq.m')]
reRooms = [re.compile(r'(\d+)-СТАЕН')]
reRoomsMany = [re.compile(r'МНОГОСТАЕН', re.IGNORECASE)]
reMountain = [re.compile(r'(view.*?mountain)', re.IGNORECASE),
              re.compile(r'(mountain.*?view)', re.IGNORECASE)]
reBedrooms = [re.compile(r'(\d+) Bedrooms', re.IGNORECASE),
              re.compile(r'(\d+)-bedroom', re.IGNORECASE)]
reElevator = [re.compile(r'[ >,.](Асансьор)[ <,.]', re.IGNORECASE),
              re.compile(r'[ >,](lift)[ <,.]', re.IGNORECASE),
              re.compile(r'[ >,](elevator)[ <,.]', re.IGNORECASE)]
reDistrict = [re.compile(r'град София, (\S+)'),
              re.compile(r'Bulgaria, Sofia, ([\S ]+?), '),
              re.compile(r'/ DISTRICT (.*?)[</]', re.IGNORECASE),
              re.compile(r'Location: (\S+\s+)district', re.IGNORECASE)]
reCity = [re.compile(r'"град (\S*)"')]
reSubway = [re.compile(r'(метростанция)', re.IGNORECASE),
            re.compile(r'(metrostantsiya)', re.IGNORECASE),
            re.compile(r'[ >,.](metro)[ <,.]', re.IGNORECASE),
            re.compile(r'(subway)', re.IGNORECASE),
            re.compile(r'(Metrostatio)', re.IGNORECASE)]
reStreet = [re.compile(r'[ >]?б*ул\.\s+(.*?)[<,]')]
reStreetFull = [re.compile(r'[ >]?(б*ул\..*?)[<,]')]
rePrice = [re.compile(r'([\d ]*\d+) EUR<'),
           re.compile(r'&euro; ([\d ]*\d+)'),
           re.compile(r'curr_conv\S*\s*([\d ]*\d+)')]
rePriceWoVat = [re.compile(r'([\d ]*\d+) without VAT')]
reFloor = [re.compile(r'Етаж: (\d+)-\Sи от \d+'),
           re.compile(r'Floor: (\d+)'),
           re.compile(r'Floors: (\d+)'),
           re.compile(r'(\d+)\S*\s+floor', re.IGNORECASE),
           re.compile(r'(\d+)/\d+ floor', re.IGNORECASE)]
reFloorMax = [re.compile(r'Етаж: \d+-\Sи от (\d+)'),
              re.compile(r'Floor: \d+ / (\d+)'),
              re.compile(r'\d+/(\d+) floor', re.IGNORECASE),
              re.compile(r'(\d+)-storey')]
rePark = [re.compile(r'[ ,>](park)[ ,.<]', re.IGNORECASE),
          re.compile(r'[ ,>](парк)[ ,.<]', re.IGNORECASE)]
reGarden = [re.compile(r'[ ,>](garden)[ ,.<]',  re.IGNORECASE)]
reGym = [re.compile(r'[ ,>](gym)[ ,.<]',  re.IGNORECASE)]
reLocation = [re.compile(r'good\s+(location)',  re.IGNORECASE),
              re.compile(r'wonderful\s+(location)', re.IGNORECASE),
              re.compile(r'great\s+(location)', re.IGNORECASE),
              re.compile(r'top\s+(location)', re.IGNORECASE),
              re.compile(r'excellent\s+(location)', re.IGNORECASE),
              re.compile(r'strategic\s+(location)', re.IGNORECASE),
              re.compile(r'prestigious\s+(location)', re.IGNORECASE),
              re.compile(r'communicative\s+(location)', re.IGNORECASE),
              re.compile(r'(the location of the property)', re.IGNORECASE),
              re.compile(r'(the location is)', re.IGNORECASE),
              re.compile(r'(is its location)', re.IGNORECASE),
              re.compile(r'(central location)', re.IGNORECASE),
              re.compile(r'(the location has)', re.IGNORECASE),
              re.compile(r'(топ локацция)', re.IGNORECASE),
              re.compile(r'unique\s+(location)', re.IGNORECASE)]
reMall = [re.compile(r'[ ,.>](mall)[ ,.<]',  re.IGNORECASE)]
reSupermarketl = [re.compile(r'[ ,.>](supermarket)[ ,.<]',  re.IGNORECASE)]
reTransport = [re.compile(r'[ ,>](transport)[ ,.<]',  re.IGNORECASE)]
reLeisure = [re.compile(r'[ ,>](leisure)[ ,.<]',  re.IGNORECASE)]
rePool = [re.compile(r'[ ,>](pool)[ ,.<]',  re.IGNORECASE),
          re.compile(r'[ ,>](swimming)[ ,.<]',  re.IGNORECASE)]
reCalm = [re.compile(r'[ ,>](calm)', re.IGNORECASE),
          re.compile(r'[ ,>](qiuet)', re.IGNORECASE)]
reUnique = [re.compile(r'[ ,>](unique)', re.IGNORECASE)]
reLuxury = [re.compile(r'[ ,>](luxury)', re.IGNORECASE)]
rePrestigious = [re.compile(r'[ ,>](prestigious)', re.IGNORECASE)]
reRenovated = [re.compile(r'[ ,>](renovated)', re.IGNORECASE)]
reFireplace = [re.compile(r'[ ,>](fireplace)', re.IGNORECASE)]
reRestaurants = [re.compile(r'[ ,>](restaurant)', re.IGNORECASE)]
reApartmentLink = [re.compile(r'//(www.imot.bg/pcgi/imot.cgi\?act=5&adv=\S+?&slink=\S+?)"'),
                   re.compile(r'(https://ues.bg/en/offers/\S+?)["<\s]'),
                   re.compile(r'<a class="offer-link"\s+href="(https://www.luximmo.com/\S+.html)">')]
reImg = [re.compile(r'src=\"(//imot.focus.bg/photosimotbg/\S+small\S+?.pic)'),
         re.compile(r'url\(\'(https://image.ues.bg/estates/watermark/\S+?.jpg)\'', re.IGNORECASE),
         re.compile(r'"image":"(https:\\/\\/static.luximo.ru\\/property-images\\/\S+?.jpg)', re.IGNORECASE)]
reStopWord = [re.compile(r"Contact us"),
              re.compile(r"За контакти:<")]

reAZ = re.compile("[^a-zA-Z0-9]")

CACHE_DIR = os.path.join(tempfile.gettempdir(), 'aparts-scanner')

VIEWS = {"View": 1, "Panorama": 2, "Rock View": 3}


class Apartment:
    def __init__(self, id, url):
        self.id = id
        self.url = url
        self.score = 0
        self.district = ""
        self.country = "България"
        self.city = "Sofia"
        self.street = ""
        self.street_full = ""
        self.geolocation = None

        self.subway = 0
        self.price = 0
        self.price_wo_vat = 0
        self.rooms = 0
        self.bedrooms = 0
        self.sqm = 0
        self.location = 0
        self.mall = 0
        self.supermarket = 0
        self.transport = 0
        self.leisure = 0
        self.pool = 0
        self.calm = 0
        self.fireplace = 0
        self.unique = 0
        self.luxury = 0
        self.prestigious = 0
        self.renovated = 0
        self.gym = 0
        self.restaurants = 0
        self.floor = 0
        self.floor_max = 0
        self.elevator = 0
        self.internet = 0
        self.luxe = 0
        self.view = 0
        self.balcony = 0
        self.park = 0
        self.garden = 0
        self.garage = 0
        self.parkslot = 0
        self.furniture = 0
        self.cozy = 0
        self.distance = 0

        self.images_list = []
        self.images_set = set()

    @staticmethod
    def toHtmlHeader():
        return "<table id='apartments' class='countries-tiny'><thead><tr>" + \
               "<th>#</th><th>Score</th><th>District</th><th>Street</th><th>Price (EUR)</th>" + \
               "<th>Rooms</th><th>Sq.m</th><th>Floor</th><th>Floor (max)</th>" + \
               "<th>Elevator</th><th>Internet</th><th>View</th><th>Balcony</th>" + \
               "<th>Environment</th><th>Parking</th>" + \
               "<th>Furnt.</th><th>Subway</th><th>Dist (KM)</th>" + \
               "<th>Images</th>" + \
               "<th>Link</th>" + \
               "</tr><tbody>"

    @staticmethod
    def toHtmlFooter():
        return "</tbody></table>"

    def toHtml(self):
        img = "".join("<img class='imgpreview' src='%s'>" % i for i in self.images_list[0:5])

        facilities = []
        if self.park:
            facilities.append("park")
        if self.pool:
            facilities.append("pool")
        if self.gym:
            facilities.append("gym")
        if self.restaurants:
            facilities.append("restaurants")
        if self.calm:
            facilities.append("calm")
        if self.fireplace:
            facilities.append("fireplace")
        if self.unique:
            facilities.append("unique")
        if self.luxury:
            facilities.append("luxury")
        if self.luxe:
            facilities.append("luxe")
        if self.prestigious:
            facilities.append("prestigious")
        if self.renovated:
            facilities.append("renovated")
        if self.location:
            facilities.append("location")
        if self.mall:
            facilities.append("mall")
        if self.supermarket:
            facilities.append("supermarket")
        if self.transport:
            facilities.append("transport")
        if self.leisure:
            facilities.append("leisure")

        try:
            link_name = self.url.split("/")[2]
        except RuntimeException as e:
            link_name = "link"

        return (("<tr class='grid' id='%d'><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td>"
                 "<td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                 "<td>%s</td><td>%s</td><td>%s</td>"
                 "<td>%s</td><td>%s</td><td>%s</td>"
                 "<td>%s</td><td>%s</td><td>%.1f</td>"
                 "<td>%s</td>"
                 "<td><a target=_blank href='%s'>%s</a></td></tr>") %
                (self.id, self.id, int(self.score), self.district, self.street, self.price,
                 self.rooms, self.sqm, self.floor, self.floor_max,
                 "Elevator" if self.elevator else "-",
                 "Inet" if self.internet else "-",
                 self.view if self.view else "-",
                 "Balcony" if self.balcony else "-",
                 ", ".join(facilities) if facilities else "-",
                 "Garage" if self.garage else ("Parkslot" if self.parkslot else "-"),
                 "Cozy" if self.cozy else ("Furnit" if self.furniture else "-"),
                 "Metro" if self.subway else "-",
                 self.distance, img, self.url, link_name))

    def getBigImages(self):
        images = "".join("<img class=\"imgbig\" src=\"%s\">" % i for i in self.images_list)
        if "imot." in images:
            images = images.replace("/small/", "/big/")
            images = images.replace("/med/", "/big/")
        return images

    def parseImages(self, line):
        for r in reImg:
            for link in r.findall(line):
                if link in self.images_set:
                    continue
                self.images_set.add(link)
                if not link.startswith("http"):
                    link = "http:" + link
                if "imot" in link:
                    link = link.replace('small', 'med')
                if "luximo" in link or "luximmo" in link:
                    link = link.replace('\\', '')
                self.images_list.append(link)
                logging.debug("    img: %s" % link)

    def parse(self, property, regexp, line, val=None, overwrite=False):
        if property and not overwrite and self.__dict__[property] and self.__dict__[property] != "-":
            return False

        line = line.strip()

        if type(regexp) == str:
            if regexp.lower() not in line.lower():
                return False
            if property:
                self.__dict__[property] = 1 if val is None else val
                logging.debug("  found: %s = %s (%s)" % (property, str(self.__dict__[property]), line))
            return True
        else:
            for r in regexp:
                m = r.search(line)
                if m:
                    if property:
                        self.__dict__[property] = m.group(1) if val is None else val
                        logging.debug("  found: %s = %s (%s)" % (property, str(self.__dict__[property]), line))
                    return True
        return False

    def getHtml(self):
        p = os.path.join(CACHE_DIR, reAZ.sub('_', self.url))
        if os.path.exists(p):
            f = open(p)
            data = f.readlines()
            logging.info("from cache: %s" % self.url)
            f.close()
        else:
            logging.info("fetching url: %s" % self.url)
            try:
                response = url_open(self.url)
            except HTTPError as e:
                return ""
            data = response.read()
            f = open(p, 'w')
            f.write(data)
            f.close()
            data = data.split('\n')
        return data

    def scan(self):
        data = self.getHtml()

        parse_next = False

        for line in data:
            try:
                line = line.decode('utf-8').encode('cp1251', 'ignore')
            except UnicodeDecodeError as e:
                pass
            self.parse('sqm', reSqm, line)
            self.parse('rooms', reRooms, line)
            self.parse('rooms', reRoomsMany, line, 5)
            self.parse('bedrooms', reBedrooms, line)
            self.parse('elevator', reElevator, line, 1)
            self.parse('internet', 'Интернет връзка', line)
            self.parse('internet', 'internet', line)
            self.parse('luxe', 'Лукс</div>', line)
            self.parse('garage', 'гараж</div>', line)
            self.parse('garage', 'гараж в цената', line)
            self.parse('garage', 'garage', line)
            self.parse('parkslot', 'паркомясто</div>', line)
            self.parse('parkslot', 'parking', line)
            self.parse('parkslot', 'no parking', line, 0, overwrite=True)
            self.parse('parkslot', 'underground parking', line, 1, overwrite=True)
            self.parse('park', 'park environment', line, 1)
            self.parse('park', rePark, line, 1)
            self.parse('garden', reGarden, line, 1)
            self.parse('district', reDistrict, line)
            self.parse('street', reStreet, line)
            self.parse('street_full', reStreetFull, line)
            self.parse('subway', reSubway, line, 1)
            self.parse('city', reCity, line, overwrite=True)
            self.parse('price', rePrice, line, overwrite=True)
            self.parse('price_wo_vat', rePriceWoVat, line)
            self.parse('floor', reFloor, line)
            self.parse('floor_max', reFloorMax, line)
            self.parse('furniture', ' Обзаведен</div>', line)
            self.parse('furniture', ' with furniture', line)
            self.parse('furniture', 'partly furnished', line, 0, overwrite=True)
            self.parse('furniture', 'fully furnished', line, 1, overwrite=True)
            self.parse('cozy', 'cozy', line)
            self.parse('cozy', 'coziness', line)
            self.parse('pool', rePool, line, 1)
            self.parse('calm', reCalm, line, 1)
            self.parse('fireplace', reFireplace, line, 1)
            self.parse('unique', reFireplace, line, 1)
            self.parse('luxury', reLuxury, line, 1)
            self.parse('prestigious', rePrestigious, line, 1)
            self.parse('renovated', reRenovated, line, 1)
            self.parse('gym', reGym, line, 1)
            self.parse('restaurants', reRestaurants, line, 1)
            self.parse('location', reLocation, line, 1)
            self.parse('location', 'Search by basic location', line, 0, overwrite=True)
            self.parse('mall', reMall, line, 1)
            self.parse('transport', reTransport, line, 1)
            self.parse('leisure', reLeisure, line, 1)
            self.parse('balcony', ' тераса', line)
            self.parse('balcony', ' терасите', line)
            self.parse('balcony', ' балкон', line)
            self.parse('balcony', 'terrace', line)
            self.parse('balcony', 'balcony', line)
            self.parse('view', ' гледка', line, 'View')
            self.parse('view', ' гледки', line, 'View')
            self.parse('view', 'гледка към Витоша', line, 'Rock View', overwrite=True)
            self.parse('view', ' планината', line, 'Rock View', overwrite=True)
            self.parse('view', ' околностите', line, 'Panorama', overwrite=True)
            self.parse('view', ' панорама', line, 'Panorama', overwrite=True)
            self.parse('view', ' панорамни', line, 'Panorama', overwrite=True)
            self.parse('view', 'great view', line, 'View')
            self.parse('view', 'amazing view', line, 'View')
            self.parse('view', 'nice view', line, 'View')
            self.parse('view', 'beautiful views', line, 'View')
            self.parse('view', 'panoramic', line, 'Panorama', overwrite=True)
            self.parse('view', 'panoramik', line, 'Panorama', overwrite=True)
            self.parse('view', reMountain, line, 'Rock View', overwrite=True)

            self.parseImages(line)

            if "luximmo.com" in self.url:
                if parse_next == "price":
                    try:
                        self.price = int(line.replace("\"", "").replace(" ", ""))
                    except ValueError as e:
                        pass
                    parse_next = ""

                elif parse_next == "floor":
                    self.parse('floor', reInt, line)
                    if self.floor:
                        parse_next = ""

                elif parse_next == "num_of_floors":
                    self.parse('floor_max', reInt, line)
                    if self.floor_max:
                        parse_next = ""

                if "curr_conv" in line:
                    parse_next = "price"
                elif "Floor:" in line:
                    parse_next = "floor"
                elif "Number of floors:" in line:
                    parse_next = "num_of_floors"

            if self.parse(None, reStopWord, line):
                break

        for s in (" в ", " до "):
            self.street = self.street.split(s)[0]
            self.street_full = self.street_full.split(s)[0]
        for s in ("'", "&#39;", "&quot;"):
            self.street = self.street.replace(s, " ")
            self.street_full = self.street_full.replace(s, " ")
        for s in (" ",):
            self.price = int(str(self.price).replace(s, ""))
            self.price_wo_vat = int(str(self.price_wo_vat).replace(s, ""))

        if not self.rooms and self.bedrooms:
            self.rooms = int(self.bedrooms) + 1
        if self.price_wo_vat:
            self.price = float(self.price_wo_vat) * 1.20

        if "ues.bg" in self.url:
            self.luxe = 1

    def getAddressesUtf8(self):
        if not self.city:
            return None

        # it glitches... try "България София ул. Тинтява" vs "България София Тинтява"
        addresses = [self.country + " " + self.city + " " + self.district + " " + self.street,
                     self.country + " " + self.city[:-1] + " " + self.district + " " + self.street,
                     self.country + " " + self.city + " " + self.district + " " + self.street.split(".")[0],
                     self.country + " " + self.city + " " + self.district + " " + self.street.split(" и ")[0],
                     self.country + " " + self.city + " " + self.district + " " + self.street.split(" вх ")[0],
                     self.country + " " + self.city + " " + self.district + " " + self.street_full]

        return [(a, a.decode('cp1251').encode('utf8')) for a in addresses]

    def calcDistance(self, addr_str, addr_unicode, geolocator, location, location_str):
        p = os.path.join(CACHE_DIR, hashlib.md5(addr_unicode + " " + location_str).hexdigest())
        if os.path.exists(p):
            f = open(p)
            km = float(f.read())
            f.close()

            logging.debug("  distance from cache: %.1f (%s)" % (km, addr_str))
        else:
            logging.debug("  fetching distance...")
            try:
                _, self.geolocation = geolocator.geocode(addr_unicode, language="bg-BG", timeout=15)
                km = float(distance.distance(location, self.geolocation).km)
                logging.debug("  distance fetched: %.1f (%s)" % (km, addr_str))
            except GeocoderTimedOut as e:
                logging.debug("  can't determine geolocation of: %s - TIMED OUT" % addr_str)
                return 0.0
            except GeocoderQuotaExceeded as e:
                logging.debug("  geocoder quota exceeded: %s" % addr_str)
                time.sleep(2.0)
                return 0.0
            except TypeError as e:
                logging.debug("  can't determine geolocation of: %s" % addr_str)
                km = 0.0

            f = open(p, 'w')
            f.write(str(km))
            f.close()

        return km

    def initDistance(self, geolocator, location, location_str):
        addresses = self.getAddressesUtf8()
        if not addresses:
            return

        best = None
        for (a_str, a_unicode) in addresses:
            km = self.calcDistance(a_str, a_unicode, geolocator, location, location_str)
            if km > 0.0 and (best is None or km < best):
                best = km
                self.distance = km

        if self.distance == 0:
            logging.warning("  can't determine location for:\n  %s" % "\n  ".join([a[0] for a in addresses]))
        else:
            logging.debug("  distance: %.1f km" % self.distance)

    def calcScore(self, weights):
        self.score = 0

        for attr in ('price', 'rooms', 'sqm', 'floor', 'elevator', 'internet',
                     'location', 'mall',
                     'luxe', 'view', 'calm', 'fireplace', 'unique', 'luxury', 'leisure',
                     'pool', 'restaurants', 'supermarket', 'balcony', 'park', 'garden', 'garage', 'parkslot',
                     'furniture', 'cozy', 'subway', 'distance'):
            if self.__dict__[attr]:
                v = self.__dict__[attr]

                if attr == "view":
                    v = VIEWS.get(v, 0)
                elif attr == "distance":
                    v = float(v) if v else 4.0
                elif attr == "price" and not v:
                    v = 1000.0
                elif attr == "floor" and not v:
                    v = 2
                else:
                    v = float(v)

                s = v * float(weights.get(attr, 0))
                logging.debug("  subscore for '%s': %.1f" % (attr, s))
                self.score += s
        logging.debug("  SCORE: %.1f" % self.score)


class Config:
    def __init__(self, config_file):

        self.weights = {}

        config = configparser.ConfigParser()
        config.read(config_file)
        self.weights.update(config['WEIGHTS'])


HEADER = """
<html lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=cp1251">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Filter types | TableFilter</title>

    <link rel="stylesheet" href="https://www.tablefilter.com/assets/css/bootstrap.min.css">
    <link href="https://www.tablefilter.com/assets/css/bootstrap-theme.min.css" rel="stylesheet">
    <link href="https://www.tablefilter.com/assets/css/theme.css" rel="stylesheet">
    <link href="https://www.tablefilter.com/tablefilter/style/tablefilter.css" rel="stylesheet">
    <script src="https://www.tablefilter.com/tablefilter/tablefilter.js"></script>
  </head>
<body>

<script src="https://code.jquery.com/jquery-3.4.1.min.js" integrity="sha256-CSXorXvZcTkaix6Yvo6HppcZGetbYMGWSFlBw8HfCJo="
  crossorigin="anonymous"></script>

<style>
body { padding: 5px; }
table.TF th, table.TF tr.fltrow td { background-color: #d8d8d8; border: 1px solid #fff; }
table.TF th, table.TF td {padding: 1px 2px; font-size: 12px; }
table.TF td img.imgpreview { padding: 1px; float: left; height: 60px; }
table.TF tr.details td { background-color: #333; }
table.TF td img.imgbig { padding: 0px; border: 1px solid #fff; float: left; height: 260px; }
table.TF td { border: 1px solid #fff; }
table.TF tr:nth-child(even) { background: #f0f0f0; }
table.TF tr:nth-child(odd) { background: #f8f8f8; }
table.TF tr:nth-child(even).selected { background: #f8f0e0; }
table.TF tr:nth-child(odd).selected { background: #fff7e5; }
</style>
"""

FOOTER = """
<script data-config>

function hide_all_details() {
    console.log("hide all details");
    $(".details").remove();
}

function init_table() {
    var filtersConfig = {
        base_path: 'https://www.tablefilter.com/tablefilter/',
        col_0: 'none',
        col_1: 'none',
        col_2: 'multiple',
        col_3: 'multiple',
        col_4: 'none',
        col_5: 'multiple',
        col_6: 'none',
        col_7: 'multiple',
        col_8: 'multiple',
        col_9: 'multiple',
        col_10: 'multiple',
        col_11: 'multiple',
        col_12: 'multiple',
        col_14: 'multiple',
        col_15: 'multiple',
        col_16: 'multiple',
        col_17: 'multiple',
        col_18: 'none',
        col_19: 'none',
        col_widths: [
            '30px', '40px', '80px', '100px',
            '45px', '45px', '45px', '50px',
            '50px', '60px', '60px', '60px',
            '60px', '100px', '60px', '50px',
            '60px', '50px', '460px', '100px'
        ],
        col_types: [
            'number',
            'number',
            'string',
            'string',
            'number',
            'number',
            'number',
            'number',
            'number',
            'string',
            'string',
            'string',
            'string',
            'string',
            'string',
            'string',
            'string',
            'string',
            'number',
        ],
        extensions: [{ name: 'sort' }]
    };
    var tf = new TableFilter('apartments', filtersConfig);

    tf.onBeforeFilter = function(o) { hide_all_details(); }
    tf.onBeforeSort = function(o, colIndex) { hide_all_details(); }
    tf.init();
}
init_table();

$(document).ready(function() {

    $('img.imgpreview').click(function(){
        $curRow = $(this).closest('tr');
        $curId = $curRow.attr('id');
        var details = $curId + "_details";

        if ($("#" + details).length) {
            $("#" + details).remove();
        } else {
            $curRow.after('<tr class="details" id="' + details + '"><td colspan="21">' + images[$curId] + '</td></tr>')
        }
    });

    $('tr.fltrow th').click(function(){ hide_all_details(); });
    $('tr.fltrow td').click(function(){ hide_all_details(); });
    $('tr.grid').click(function(){ $(this).toggleClass("selected"); });
});

</script>
</body>
"""


def parse_args():
    description = ""

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', action='count', help='Enable verbose mode (use -vv for max verbosity)')

    parser.add_argument('-l', '--links', help="file with imot.bg apartments links")
    parser.add_argument('-p', '--pages', help="file with imot.bg apartments search pages links")
    parser.add_argument('-w', '--html', help="write to given HTML file")
    parser.add_argument('-r', '--clear-cache', action="store_true", help="clear apartments HTML caches")
    parser.add_argument('-d', '--distance', help="analyze distance to given location")
    parser.add_argument('-c', '--config', default='config.txt', help="configuration file")
    parser.add_argument('-n', '--head', default=None, type=int, help="take only HEAD first urls from the file")

    return parser.parse_args()


def url_open(url):
    for retry in range(0, 5):
        try:
            return urlopen(url)
        except HTTPError as e:
            logging.warning("can't fetch: %s - %s" % (url, str(e)))
            time.sleep(1.0)
    raise


def find_links(args):
    links = []

    if args.links:
        for l in open(args.links).readlines()[0:args.head]:
            links.append(l.strip())

    if args.pages:
        seen = set()

        for l in open(args.pages).readlines()[0:args.head]:
            url = l.strip()
            if not url.startswith("http"):
                continue

            logging.info("open apartments search page list: %s" % url)
            data = url_open(url)
            for l in data.readlines():
                for r in reApartmentLink:
                    m = r.search(l)
                    if not m:
                        continue
                    link = m.group(1)
                    if link in seen:
                        continue
                    seen.add(link)
                    logging.debug("  found apartment link: %s" % link)
                    if not link.startswith("http"):
                        link = "http://" + link
                    links.append(link)

    return links


def main():
    args = parse_args()

    fmt = '%(asctime)-15s %(levelname)7s %(message)s'
    if args.verbose >= 2:
        logging.basicConfig(format=fmt, level=logging.DEBUG, filename=None)
    else:
        logging.basicConfig(format=fmt, level=logging.INFO if args.verbose else logging.ERROR, filename=None)

    if args.clear_cache:
        shutil.rmtree(CACHE_DIR)
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    if args.distance:
        geolocator = geocoders.Nominatim(user_agent="aparts-scanner-2")
        try:
            _, location = geolocator.geocode(args.distance, language="bg-BG")
        except GeocoderQuotaExceeded as e:
            logging.warning(str(e))
            logging.warning("distance calculation will be disabled")
            args.distance = False

    config = Config(args.config)

    apartments = []

    n = 1
    for l in find_links(args):
        a = Apartment(n, l.strip())
        a.scan()
        if args.distance:
            a.initDistance(geolocator, location, args.distance)
        a.calcScore(config.weights)
        apartments.append(a)
        n += 1

    html = HEADER
    html += Apartment.toHtmlHeader()

    apartments = sorted(apartments, key=lambda x: x.score, reverse=True)
    for a in apartments:
        html += a.toHtml()

    html += Apartment.toHtmlFooter()

    html += "<script>var images = {"
    html += ", ".join(["\"%d\": '%s'" % (a.id, a.getBigImages()) for a in apartments])
    html += "};</script>"

    html += FOOTER

    if args.html:
        f = open(args.html, 'w')
        f.write(html)
        f.close
    else:
        print(html)


if __name__ == '__main__':
    main()
