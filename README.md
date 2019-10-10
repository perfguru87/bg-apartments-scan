# Summary
Raw, buggy, dirty but yet working Bulgarian apartments scanner.

Supported websites:
- imot.bg
- ues.bg
- luximmo.com

Features:
- websites scanner
- overall apartment "weight" calculation
- distance calculation
- configurable metrics weights (see config.txt)

Scanned metrics:
- square
- num of rooms
- price
- parkslot / garage
- parks, gardens nearby
- view (mountain, panorama, etc)
- furniture
- fireplace
- luxury
- elevator
- ...

# Example

First, review and edit the metrics weights in the *config.txt*
Second, build a list of apartments to scan and scan it:

## Rank given list of apartments

```
cat > apartments-list.txt << EOD
https://www.imot.bg/pcgi/imot.cgi?act=5&adv=2e156534515892505&slink=4v6yvc&f1=23
https://www.luximmo.com/bulgaria/region-sofia/sofia/luxury-properties-penthouses/luxury-property-22338-penthouse-for-rent-in-sofia.html
https://www.luximmo.com/bulgaria/region-sofia/sofia/luxury-properties-3-bedroom-apartments/luxury-property-28431-3-bedroom-apartment-for-rent-in-sofia.html
http://www.imot.bg/pcgi/imot.cgi?act=5&adv=2e156100140276177&slink=4v1lqy&f1=19
https://ues.bg/en/offers/11175-furnished-apartment-with-parking-place-in-lozenets-for-rent
http://www.imot.bg/pcgi/imot.cgi?act=5&adv=2e155964721281710&slink=4vawmn&f1=12
EOD
python ./bg-apartments-scan.py -l apartments-list.txt -w apartments-list.html -d 'InterContinental Sofia'
```

## Scan results of some pre-filtered results

```
cat > search-results.txt << EOD
https://www.imot.bg/pcgi/imot.cgi?act=3&slink=4vawmn&f1=1
https://www.imot.bg/pcgi/imot.cgi?act=3&slink=4vawmn&f1=2
https://www.imot.bg/pcgi/imot.cgi?act=3&slink=4vawmn&f1=3
https://www.imot.bg/pcgi/imot.cgi?act=3&slink=4vawmn&f1=4
https://www.imot.bg/pcgi/imot.cgi?act=3&slink=4vawmn&f1=5
https://ues.bg/en/loadOffers/rentals?map_quarter_id=1155%2C1153%2C1092%2C1072%2C1168%2C1169%2C1096%2C1151%2C1154%2C1152%2C1118&rent=rentals&category=apartment&category2=&location_id=4451&quarter_id%5B0%5D=&price_from=&price_to=1300&area_from=50&area_to=&type=&lifestyle_category_id=&completion_id=&offer_category_type_id=&heating_id=&parking_id=&closed-complex-header=&project-header=&advanced-search=&page=1
https://ues.bg/en/loadOffers/rentals?map_quarter_id=1155%2C1153%2C1092%2C1072%2C1168%2C1169%2C1096%2C1151%2C1154%2C1152%2C1118&rent=rentals&category=apartment&category2=&location_id=4451&quarter_id%5B0%5D=&price_from=&price_to=1300&area_from=50&area_to=&type=&lifestyle_category_id=&completion_id=&offer_category_type_id=&heating_id=&parking_id=&closed-complex-header=&project-header=&advanced-search=&page=2
EOD
python ./bg-apartments-scan.py -p search-results.txt -w search-results.html -d 'InterContinental Sofia'
```
