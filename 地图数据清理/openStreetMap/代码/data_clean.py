
# coding: utf-8

# In[97]:

import xml.etree.cElementTree as ET
from collections import defaultdict 
import re
import pprint
from langconv import * 
from pypinyin import pinyin, lazy_pinyin


# In[36]:

OSM_FILE = "shenzhen_china.osm"


# In[73]:

street_type_re = re.compile(r'\b\S+\.?$',re.IGNORECASE)
city_type_re = re.compile(r'\b\S+\.?$',re.IGNORECASE)

street_expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Alley", "Center", "Highway", "Way", "Gardens",'Parts','Path']



def audit_street_type(street_types,street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in street_expected:
            street_types[street_type].add(street_name)
            
    
                        
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def is_city_name(elem):
    return (elem.attrib['k'] == 'addr:city')

def audit_street(osmfile):
    osm_file = open(osmfile,"r")
    street_types = defaultdict(set)
    city_types = defaultdict(set)
    
    for event, elem in ET.iterparse(osm_file, events = ("start",)):
        if elem.tag ==  "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                elif is_city_name(tag):
                    city_types[tag.attrib['v']].add(tag.attrib['v'])
                    
    osm_file.close()
    return street_types ,city_types 


# In[50]:

def tradition2simple(line):
    # 将繁体转换成简体
    #http://blog.csdn.net/thomashtq/article/details/41512359#t2
    line = Converter('zh-hans').convert(line)
    return line


# In[172]:

mapping = { "St": "Street","St.": "Street","ST": "Street","street":"Street","st": "Street",'Jie':'Street',
            'jie':'Street',
            "Rd": "Road","raod":"Road","road": "Road","Lu":'Road',
            "Ln":"Lane",
            "BLVD": "Boulevard",
            "Acenue": "Avenue", "Ave": "Avenue","avenue": "Avenue", "Av": "Avenue",
            "Hwy": "Highway",
            "Blvd": "Boulevard",
            "Ct": "Court",
            "E": "East","S": "South","W": "West","N": "North","S.": "South",
            "NE": "Northeast","NW": "Northwest","SE": "Southeast","SW": "Southwest",
            "Dadao": "DaDao"
            }
def update_name(name, mapping):
    words = name.split()
    for i in range(len(words)):
        if words[i] in mapping:
            words[i] = mapping[words[i]]
    name = " ".join(words)
    return tradition2simple(name)


# In[185]:

city_mapping = {'shenzhen':'深圳','龙岗中心城':'深圳龙岗','Nanshan':'深圳南山','Shenzhen City':'深圳','Shenzhen, China':'深圳','Shenzhen':'深圳'}


# In[198]:

def updata_city_name(city_name):
    return city_mapping[city_name]


# In[194]:

def is_shenzhen_city_name(name):
    return name in city_mapping


# In[219]:

def test():
    st_types,city_types = audit_street(OSM_FILE)
    for st_type, ways in st_types.items():
        for name in ways:
            better_name = update_name(name, mapping)
            print (name, '=>', better_name)
            if name == "鳳攸東街 Fung Yau Street East":
                assert better_name == "凤攸东街 Fung Yau Street East"
            if name == "景田北二街 Jingtian North 2nd St":
                assert better_name == "景田北二街 Jingtian North 2nd Street"
    
    for cy_type,name in city_types.items():
        if is_shenzhen_city_name(cy_type):
            better_name = updata_city_name(cy_type)
            print (name,'=>',better_name)
            if name == 'Shenzhen':
                assert better_name == '深圳'
            if name == 'Nanshan':
                assert better_name == '深圳南山'


# In[220]:

if __name__ == '__main__':
    test()


# In[ ]:



