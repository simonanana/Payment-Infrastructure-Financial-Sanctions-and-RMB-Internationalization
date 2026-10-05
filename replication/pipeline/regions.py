"""Region map used for the leave-one-out regional CIPS instrument (copied from the paper notebook)."""
_af = ['DZA','AGO','BEN','BWA','BFA','BDI','CPV','CMR','CAF','TCD','COM','COD',
       'COG','CIV','DJI','EGY','GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN',
       'GNB','KEN','LSO','LBR','LBY','MDG','MWI','MLI','MRT','MUS','MAR','MOZ',
       'NAM','NER','NGA','RWA','STP','SEN','SYC','SLE','SOM','ZAF','SSD','SDN',
       'TZA','TGO','TUN','UGA','ZMB','ZWE']
_as = ['AFG','ARM','AZE','BHR','BGD','BTN','BRN','KHM','CHN','GEO','IND','IDN',
       'IRN','IRQ','ISR','JPN','JOR','KAZ','KWT','KGZ','LAO','LBN','MYS','MDV',
       'MNG','MMR','NPL','OMN','PAK','PHL','QAT','SAU','SGP','KOR','LKA','SYR',
       'TJK','THA','TLS','TUR','TKM','ARE','UZB','VNM','YEM','TWN','HKG','MAC']
_eu = ['ALB','AND','AUT','BLR','BEL','BIH','BGR','HRV','CYP','CZE','DNK','EST',
       'FIN','FRA','DEU','GRC','HUN','ISL','IRL','ITA','LVA','LTU','LUX','MLT',
       'MDA','MNE','NLD','MKD','NOR','POL','PRT','ROU','RUS','SRB','SVK','SVN',
       'ESP','SWE','CHE','UKR','GBR']
_am = ['ARG','BHS','BRB','BLZ','BOL','BRA','CAN','CHL','COL','CRI','CUB','DOM',
       'ECU','SLV','GTM','GUY','HTI','HND','JAM','MEX','NIC','PAN','PRY','PER',
       'SUR','TTO','URY','VEN','USA']
_oc = ['AUS','FJI','NZL','PNG','WSM','SLB','TON','VUT']
REGION_MAP = {}
for _lst, _r in [(_af, 'Africa'), (_as, 'Asia'), (_eu, 'Europe'), (_am, 'Americas'), (_oc, 'Oceania')]:
    for _c in _lst:
        REGION_MAP[_c] = _r
