#!/usr/bin/python3

import xml.etree.ElementTree as ET
from collections import OrderedDict
from os import path
import sys

class Protocol:
    def __init__(self, name, interfaces):
        assert isinstance(name, str)
        assert isinstance(interfaces, OrderedDict)
        self.name = name
        self.interfaces = interfaces

class Interface:
    def __init__(self, name, messages, enums):
        assert isinstance(name, str)
        assert isinstance(messages, OrderedDict)
        assert isinstance(enums, OrderedDict)
        self.name = name
        self.messages = messages
        self.enums = enums

class Message:
    def __init__(self, name, is_event, args):
        assert isinstance(name, str)
        assert isinstance(is_event, bool)
        assert isinstance(args, OrderedDict)
        self.name = name
        self.is_event = is_event
        self.args = args

class Arg:
    def __init__(self, name, type_, interface, enum):
        assert isinstance(name, str)
        assert isinstance(type_, str)
        assert isinstance(interface, str) or interface == None
        assert isinstance(enum, str) or enum == None
        self.name = name
        self.type = type_
        self.interface = interface
        self.enum = enum

class Enum:
    def __init__(self, name, bitfield, entries):
        assert isinstance(name, str)
        assert isinstance(bitfield, bool)
        assert isinstance(entries, OrderedDict)
        self.name = name
        self.bitfield = bitfield
        self.entries = entries

class Entry:
    def __init__(self, name, value):
        assert isinstance(name, str)
        assert isinstance(value, int)
        self.name = name
        self.value = value

def parse_protocol(xmlfile):
    protocol = ET.parse(xmlfile).getroot()
    assert protocol.tag == 'protocol'
    return Protocol(
        protocol.attrib['name'],
        OrderedDict(
            [(i.name, i) for i in [
                Interface(
                    interface.attrib['name'],
                    OrderedDict(
                        [(i.name, i) for i in [
                            Message(
                                message.attrib['name'],
                                message.tag == 'event',
                                OrderedDict(
                                    [(i.name, i) for i in [
                                        Arg(
                                            arg.attrib['name'],
                                            arg.attrib['type'],
                                            arg.attrib.get('interface', None),
                                            arg.attrib.get('enum', None)
                                        ) for arg in message
                                        if message.tag == 'arg'
                                    ]]
                                )
                            ) for message in interface
                            if message.tag == 'event' or message.tag == 'request'
                        ]]
                    ),
                    OrderedDict(
                        [(i.name, i) for i in [
                            Enum(
                                enum.attrib['name'],
                                bool('bitfield' in enum.attrib and enum.attrib['bitfield']),
                                OrderedDict(
                                    [(i.name, i) for i in [
                                        Entry(
                                            entry.attrib['name'],
                                            int(entry.attrib['value'], 0)
                                        ) for entry in enum
                                        if entry.tag == 'entry'
                                    ]]
                                )
                            ) for enum in interface
                            if enum.tag == 'enum'
                        ]]
                    ),
                ) for interface in protocol
                if interface.tag == 'interface'
            ]]
        )
    )

interfaces = {}
has_parsed = {}

def load(xml_file, out):
    if path.basename(xml_file) in has_parsed:
        out.log('skipped ' + xml_file + ' as ' + path.basename(xml_file) + ' has already been parsed')
        return
    has_parsed[path.basename(xml_file)] = True
    protocol = parse_protocol(xml_file)
    for name, interface in protocol.interfaces.items():
        interfaces[name] = interface
    out.log('Loaded ' + str(len(protocol.interfaces)) + ' interfaces from ' + xml_file)

def discover_xml(p, out):
    if path.isdir(p):
        files = []
        for i in path.os.listdir(p):
            files += discover_xml(path.join(p, i), out)
        return files
    elif path.isfile(p) and p.endswith('.xml'):
        return [p]
    else:
        return []

def load_all(out):
    files = (
        discover_xml('/usr/share/wayland', out) +
        discover_xml('/usr/share/wayland-protocols', out) +
        discover_xml(path.join(path.dirname(sys.argv[0]), 'protocol'), out)
    )
    for f in files:
        load(f, out)

def lookup_enum(interface_name, message_name, arg_index, arg_value):
    pass
