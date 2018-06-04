
# coding: utf-8

# In[52]:

#!/usr/bin/env python


"""
After auditing is complete the next step is to prepare the data to be inserted into a SQL database.
To do so you will parse the elements in the OSM XML file, transforming them from document format to
tabular format, thus making it possible to write to .csv files.  These csv files can then easily be
imported to a SQL database as tables.

The process for this transformation is as follows:
- Use iterparse to iteratively step through each top level element in the XML
- Shape each element into several data structures using a custom function
- Utilize a schema and validation library to ensure the transformed data is in the correct format
- Write each data structure to the appropriate .csv files

We've already provided the code needed to load the data, perform iterative parsing and write the
output to csv files. Your task is to complete the shape_element function that will transform each
element into the correct format. To make this process easier we've already defined a schema (see
the schema.py file in the last code tab) for the .csv files and the eventual tables. Using the 
cerberus library we can validate the output against this schema to ensure it is correct.

## Shape Element Function
The function should take as input an iterparse Element object and return a dictionary.

### If the element top level tag is "node":
The dictionary returned should have the format {"node": .., "node_tags": ...}

The "node" field should hold a dictionary of the following top level node attributes:
- id
- user
- uid
- version
- lat
- lon
- timestamp
- changeset
All other attributes can be ignored

The "node_tags" field should hold a list of dictionaries, one per secondary tag. Secondary tags are
child tags of node which have the tag name/type: "tag". Each dictionary should have the following
fields from the secondary tag attributes:
- id: the top level node id attribute value
- key: the full tag "k" attribute value if no colon is present or the characters after the colon if one is.
- value: the tag "v" attribute value
- type: either the characters before the colon in the tag "k" value or "regular" if a colon
        is not present.

Additionally,

- if the tag "k" value contains problematic characters, the tag should be ignored
- if the tag "k" value contains a ":" the characters before the ":" should be set as the tag type
  and characters after the ":" should be set as the tag key
- if there are additional ":" in the "k" value they and they should be ignored and kept as part of
  the tag key. For example:

  <tag k="addr:street:name" v="Lincoln"/>
  should be turned into
  {'id': 12345, 'key': 'street:name', 'value': 'Lincoln', 'type': 'addr'}

- If a node has no secondary tags then the "node_tags" field should just contain an empty list.

The final return value for a "node" element should look something like:

{'node': {'id': 757860928,
          'user': 'uboot',
          'uid': 26299,
       'version': '2',
          'lat': 41.9747374,
          'lon': -87.6920102,
          'timestamp': '2010-07-22T16:16:51Z',
      'changeset': 5288876},
 'node_tags': [{'id': 757860928,
                'key': 'amenity',
                'value': 'fast_food',
                'type': 'regular'},
               {'id': 757860928,
                'key': 'cuisine',
                'value': 'sausage',
                'type': 'regular'},
               {'id': 757860928,
                'key': 'name',
                'value': "Shelly's Tasty Freeze",
                'type': 'regular'}]}

### If the element top level tag is "way":
The dictionary should have the format {"way": ..., "way_tags": ..., "way_nodes": ...}

The "way" field should hold a dictionary of the following top level way attributes:
- id
-  user
- uid
- version
- timestamp
- changeset

All other attributes can be ignored

The "way_tags" field should again hold a list of dictionaries, following the exact same rules as
for "node_tags".

Additionally, the dictionary should have a field "way_nodes". "way_nodes" should hold a list of
dictionaries, one for each nd child tag.  Each dictionary should have the fields:
- id: the top level element (way) id
- node_id: the ref attribute value of the nd tag
- position: the index starting at 0 of the nd tag i.e. what order the nd tag appears within
            the way element

The final return value for a "way" element should look something like:

{'way': {'id': 209809850,
         'user': 'chicago-buildings',
         'uid': 674454,
         'version': '1',
         'timestamp': '2013-03-13T15:58:04Z',
         'changeset': 15353317},
 'way_nodes': [{'id': 209809850, 'node_id': 2199822281, 'position': 0},
               {'id': 209809850, 'node_id': 2199822390, 'position': 1},
               {'id': 209809850, 'node_id': 2199822392, 'position': 2},
               {'id': 209809850, 'node_id': 2199822369, 'position': 3},
               {'id': 209809850, 'node_id': 2199822370, 'position': 4},
               {'id': 209809850, 'node_id': 2199822284, 'position': 5},
               {'id': 209809850, 'node_id': 2199822281, 'position': 6}],
 'way_tags': [{'id': 209809850,
               'key': 'housenumber',
               'type': 'addr',
               'value': '1412'},
              {'id': 209809850,
               'key': 'street',
               'type': 'addr',
               'value': 'West Lexington St.'},
              {'id': 209809850,
               'key': 'street:name',
               'type': 'addr',
               'value': 'Lexington'},
              {'id': '209809850',
               'key': 'street:prefix',
               'type': 'addr',
               'value': 'West'},
              {'id': 209809850,
               'key': 'street:type',
               'type': 'addr',
               'value': 'Street'},
              {'id': 209809850,
               'key': 'building',
               'type': 'regular',
               'value': 'yes'},
              {'id': 209809850,
               'key': 'levels',
               'type': 'building',
               'value': '1'},
              {'id': 209809850,
               'key': 'building_id',
               'type': 'chicago',
               'value': '366409'}]}
"""

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

OSM_PATH = "shenzhen_china.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

mapping = { "St": "Street","St.": "Street","ST": "Street","street":"Street","st": "Street",'Jie':'Street',
            'jie':'Street',
            "Rd": "Road","raod":"Road","road": "Road","Lu":'Road',
            "Ln":"Lane",
            "BLVD": "Boulevard",
            "Acenue": "Avenue", "Ave": "Avenue","avenue": "Avenue", "Av": "Avenue",
            "Hwy": "Highway",
            "Blvd": "Boulevard",
            "Ct": "Court",
            "E": "East","S": "South","W": "West","N": "North",
            "NE": "Northeast","NW": "Northwest","SE": "Southeast","SW": "Southwest",
            "Dadao": "DaDao",
            }

city_mapping = {'shenzhen':'深圳','龙岗中心城':'深圳龙岗','Nanshan':'深圳南山','Shenzhen City':'深圳','Shenzhen, China':'深圳','Shenzhen':'深圳'}



    
# OSM2CSV


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    id_set = set()

    if element.tag == 'node':
        for Key in NODE_FIELDS:
            node_attribs[Key] = element.get(Key)

        for row in element.iterfind('tag'):
            if PROBLEMCHARS.search(row.get('k')):
                continue
            else:
                node_tag = {}
                node_tag['id'] = node_attribs['id']

                # clean the data
                if row.get('k') == 'addr:city':
                    node_tag['value'] = updata_city_name(row.get('v'))
                elif row.get('k') == 'addr:street':
                    node_tag['value'] = update_name(row.get('v'))
                else:
                    node_tag['value'] = row.get('v')

                if LOWER_COLON.search(row.get('k')):
                    node_tag['key'] = row.get('k').split(':', 1)[1]
                    node_tag['type'] = row.get('k').split(':', 1)[0]
                else:
                    node_tag['key'] = row.get('k')
                    node_tag['type'] = 'regular'
                tags.append(node_tag)


    elif element.tag == 'way':
        for Key in WAY_FIELDS:
            way_attribs[Key] = element.get(Key)

        index = 0
        for row in element.iterfind('nd'):
            way_node = {}
            way_node['id'] = way_attribs['id']
            way_node['node_id'] = int(row.get('ref'))
            way_node['position'] = index
            way_nodes.append(way_node)
            index += 1

        for row in element.iterfind('tag'):
            if PROBLEMCHARS.search(row.get('k')):
                continue
            else:
                way_tag = {}
                way_tag['id'] = way_attribs['id']

                # clean the data
                if row.get('k') == 'addr:city':
                    way_tag['value'] = updata_city_name(row.get('v'))
                elif row.get('k') == 'addr:street':
                    way_tag['value'] = update_name(row.get('v'))
                else:
                    way_tag['value'] = row.get('v')

                if LOWER_COLON.search(row.get('k')):
                    way_tag['key'] = row.get('k').split(':', 1)[1]
                    way_tag['type'] = row.get('k').split(':', 1)[0]
                else:
                    way_tag['type'] = 'regular'
                    way_tag['key'] = row.get('k')
                tags.append(way_tag)

    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}



def update_name(name, mapping = city_mapping):
    words = name.split()
    for i in range(len(words)):
        if words[i] in mapping:
            words[i] = mapping[words[i]]
    name = " ".join(words)
    return name

def tradition2simple(line):
    # 将繁体转换成简体
    #http://blog.csdn.net/thomashtq/article/details/41512359#t2
    line = Converter('zh-hans').convert(line)
    return line


def is_shenzhen_city_name(name):
    return name in city_mapping


def updata_city_name(city_name):
    if is_shenzhen_city_name(city_name):
        return city_mapping[city_name]
    else:
        return ''        

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()







# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file,             codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,             codecs.open(WAYS_PATH, 'w') as ways_file,             codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,             codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = csv.DictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = csv.DictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = csv.DictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = csv.DictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = csv.DictWriter(way_tags_file, WAY_TAGS_FIELDS)
        
        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])



if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)


# In[ ]:

SELECT COUNT(*) as num FROM nodes_tags WHERE value = 'hospital'

