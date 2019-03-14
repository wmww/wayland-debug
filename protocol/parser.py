#!/usr/bin/python3

import xml.etree.ElementTree as ET
from os import path
import sys

class Protocol:
    def __init__(self, name):
        self.name = name
        self.interfaces = []

class Interface:
    def __init__(self, name):
        self.name = name
        self.messages = []
        self.enums = []

class Message:
    def __init__(self, name, is_event):
        self.name = name
        self.is_event = is_event
        self.args = []

class Arg:
    def __init__(self, name, type_name, specific_type):
        self.name = name
        self.type_name = type_name
        self.specific_type = specific_type

class Enum:
    def __init__(self, name, bitfield):
        self.name = name
        self.bitfield = bitfield

def parse_protocol(xmlfile, enums):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    assert root.tag == 'protocol'
    protocol = Protocol(root.attrib['name'])
    for node in [i for i in root if i.tag == 'interface']:
        interface = Interface(interface.attrib['name'])
        protocol.interfaces.append(interface)
        for node in [e for e in node if e.tag == 'enum']:
            if 'bitfield' in element.attrib and element.attrib['bitfield'] == True:
                local_enums[element.attrib['name']] = [
                    (e.attrib['name'], e.attrib['value'])
                    for e in element
                    if e.tag == 'entry'
                ]
            else:
                local_enums[element.attrib['name']] = {
                    e.attrib['value']: e.attrib['name']
                    for e in element
                    if e.tag == 'entry'
                }
        for element in [e for e in interface if e.tag == 'request' or e.tag == 'event']:
            for i, arg in enumerate([a for a in element if a.tag == 'arg']):
                if 'enum' in arg.attrib:
                    enums[(
                        interface.attrib['name'],
                        element.attrib['name'],
                        i,
                    )] = local_enums[arg.attrib['enum']]

def bad_usage():
    print('usage: ' + sys.argv[0] + ' [source XML] [dest python]')
    exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Wrong number of args')
        bad_usage()
    source = sys.argv[1]
    dest = sys.argv[2]
    if not path.isfile(source):
        print(repr(source) + ' is not a file')
        bad_usage()
    if not source.endswith('.xml'):
        print(repr(source) + ' is not an .xml file')
        bad_usage()
    if not dest.endswith('.py'):
        print(repr(dest) + ' is not a .py file')
        bad_usage()
    enums = {}
    parse_protocol(source, enums)
    print(enums)
