#!/usr/bin/python3

import xml.etree.ElementTree as ET
from collections import OrderedDict
from os import path
import sys
import time

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
                                        if arg.tag == 'arg'
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

def load(xml_file, out):
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
    start = time.perf_counter()
    shipped_protocols_path = path.join(path.dirname(path.realpath(sys.argv[0])), 'protocol')
    if not path.isdir(shipped_protocols_path):
        out.warn(
            'Could not fined protocols shipped with Wayland Debug at ' + shipped_protocols_path +
            ', will look for protocols on system and fall back to simpler output when not found')
    files = (
        discover_xml('/usr/share/wayland', out) +
        discover_xml('/usr/share/wayland-protocols', out) +
        discover_xml(shipped_protocols_path, out)
    )
    have_seen = {}
    unique = []
    for xml_file in files:
        basename = path.basename(xml_file)
        if basename not in have_seen:
            have_seen[basename] = True
            unique.append(xml_file)
    for f in unique:
        load(f, out)
    end = time.perf_counter()
    out.log('Took ' + str(int((end - start) * 1000)) + 'ms to load ' + str(len(unique)) + ' protocol files')

def get_arg(interface_name, message_name, arg_index):
    if (interface_name, message_name) == ('wl_registry', 'bind'):
        return None # the protocol doesn't match the detected messages
    if not interface_name in interfaces:
        return []
    interface = interfaces[interface_name]
    if not message_name in interface.messages:
        raise RuntimeError(str(message_name) + ' is not a message in ' + interface_name)
    message = interface.messages[message_name]
    arg = list(message.args.values())[arg_index]
    return arg

def get_arg_name(interface_name, message_name, arg_index):
    arg = get_arg(interface_name, message_name, arg_index)
    if arg:
        return arg.name
    else:
        return None

def look_up_enum(interface_name, message_name, arg_index, arg_value):
    arg = get_arg(interface_name, message_name, arg_index)
    if not arg or not arg.enum:
        return []
    enum_name_parts = [interface_name] + arg.enum.split('.')
    enum_interface_name = enum_name_parts[-2]
    enum_name = enum_name_parts[-1]
    enum_interface = interfaces[enum_interface_name]
    if not enum_name in enum_interface.enums:
        raise RuntimeError(str(enum_name) + ' is not an enum in ' + enum_interface_name)
    enum = enum_interface.enums[enum_name]
    entries = []
    for entry in enum.entries.values():
        if enum.bitfield:
            if entry.value & arg_value:
                entries.append(entry.name)
        else:
            if entry.value == arg_value:
                entries.append(entry.name)
    if entries:
        return entries
    else:
        return ['INVALID ENUM VALUE']
