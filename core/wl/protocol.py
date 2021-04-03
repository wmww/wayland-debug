import xml.etree.ElementTree as ET
from collections import OrderedDict
import logging
from typing import Dict

from core.util import project_root
from os import path
import sys
import time
import re

logger = logging.getLogger(__name__)

class Protocol:
    def __init__(self, name, xml_file, interfaces):
        assert isinstance(name, str)
        assert isinstance(interfaces, OrderedDict)
        for i in interfaces.values():
            i.parent = self
        self.name = name
        self.xml_file = xml_file
        self.interfaces = interfaces

class Interface:
    def __init__(self, name, version, messages, enums):
        assert isinstance(name, str)
        assert isinstance(version, int)
        assert version > 0
        assert isinstance(messages, OrderedDict)
        assert isinstance(enums, OrderedDict)
        for i in messages.values():
            i.parent = self
        for i in enums.values():
            i.parent = self
        self.name = name
        self.version = version
        self.messages = messages
        self.enums = enums

class Message:
    def __init__(self, name, is_event, args):
        assert isinstance(name, str)
        assert isinstance(is_event, bool)
        assert isinstance(args, OrderedDict)
        for i in args.values():
            i.parent = self
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
        for i in entries.values():
            assert isinstance(i, Entry)
            i.parent = self
        self.name = name
        self.bitfield = bitfield
        self.entries = entries

class Entry:
    def __init__(self, name, value):
        assert isinstance(name, str)
        assert isinstance(value, int)
        self.name = name
        self.value = value

def parse_arg(arg):
    return Arg(
        arg.attrib['name'],
        arg.attrib['type'],
        arg.attrib.get('interface', None),
        arg.attrib.get('enum', None))

def parse_message(message):
    args = OrderedDict()
    for node in message:
        if node.tag == 'arg':
            arg = parse_arg(node)
            args[arg.name] = arg
    return Message(message.attrib['name'], message.tag == 'event', args)

number_re = re.compile(r'^\w+$') # Matches 7 and 0x42
bitshift_re = re.compile(r'^(\w+)\s*<<\s*(\w+)$') # matches 3 << 4
def parse_enum_value(value):
    assert isinstance(value, str)
    if number_re.match(value):
        # "Base 0 means to interpret exactly as a code literal"
        # Value might be base 10 or hex, but format should be the same as Python literals
        return int(value, 0)
    match = bitshift_re.match(value)
    if match:
        return int(match.group(1), 0) << int(match.group(2), 0)
    raise RuntimeError('Could not parse enum value ' + repr(value))

def parse_enum_entry(entry):
    value = parse_enum_value(entry.attrib['value'].strip())
    return Entry(entry.attrib['name'], value)

def parse_enum(enum):
    bitfield_str = enum.attrib.get('bitfield', 'false')
    if bitfield_str == 'true':
        bitfield = True
    elif bitfield_str == 'false':
        bitfield = False
    else:
        raise RuntimeError('Invalid bitfield string: ' + repr(bitfield_str))
    entries = OrderedDict()
    for node in enum:
        if node.tag == 'entry':
            entry = parse_enum_entry(node)
            entries[entry.name] = entry
    return Enum(enum.attrib['name'], bitfield, entries)

def parse_interface(interface):
    version = int(interface.attrib['version'])
    messages = OrderedDict()
    enums = OrderedDict()
    for node in interface:
        if node.tag == 'event' or node.tag == 'request':
            message = parse_message(node)
            messages[message.name] = message
        elif node.tag == 'enum':
            enum = parse_enum(node)
            enums[enum.name] = enum
    return Interface(interface.attrib['name'], version, messages, enums)

def parse_protocol(xmlfile):
    protocol = ET.parse(xmlfile).getroot()
    assert protocol.tag == 'protocol'
    interfaces = OrderedDict()
    for node in protocol:
        if node.tag == 'interface':
            interface = parse_interface(node)
            interfaces[interface.name] = interface
    return Protocol(protocol.attrib['name'], xmlfile, interfaces)

interfaces: Dict[str, Interface] = {}

def load(xml_file, out):
    try:
        protocol = parse_protocol(xml_file)
    except:
        raise RuntimeError('Failed to parse ' + xml_file)
    for name, interface in protocol.interfaces.items():
        existing = interfaces.get(name, None)
        if not existing or existing.version < interface.version:
            interfaces[name] = interface
    logger.info('Loaded ' + str(len(protocol.interfaces)) + ' interfaces from ' + xml_file)

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

def protocols_path():
    return path.join(project_root(), 'resources', 'protocols')

def load_all(out):
    start = time.perf_counter()
    shipped_protocols_path = protocols_path()
    if not path.isdir(shipped_protocols_path):
        out.warn(
            'Could not fined protocols shipped with Wayland Debug at ' + shipped_protocols_path +
            ', will look for protocols on system and fall back to simpler output when not found')
    files = (
        discover_xml('/usr/share/wayland', out) +
        discover_xml('/usr/share/wayland-protocols', out) +
        discover_xml(shipped_protocols_path, out)
    )
    for xml_file in files:
        load(xml_file, out)
    end = time.perf_counter()
    logger.info('Took ' + str(int((end - start) * 1000)) + 'ms to load ' + str(len(files)) + ' protocol files')

    # Come on protocols, tag your fukin enums
    try:
        interfaces['wl_data_offer'].messages['set_actions'].args['dnd_actions'].enum = 'wl_data_device_manager.dnd_action'
        interfaces['wl_data_offer'].messages['set_actions'].args['preferred_action'].enum = 'wl_data_device_manager.dnd_action'
        interfaces['wl_data_offer'].messages['source_actions'].args['source_actions'].enum = 'wl_data_device_manager.dnd_action'
        interfaces['wl_data_offer'].messages['action'].args['dnd_action'].enum = 'wl_data_device_manager.dnd_action'
        interfaces['wl_data_source'].messages['set_actions'].args['dnd_actions'].enum = 'wl_data_device_manager.dnd_action'
        interfaces['wl_data_source'].messages['action'].args['dnd_action'].enum = 'wl_data_device_manager.dnd_action'

        interfaces['wl_pointer'].messages['button'].args['button'].enum = 'fake_enums.button'

        interfaces['zxdg_toplevel_v6'].messages['configure'].args['states'].enum = 'state'
        interfaces['zxdg_toplevel_v6'].messages['resize'].args['edges'].enum = 'resize_edge'
        interfaces['zxdg_positioner_v6'].messages['set_constraint_adjustment'].args['constraint_adjustment'].enum = 'constraint_adjustment'

        interfaces['xdg_toplevel'].messages['configure'].args['states'].enum = 'state'
        interfaces['xdg_toplevel'].messages['resize'].args['edges'].enum = 'resize_edge'
        interfaces['xdg_positioner'].messages['set_constraint_adjustment'].args['constraint_adjustment'].enum = 'constraint_adjustment'

        interfaces['zwlr_foreign_toplevel_handle_v1'].messages['state'].args['state'].enum = 'state'

        interfaces['org_kde_kwin_server_decoration_manager'].messages['default_mode'].args['mode'].enum = 'mode'
        interfaces['org_kde_kwin_server_decoration'].messages['request_mode'].args['mode'].enum = 'mode'
        interfaces['org_kde_kwin_server_decoration'].messages['mode'].args['mode'].enum = 'mode'

        interfaces['fake_enums'] = Interface(
            'fake_enums',
            1,
            OrderedDict(),
            OrderedDict([( # from /usr/include/linux/input-event-codes.h
                'button',
                Enum(
                    'button',
                    False,
                    OrderedDict([
                        ('left', Entry('left', 0x110)),
                        ('right', Entry('right', 0x111)),
                        ('middle', Entry('middle', 0x112)),
                    ])
                )
            )])
        )

        interfaces['wl_pointer'].messages['button'].args['button'].enum = 'fake_enums.button'
    except KeyError as e:
        print(list(interfaces))
        out.warn('Could not set up enum for: ' + str(e))
    # Uncomment this when debugging enum tagging
    """
    for i in interfaces.values():
        for m in i.messages.values():
            for a in m.args.values():
                if a.type == 'array' and not a.enum:
                    print('array without enum:', i.parent.xml_file, '::', i.name, '.', m.name, '(', a.name, ')')
                if a.enum:
                    get_enum(i.name, a.enum).used = True
        for e in i.enums.values():
            if e.name != 'error' and not hasattr(e, 'used'):
                print('unused enum:', i.parent.xml_file, '::', i.name, '.', e.name, '(', ', '.join([j.name for j in e.entries.values()]), ')')
    # check to make sure all the enums are valid
    for i in interfaces.values():
        for m in i.messages.values():
            for index, a in enumerate(m.args.values()):
                if a.enum:
                    get_enum(i.name, a.enum)
    exit(1)
    """

def dump_all():
    global interfaces
    interfaces = {}

def get_arg(interface_name, message_name, arg_index):
    if (interface_name, message_name) == ('wl_registry', 'bind'):
        return None # the protocol doesn't match the detected messages
    interface = interfaces.get(interface_name)
    if not interface:
        return None
    message = interface.messages.get(message_name)
    if not message:
        raise RuntimeError(str(message_name) + ' is not a message in ' + str(interface_name))
    arg_list = list(message.args.values())
    if arg_index >= len(arg_list):
        raise RuntimeError(
            'Tried to access arg ' + str(arg_index) +
            ' in ' + str(interface_name) + '.' + str(message_name) +
            ' (which only has ' + str(len(arg_list)) + ' args)')
    arg = arg_list[arg_index]
    return arg

def get_arg_name(interface_name, message_name, arg_index):
    arg = get_arg(interface_name, message_name, arg_index)
    if arg:
        return arg.name
    else:
        return None

def look_up_interface(interface_name, message_name, arg_index):
    arg = get_arg(interface_name, message_name, arg_index)
    return arg.interface

def get_enum(interface_name, enum_path):
    # enum can be "interface.enum" or just "enum" (in which case the provided interface is used)
    enum_name_parts = [interface_name] + enum_path.split('.')
    enum_interface_name = enum_name_parts[-2]
    enum_name = enum_name_parts[-1]
    enum_interface = interfaces[enum_interface_name]
    if not enum_name in enum_interface.enums:
        raise RuntimeError(str(enum_name) + ' is not an enum in ' + enum_interface_name)
    return enum_interface.enums[enum_name]

def look_up_enum(interface_name, message_name, arg_index, arg_value):
    arg = get_arg(interface_name, message_name, arg_index)
    if not arg or not arg.enum:
        return []
    enum = get_enum(interface_name, arg.enum)
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
    elif enum.bitfield:
        return ['(none)']
    else:
        return ['INVALID ENUM VALUE']
