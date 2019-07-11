#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import struct
import json
import math
from decimal import Decimal


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__version__ = [0, 0]


struct_format_sign = ['b', 'h', 'i', 'q']
struct_format_unsign = ['B', 'H', 'I', 'Q']
byte_order = '>'


def define_hex_size_of_sign_number(number):
    for sign_of_size in xrange(Type.schema_max_sign_of_size+1):
        max_val = (1<<(8*(1<<sign_of_size)))/2-1
        min_val = -(1<<(8*(1<<sign_of_size)))/2
        if min_val <= number <= max_val:
            return sign_of_size
    raise Exception('int out of size {}'.format(number))


def define_hex_size_of_unsign_number(number):
    for sign_of_size in xrange(Type.schema_max_sign_of_size+1):
        max_val = 1<<(8*(1<<sign_of_size))
        if number < max_val:
            return sign_of_size
    raise Exception('int out of size {}'.format(number))


class NotFound:
    def __str__(self):
        return 'NOT_FIND'

    def __unicode__(self):
        return 'NOT_FIND'

    def __repr__(self):
        return 'NOT_FIND'

    def __getattr__(self, attr):
        return self

    def __getitem__(self, item):
        return self

    def __call__(self):
        return self

    def __eq__(self, inst):
        return self is inst


not_find = NotFound()


class Byte:
    def __init__(self, variable=0):
        if isinstance(variable, int):
            self.number = variable
        if isinstance(variable, str):
            self.number = ord(variable)

    def shift_bits(self, bit_number):
        self.number <<= bit_number
        return self

    def get(self):
        return chr(self.number)

    def put_number_on_place(self, number, place):
        return chr(self.number|(number<<place))

    def define_bits_by_number(self, number):
        bits = 0
        while (1<<bits)-1 < number:
            bits += 1
        return bits

    def number_or(self, byte):
        self.number |= byte
        return self

    def get_number_by_edge(self, low_bit, length):
        return (self.number>>low_bit)&((1<<length)-1)

    def char_and(self, char):
        self.number & ord(char)
        return self


class SchemaHandler:
    def pack_schema(self, schema, sign_of_size):
        return Byte(schema).put_number_on_place(
            number=sign_of_size,
            place=Type.schema_bit_length_bit)

    def unpack_sign_of_size(self, schema):
        length_of_bits = Byte().define_bits_by_number(Type.schema_max_sign_of_size)
        return Byte(schema).get_number_by_edge(Type.schema_bit_length_bit, length_of_bits)


class Integer:
    '''
    schema
    765 bits
    000 reserverd for type bits

     43 bits
    ~00~ length 1 byte
    ~01~ length 2 byte
    ~10~ length 4 byte
    ~11~ length 8 byte
    '''

    def __define_sign_of_size(self):
        self.sign_of_size = define_hex_size_of_sign_number(self.number)

    def __pack_type(self):
        self.schema = Type().pack(self)

    def __pack_sign_of_size(self):
        self.schema = SchemaHandler().pack_schema(self.schema, self.sign_of_size)

    def __pack_schema(self):
        self.__pack_type()
        self.__pack_sign_of_size()

    def __pack_data(self):
        self.__define_sign_of_size()
        fmt = byte_order+struct_format_sign[self.sign_of_size]
        self.data = struct.pack(fmt, self.number)

    def pack(self, number):
        self.number = number
        self.__pack_data()
        self.__pack_schema()
        return self.schema, self.data

    def __unpack_sign_of_size(self):
        self.sign_of_size = SchemaHandler().unpack_sign_of_size(self.schema[0])

    def __unpack_schema(self):
        self.__unpack_sign_of_size()
        self.schema_tail = self.schema[1:]

    def __unpack_data(self):
        data_lengh = 2**self.sign_of_size
        fmt = byte_order + struct_format_sign[self.sign_of_size]
        self.number, = struct.unpack(fmt, self.data[:data_lengh])
        self.data_tail = self.data[data_lengh:]

    def unpack(self, schema, data):
        self.schema = schema
        self.data = data
        self.__unpack_schema()
        self.__unpack_data()
        return self.number, self.schema_tail, self.data_tail


class Float:
    '''
    schema
    765 bits
    000~ reserverd for type bits

     43  bits
    ~00~ length 1 byte
    ~01~ length 2 byte
    ~10~ length 4 byte
    ~11~ length 8 byte

    '''

    denormalized = {
        #               -128
        #float('-nan'): '\x80\x7f\xff\xff\xff\xff\xff\xff\xfe',
        'nan':  '\x80\x7f\xff\xff\xff\xff\xff\xff\xff',
        '-inf': '\x80\x80\x00\x00\x00\x00\x00\x00\x00',
        'inf':  '\x80\x80\x00\x00\x00\x00\x00\x00\x01'
    }

    def __get_mantissa_and_exponent_from_variable(self):
        self.__check_exponent()
        self.__check_dot()
        self.__cut_right_zeros()
        self.mantissa = int(self.mantissa)

    def __check_exponent(self):
        if 'e' in str(self.variable):
            self.mantissa, self.exponent = str(self.variable).split('e')
        else:
            self.mantissa = str(self.variable)
            self.exponent = '0'

    def __check_dot(self):
        if '.' in self.mantissa:
            self.exponent = int(self.exponent) - len(self.mantissa) + self.mantissa.index('.') + 1
            self.mantissa = self.mantissa.replace('.', '')
        else:
            self.exponent = int(self.exponent)

    def __cut_right_zeros(self):
        self.exponent += len(self.mantissa) - len(self.mantissa.rstrip('0'))
        self.mantissa = self.mantissa.rstrip('0')

    def __check_exponent_size(self):
        if self.exponent > 0xFF:
            print 'Error: exponent more then 0xFF'
            raise

    def __put_exponent_to_data(self):
        self.data = struct.pack('>b', self.exponent)

    def __put_mantissa_to_data(self):
        fmt = byte_order + struct_format_sign[self.sign_of_mantissa_size]
        self.data += struct.pack(fmt, self.mantissa)

    def __define_sign_of_mantissa_size(self):
        self.sign_of_mantissa_size = define_hex_size_of_sign_number(self.mantissa)

    def __pack_sign_of_size(self):
        self.schema = SchemaHandler().pack_schema(self.schema, self.sign_of_mantissa_size)

    def __pack_schema(self):
        self.schema = Type().pack(self)
        self.__pack_sign_of_size()

    def __pack_data(self):
        self.__get_mantissa_and_exponent_from_variable()
        self.__check_exponent_size()
        self.__define_sign_of_mantissa_size()
        self.__put_exponent_to_data()
        self.__put_mantissa_to_data()

    def __check_denormalized_variable(self):
        if str(self.variable) in Float.denormalized.keys():
            return True
        return False

    def __pack_denormalized(self):
        self.sign_of_mantissa_size = 3
        self.__pack_schema()
        self.data = Float.denormalized[str(self.variable)]

    def pack(self, variable):
        self.variable = variable
        if self.__check_denormalized_variable() is True:
            self.__pack_denormalized()
            return self.schema, self.data
        self.__pack_data()
        self.__pack_schema()
        return self.schema, self.data

    def __unpack_schema(self):
        self.__unpack_length()
        self.schema_tail = self.schema[1: ]

    def __unpack_length(self):
        self.sign_of_mantissa_size = SchemaHandler().unpack_sign_of_size(self.schema[0])

    def __unpack_exponent(self):
        self.exponent = struct.unpack('>b', self.data[0])[0]

    def __unpack_mantissa(self):
        data_lengh = 2 ** self.sign_of_mantissa_size
        fmt = byte_order + struct_format_sign[self.sign_of_mantissa_size]
        mantissa_byte_start = 1
        mantissa_byte_end = mantissa_byte_start + data_lengh
        mantissa_bytes = self.data[mantissa_byte_start: mantissa_byte_end]
        self.mantissa = struct.unpack(fmt, mantissa_bytes)[0]
        self.data_tail = self.data[mantissa_byte_end: ]

    def __unpack_data(self):
        self.__unpack_exponent()
        self.__unpack_mantissa()
        self.variable = float(self.mantissa * Decimal(10) ** self.exponent)

    def __check_denormalized_data(self):
        if self.sign_of_mantissa_size != 3:
            return False

        data_lengh = 2 ** self.sign_of_mantissa_size
        exponent_and_mantissa_data = self.data[: 1 + data_lengh]

        if not exponent_and_mantissa_data in Float.denormalized.values():
            return False

        denormalized_revers = {v: k for k, v in Float.denormalized.items()}
        self.variable = float(denormalized_revers[exponent_and_mantissa_data])
        self.data_tail = self.data[1 + data_lengh: ]
        return True

    def __unpack_denormalized(self):
        pass

    def unpack(self, schema, data):
        self.schema = schema
        self.data = data
        self.__unpack_schema()
        if self.__check_denormalized_data():
            self.__unpack_denormalized()
            return self.variable, self.schema_tail, self.data_tail
        self.__unpack_data()
        return self.variable, self.schema_tail, self.data_tail


class String:
    def __check_variable_size_is_correct(self):
        if len(self.data) >= self.length:
            return
        raise Exception('data size less then {}'.format(self.length))

    def __pack_type(self):
        self.schema = Type().pack(self)

    def __pack_sign_of_size(self):
        self.schema = SchemaHandler().pack_schema(self.schema, self.sign_of_size)
        fmt = byte_order+struct_format_unsign[self.sign_of_size]
        self.schema += struct.pack(fmt, self.length)

    def __define_sign_of_size(self):
        self.length = len(self.variable)
        self.sign_of_size = define_hex_size_of_unsign_number(self.length)

    def __pack_schema(self):
        self.__pack_type()
        self.__pack_sign_of_size()

    def __pack_data(self):
        self.__define_sign_of_size()
        self.data = self.variable

    def pack(self, variable):
        self.variable = variable
        self.__pack_data()
        self.__pack_schema()
        return self.schema, self.data

    def __unpack_length(self):
        sign_of_size = SchemaHandler().unpack_sign_of_size(self.schema[0])
        fmt = byte_order + struct_format_unsign[sign_of_size]
        schema_size_length = 2**sign_of_size
        length_bits_start = 1
        length_bits_end = length_bits_start + schema_size_length
        length_bits = self.schema[length_bits_start: length_bits_end]

        self.schema_tail = self.schema[length_bits_end: ]
        self.length, = struct.unpack(fmt, length_bits)

    def __unpack_schema(self):
        self.__unpack_length()

    def __unpack_data(self):
        self.variable = self.data[: self.length]
        self.data_tail = self.data[self.length: ]

    def unpack(self, schema, data):
        self.schema = schema
        self.data = data
        self.__unpack_schema()
        self.__unpack_data()
        return self.variable, self.schema_tail, self.data_tail


class Boolean:
    variables = {
        False: '\x00',
        True:  '\x01',
        None:  '\xff',
    }

    def pack(self, variable):
        self.schema = Type().pack(self)
        self.data = self.variables[variable]
        return self.schema, self.data

    def unpack(self, schema, data):
        self.schema = schema
        self.data = data
        self.variable = self.variables.keys()[
            self.variables.values().index(self.data[0])
        ]
        return self.variable, self.schema[1:], self.data[1:]


class List:
    # TODO
    # bit
    #   7 unequeal/equal type objects                    0/1
    #   6 bytes len objects off/on                       0/1
    #   5 bytes len in map/data                          0/1
    #   4 address each NN objects (for long List) off/of 0/1
    #     full length of List

    bit_length_high = 3

    def __init__(self, variable):
        if isinstance(variable, list):
            self.variable = variable
        if isinstance(variable, str):
            self.data = variable

    def __pack_item(self, item):
        item_type = Type(item).type
        self.map += item_type.pack
        self.data += item_type(item).pack

    @property
    def pack(self):
        self.map, self.data = '', ''
        for items in self.variable:
            self.__pack_item(items)
        return self.map, self.data

    @property
    def unpack(self):
        return self.variable


class Dictionary:
    '''
    keys and/or values type is unequal                    = 0
    all keys type are equal and all value types are equal = 1
    all keys and value are equal                          = 2
    definition_bit =   4  schema/data = 0/1
    length_bit     =   2
    equal_definition = 0
    '''

    def pack(self, number):
        pass

    def unpack(self, data):
        pass


class Contraction:
    def __init__(self):
        pass

    def pack(self, item):
        pass

    def unpack(self, item):
        pass


class Type:
    '''
    # type bits mark as 1
    11100000

     43 bits
    ~00~ length 1 byte
    ~01~ length 2 byte
    ~10~ length 4 byte
    ~11~ length 8 byte

    '''
    type_bit = 5
    schema_bit_length_bit = 3
    schema_max_sign_of_size = 3

    types_mapping = (
        (int,        Integer),
        (long,       Integer),
        (float,      Float),
        (str,        String),
        (bool,       Boolean),
        (type(None), Boolean),
        (list,       List),
        (dict,       Dictionary),
    )

    types_index = (
        Integer,
        Float,
        String,
        Boolean,
        List,
        Dictionary,
        Contraction,
    )

    def pack(self, obj):
        for class_type in self.types_index:
            if isinstance(obj, class_type):
                obj_index = self.types_index.index(class_type)
                return Byte(obj_index).shift_bits(self.type_bit).get()
        raise Exception('wrong type data {}'.format(obj))

    def unpack(self, schema):
        pass


#=============================================================================#



class BTYPE:
    b_type = {
        0: type(None),
        1: bool,
        2: int,
        3: str
    }

    def pack(self, t):
        pass

    def unpack(self, t):
        pass

    def validator(self, t):
        pass

    '''
    NONE =      0
    BOOL =      1
    INT =       2
    INT_LEN =   3
    FLOAT =     4
    FLOAT_LEN = 5
    STR =       6
    HASH =      7
    ARRAY =     8
    INT_8
    INT_16
    INT_32
    INT_64


    '''



    #    2: int,          # positiv integer
    #    3: int,          # negativ integer
    #    4: int,          # positiv integet positiv exp
    #    5: int,          # negativ integer positiv exp
    #    6: int,          # positiv integet negativ exp
    #    7: int,          # negativ integer negativ exp

    def pack(self, value):
        if not isinstance(value, (int, long, float, Decimal)):
            print 'Error: not a number'
            raise
        sign = False if value < 0 else True
        exp = False
        if value - int(value) != 0 or value % 10 == 0:
            exp = True

        if not sign and not exp:
            pass

    def unpack(self, value, t=None):
        pass

    def validator(self, value, t=None):
        pass


class BNONE:
    @classmethod
    def pack(self):
        return {v: k for k, v in BTYPE.b_type.items()}[type(None)]

    @classmethod
    def unpack(self):
        return None


class BBOOL:
    TYPES = {
        '\x00': False,
        '\x01': True,
    }

    @classmethod
    def pack(self, x):
        return {v: k for k, v in BBOOL.TYPES.items()}[x]

    @classmethod
    def unpack(self, x):
        return BBOOL.TYPES[x]


class BDATA:
    def __init__(self, data, force=True):
        self.__dict__['__path'] = []
        self.__dict__['__force'] = force

        if isinstance(data, (str, unicode)):
            self.__parse_bin(data)
            return

        if isinstance(data, (dict, list)):
            self.__dict__['__data'] = data
            return

    def __getattr__(self, attr):
        self.__dict__['__path'].append(attr)
        return self

    def __getitem__(self, item):
        self.__dict__['__path'].append(item)
        return self

    def __setattr__(self, attr, value):
        self.__dict__['__path'].append(attr)
        if not self.__get_node() is not_find or self.__dict__['__force'] is True:
            self.__dict__['__data'] = self.__put_node(value)
        self.__dict__['__path'] = []

    def __setitem__(self, item, value):
        self.__dict__['__path'].append(item)
        if not self.__get_node() is not_find or self.__dict__['__force'] is True:
            self.__dict__['__data'] = self.__put_node(value)
        self.__dict__['__path'] = []

    def __eq__(self, item):
        return self.__dict__['__data'] == item

    def __str__(self):
        return json.dumps(self.__dict__['__data'], indent=2)

    def __unicode__(self):
        return json.dumps(self.__dict__['__data'], indent=2)

    def __repr__(self):
        return json.dumps(self.__dict__['__data'], indent=2)

    def __call__(self):
        return not_find

    def __check_data_key(self, data, key):
        if isinstance(data, dict) and key in data.keys() or \
           isinstance(data, (list, tuple)) and isinstance(key, (int, long)) and len(data) > key:
            return
        return not_find

    def __get_node(self):
        data = self.__dict__['__data']
        for x in self.__dict__['__path']:
            check = self.__check_data_key(data, x)
            if check is not_find:
                return not_find
            data = data[x]
        return data

    def __put_node(self, value, obj=not_find, path=None):
        if obj is not_find:
            obj = self.__dict__['__data']
        if path is None:
            path = self.__dict__['__path']

        if path == []:
            return value

        key = path[0]
        child_path = path[1:]
        if self.__check_data_key(obj, key) is not_find:
            if not isinstance(obj, dict):
                obj = {}
            child_obj = {}
        else:
            child_obj = obj[key]

        child = self.__put_node(value, child_obj, child_path)
        if child is not_find:
            return not_find
        obj[key] = child
        return obj

    def _copy(self, bad_response=not_find):
        copy = self.__get_node()
        self.__dict__['__path'] = []
        if isinstance(copy, (dict, list)):
            return BDATA(copy)
        if copy is not_find:
            return bad_response
        return copy

    @property
    def _bin(self):
        return ''

    @property
    def _json(self):
        js = self.__get_node()
        self.__dict__['__path'] = []
        return js


def test_integer():
    print '-' * 10
    print 'Integer'
    additional_data = '\xff'
    pack_test_cases = [
        # regular length 1 byte (b)
        {'value': 0, 'schema': '\x00', 'data': '\x00'},
        {'value': 0x7f, 'schema': '\x00', 'data': '\x7f'},
        {'value': -0x80, 'schema': '\x00', 'data': '\x80'},
        # regular length 2 byte (h)
        {'value': 0x80, 'schema': '\x08', 'data': '\x00\x80'},
        {'value': -0x81, 'schema': '\x08', 'data': '\xff\x7f'},
        {'value': 0x7fff, 'schema': '\x08', 'data': '\x7f\xff'},
        {'value': -(0x8000), 'schema': '\x08', 'data': '\x80\x00'},
        # regular length 4 bytes (l)
        {'value': 0x8000, 'schema': '\x10', 'data': '\x00\x00\x80\x00'},
        {'value': -(0x8001), 'schema': '\x10', 'data': '\xff\xff\x7f\xff'},
        {'value': 0x7fffffff, 'schema': '\x10', 'data': '\x7f\xff\xff\xff'},
        {'value': -(0x80000000), 'schema': '\x10', 'data': '\x80\x00\x00\x00'},
        # regular length 8 bytes (q)
        {'value': 0x80000000, 'schema': '\x18', 'data': '\x00\x00\x00\x00\x80\x00\x00\x00'},
        {'value': -(0x80000001), 'schema': '\x18', 'data': '\xff\xff\xff\xff\x7f\xff\xff\xff'},
        {'value': 0x7fffffffffffffff, 'schema': '\x18', 'data': '\x7f\xff\xff\xff\xff\xff\xff\xff'},
        {'value': -(0x8000000000000000), 'schema': '\x18', 'data': '\x80\x00\x00\x00\x00\x00\x00\x00'},
    ]

    for case in pack_test_cases:
        schema, data = Integer().pack(case['value'])
        if schema != case['schema']:
            print 'Error pack schema', \
                'value:',  hex(case['value']), \
                'got schema:', schema.encode('hex'), \
                'expected schema:', case['schema'].encode('hex')

        if data != case['data']:
            print 'Error pack data', \
                'value', hex(case['value']), \
                'got data:', data.encode('hex'), \
                'expected data', case['data'].encode('hex')

    for case in pack_test_cases:
        value, schema_tail, data_tail = Integer().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        if value != case['value']:
            print 'Error unpack value', \
                'expected value:',  hex(case['value']), \
                'got value:', hex(value)
        if schema_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                'value', hex(case['value']), \
                'got schema_tail:', schema_tail.encode('hex'), \
                'expected schema_tail:', additional_data.encode('hex')
        if data_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                'value', hex(case['value']), \
                'got data_tail:', data_tail.encode('hex'), \
                'expected data_tail:', additional_data.encode('hex')


def test_boolean():
    print '-' * 10
    print 'Boolean'
    additional_data = '\xff'
    pack_test_cases = [
        {'value': True, 'schema': '\x60', 'data': '\x01'},
        {'value': False, 'schema': '\x60', 'data': '\x00'},
        {'value': None, 'schema': '\x60', 'data': '\xff'},
    ]

    for case in pack_test_cases:
        schema, data = Boolean().pack(case['value'])
        if schema != case['schema']:
            print 'Error pack schema', \
                'value:',  case['value'], \
                'got schema:', schema.encode('hex'), \
                'expected schema:', case['schema'].encode('hex')

        if data != case['data']:
            print 'Error pack data', \
                'value', case['value'], \
                'got data:', data.encode('hex'), \
                'expected data', case['data'].encode('hex')

    for case in pack_test_cases:
        value, schema_tail, data_tail = Boolean().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        if value != case['value']:
            print 'Error unpack value', \
                'expected value:',  case['value'], \
                'got value:', value
        if schema_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                'value', case['value'], \
                'got schema_tail:', schema_tail.encode('hex'), \
                'expected schema_tail:', additional_data.encode('hex')
        if data_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                'value', case['value'], \
                'got data_tail:', data_tail.encode('hex'), \
                'expected data_tail:', additional_data.encode('hex')


def test_string():
    print '-' * 10
    print 'String'
    additional_data = '\xff'
    pack_test_cases = [
        {'value': 'abc', 'schema': '\x40', 'data': '\x03' + 'abc'},
        {'value': '123', 'schema': '\x40', 'data': '\x03' + '123'},
        {'value': 'Лис', 'schema': '\x40', 'data': '\x06' + 'Лис'},
        {'value': '123qweйцу', 'schema': '\x40', 'data': '\x0c' + '123qweйцу'},
        {'value': '0'*((1<<8)-1), 'schema': '\x40', 'data': '\xff'*1 + '0'*((1<<8)-1)},
        {'value': '0'*((1<<16)-1), 'schema': '\x48', 'data': '\xff'*2' + '0'*((1<<16)-1)},
        #{'value': '0'*((1<<32)-1), 'schema': '\x50', 'data': '\xff'*4 + '0'*((1<<32)-1)},
        #{'value': '0'*((1<<33)-1), 'schema': '\x70', 'data': ('\x00'*3)+'\x01'+('\xff'*4) + '0'*((1<<33)-1)},
     ]

    for case in pack_test_cases:
        schema, data = String().pack(case['value'])
        if schema != case['schema']:
            print 'Error pack schema', \
                    'value:',  case['value'][:10], \
                'got schema:', schema.encode('hex'), \
                'expected schema:', case['schema'].encode('hex')

        if data != case['data']:
            print 'Error pack data', \
                    'value', case['value'][:10], \
                    'got data:', data.encode('hex')[:10], \
                    'expected data', case['data'].encode('hex')[:10]

    for case in pack_test_cases:
        value, schema_tail, data_tail = String().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        if value != case['value']:
            print 'Error unpack value', \
                'expected value:',  case['value'][:10], \
                'got value:', value[:10]
        if schema_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                'value', case['value'][:10], \
                'got schema_tail:', schema_tail.encode('hex'), \
                'expected schema_tail:', additional_data.encode('hex')
        if data_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                'value', case['value'][:10], \
                'got data_tail:', data_tail.encode('hex'), \
                'expected data_tail:', additional_data.encode('hex')


def test_float():
    print '-' * 10
    print 'Float'

    additional_data = '\xff'
    pack_test_cases = [
        {'value': -0.0000000001,  'schema': '\x20', 'data': '\xf6\xff'            },  # -10  1
        {'value': 1e-10,          'schema': '\x20', 'data': '\xf6\x01'            },  # -10  1
        {'value': 1e+127,         'schema': '\x20', 'data': '\x7f\x01'            },  #  127 1
        {'value': 1e-128,         'schema': '\x20', 'data': '\x80\x01'            },  # -128 1
        {'value': 0.1,            'schema': '\x20', 'data': '\xff\x01'            },  # -1   1
        {'value': 0.222,          'schema': '\x28', 'data': '\xfd\x00\xde'        },  # -1   222
        {'value': -0.222,         'schema': '\x28', 'data': '\xfd\xff\x22'        },  # -1  -222
        {'value': 0.0001111111,   'schema': '\x30', 'data': '\xf6\x00\x10\xf4\x47'},  # -10  1111111
        {'value': -0.0001111111,  'schema': '\x30', 'data': '\xf6\xff\xef\x0b\xb9'},  # -10 -1111111
        {'value': 1.00000001,     'schema': '\x30', 'data': '\xf8\x05\xf5\xe1\x01'},  # -8   100000001
        {'value': -1.00000001,    'schema': '\x30', 'data': '\xf8\xfa\x0a\x1e\xff'},  # -8  -100000001
        {'value': 10000000.0,     'schema': '\x20', 'data': '\x07\x01'            },  #  7   1
        {'value': -10000000.0,    'schema': '\x20', 'data': '\x07\xff'            },  #  7  -1
        {'value': 1.2323435e-19,  'schema': '\x30', 'data': '\xe6\x00\xbc\x0a\x6b'},  # -26  12323435
        {'value': -1.2323435e-19, 'schema': '\x30', 'data': '\xe6\xff\x43\xf5\x95'},  # -26 -12323435
        {'value': 1.1111e+19,     'schema': '\x28', 'data': '\x0f\x2b\x67'        },  #  15  11111
        {'value': -1.1111e+19,    'schema': '\x28', 'data': '\x0f\xd4\x99'        },  #  15 -11111
        {'value': float('nan'),   'schema': '\x38', 'data': '\x80\x7f\xff\xff\xff\xff\xff\xff\xff'}, #
        {'value': float('-inf'),  'schema': '\x38', 'data': '\x80\x80\x00\x00\x00\x00\x00\x00\x00'}, #
        {'value': float('inf'),   'schema': '\x38', 'data': '\x80\x80\x00\x00\x00\x00\x00\x00\x01'}, #
    ]
    for case in pack_test_cases:
        schema, data = Float().pack(case['value'])
        if schema != case['schema']:
            print 'Error pack schema', \
                'value:',  case['value'], \
                'got schema:', schema.encode('hex'), \
                'expected schema:', case['schema'].encode('hex')

        if data != case['data']:
            print 'Error pack data', \
                'value', case['value'], \
                'got data:', data.encode('hex'), \
                'expected data', case['data'].encode('hex')

    for case in pack_test_cases:
        value, schema_tail, data_tail = Float().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        if value != case['value'] and str(value) != str(case['value']):
            print 'Error unpack value', \
                'expected value:',  [case['value']], type(case['value']), \
                'got value:', [value], type(value)
        if schema_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                'value', case['value'], \
                'got schema_tail:', schema_tail.encode('hex'), \
                'expected schema_tail:', additional_data.encode('hex')
        if data_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                'value', case['value'], \
                'got data_tail:', data_tail.encode('hex'), \
                'expected data_tail:', additional_data.encode('hex')


def tests():
    print 'test start'
    test_string()
    test_integer()
    test_boolean()
    test_float()

    print '-' * 10
    print 'test end'


if __name__ == '__main__':
    tests()
