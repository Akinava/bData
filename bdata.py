#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import struct
import json
from decimal import Decimal

__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__version__ = [0, 0]


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

    def get_number_by_edge(self, low_bit, length):
        return (self.number>>low_bit)&((1<<length)-1)


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

    struct_format = ['b', 'h', 'i', 'q']
    byte_order = '>'

    def __define_sign_of_size(self):
        for sign_of_size in xrange(Type.schema_max_sign_of_size+1):
            max_vol = (1<<(8*(1<<sign_of_size)))/2-1
            min_vol = -(1<<(8*(1<<sign_of_size)))/2
            if min_vol <= self.number <= max_vol:
                self.sign_of_size = sign_of_size
                return
        raise Exception('int out of size {}'.format(self.number))

    def __puck_type(self):
        self.schema = Type().pack(self)

    def __puck_sign_of_size(self):
        self.schema = SchemaHandler().pack_schema(self.schema, self.sign_of_size)

    def __pack_schema(self):
        self.__puck_type()
        self.__puck_sign_of_size()

    def __pack_sign_of_size(self):
        fmt = self.byte_order+self.struct_format[self.sign_of_size]
        self.data = struct.pack(fmt, self.number)

    def pack(self, number):
        self.number = number
        self.__define_sign_of_size()
        self.__pack_schema()
        self.__pack_sign_of_size()
        return self.schema, self.data

    def __unpack_sign_of_size(self):
        self.sign_of_size = SchemaHandler().unpack_sign_of_size(self.schema[0])

    def __unpack_schema(self):
        self.__unpack_sign_of_size()
        self.schema_tail = self.schema[1:]

    def __unpack_data(self):
        data_lengh = 2**self.sign_of_size
        fmt = self.struct_format[self.sign_of_size]
        self.number, = struct.unpack(self.byte_order+fmt, self.data[:data_lengh])
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

     43 bits
    ~00~ length 1 byte
    ~01~ length 2 byte
    ~10~ length 4 byte
    ~11~ length 8 byte

     0 bit
    ~0 nan
    ~1 inf
    '''

    def pack(self, variable):
        self.schema = Type().pack(self)
        print self.schema.encode('hex')

        return '', ''

    def unpack(self):
        return '', '', ''


class String:
    def __check_variable_size_is_correct(self):
        if len(self.data) >= self.length:
            return
        raise Exception('data size less then {}'.format(self.length))

    def __puck_type(self):
        self.schema = Type().pack(self)

    def __puck_data_length(self):
        self.length = len(self.variable)
        if self.length < 1<<8:
            self.schema += chr(self.length)
        elif self.length < 1<<16:
            self.schema = SchemaHandler().pack_schema(self.schema, 1) + struct.pack('>H', self.length)
        elif self.length < 1<<32:
            self.schema = SchemaHandler().pack_schema(self.schema, 2) + struct.pack('>I', self.length)
        else:
            self.schema = SchemaHandler().pack_schema(self.schema, 3) + struct.pack('>Q', self.length)

    def __pack_schema(self):
        self.__puck_type()
        self.__puck_data_length()

    def pack(self, variable):
        self.variable = variable
        self.__pack_schema()
        return self.schema, self.variable

    def __unpack_length(self):
        sign_of_size = SchemaHandler().unpack_sign_of_size(self.schema[0])
        if sign_of_size == 0:
            self.length = ord(self.schema[1])
            self.schema_tail = self.schema[2:]
        elif sign_of_size == 1:
            self.length, = struct.unpack('>H', self.schema[1:3])
            self.schema_tail = self.schema[3:]
        elif sign_of_size ==  2:
            self.length, = struct.unpack('>I', self.schema[1:5])
            self.schema_tail = self.schema[5:]
        elif sign_of_size ==  3:
            self.length, = struct.unpack('>Q', self.schema[1:9])
            self.schema_tail = self.schema[9:]

    def __unpack_schema(self):
        self.__unpack_length()

    def __unpack_data(self):
        self.variable = self.data[:self.length]
        self.data_tail = self.data[self.length:]

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
                "value:",  hex(case['value']), \
                "got schema:", schema.encode('hex'), \
                "expected schema:", case['schema'].encode('hex')

        if data != case['data']:
            print 'Error pack data', \
                "value", hex(case['value']), \
                "got data:", data.encode('hex'), \
                "expected data", case['data'].encode('hex')

    for case in pack_test_cases:
        value, schema_tail, data_tail = Integer().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        if value != case['value']:
            print 'Error unpack value', \
                "expected value:",  hex(case['value']), \
                "got value:", hex(value)
        if schema_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                "value", hex(case['value']), \
                "got schema_tail:", schema_tail.encode('hex'), \
                "expected schema_tail:", additional_data.encode('hex')
        if data_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                "value", hex(case['value']), \
                "got data_tail:", data_tail.encode('hex'), \
                "expected data_tail:", additional_data.encode('hex')


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
                "value:",  case['value'], \
                "got schema:", schema.encode('hex'), \
                "expected schema:", case['schema'].encode('hex')

        if data != case['data']:
            print 'Error pack data', \
                "value", case['value'], \
                "got data:", data.encode('hex'), \
                "expected data", case['data'].encode('hex')

    for case in pack_test_cases:
        value, schema_tail, data_tail = Boolean().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        if value != case['value']:
            print 'Error unpack value', \
                "expected value:",  case['value'], \
                "got value:", value
        if schema_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                "value", case['value'], \
                "got schema_tail:", schema_tail.encode('hex'), \
                "expected schema_tail:", additional_data.encode('hex')
        if data_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                "value", case['value'], \
                "got data_tail:", data_tail.encode('hex'), \
                "expected data_tail:", additional_data.encode('hex')


def test_string():
    print '-' * 10
    print 'String'
    additional_data = '\xff'
    pack_test_cases = [
        {'value': 'abc', 'schema': '\x40\x03', 'data': 'abc'},
        {'value': '123', 'schema': '\x40\x03', 'data': '123'},
        {'value': 'Лис', 'schema': '\x40\x06', 'data': 'Лис'},
        {'value': '123qweйцу', 'schema': '\x40\x0c', 'data': '123qweйцу'},
        {'value': '0'*((1<<8)-1), 'schema': '\x40'+'\xff'*1, 'data': '0'*((1<<8)-1)},
        {'value': '0'*((1<<16)-1), 'schema': '\x48'+'\xff'*2, 'data': '0'*((1<<16)-1)},
        #{'value': '0'*((1<<32)-1), 'schema': '\x50'+'\xff'*4, 'data': '0'*((1<<32)-1)},
        #{'value': '0'*((1<<33)-1), 'schema': '\x70'+('\x00'*3)+'\x01'+('\xff'*4), 'data': '0'*((1<<33)-1)},
     ]

    for case in pack_test_cases:
        schema, data = String().pack(case['value'])
        if schema != case['schema']:
            print 'Error pack schema', \
                    "value:",  case['value'][:10], \
                "got schema:", schema.encode('hex'), \
                "expected schema:", case['schema'].encode('hex')

        if data != case['data']:
            print 'Error pack data', \
                    "value", case['value'][:10], \
                    "got data:", data.encode('hex')[:10], \
                    "expected data", case['data'].encode('hex')[:10]

    for case in pack_test_cases:
        value, schema_tail, data_tail = String().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        if value != case['value']:
            print 'Error unpack value', \
                "expected value:",  case['value'][:10], \
                "got value:", value[:10]
        if schema_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                "value", case['value'][:10], \
                "got schema_tail:", schema_tail.encode('hex'), \
                "expected schema_tail:", additional_data.encode('hex')
        if data_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                "value", case['value'][:10], \
                "got data_tail:", data_tail.encode('hex'), \
                "expected data_tail:", additional_data.encode('hex')


def test_float():
    print '-' * 10
    print 'Float'

    dbl = struct.unpack('>Q', struct.pack('>d', 1))[0]

    sign = -1 if dbl>>63 else 1
    exp = (dbl>>44)&((1<<43)-1)
    mnt = dbl&((1<<44)-1)
    print hex(dbl), sign, exp, mnt
    #number = sign*((1+mnt)/2**52)*2**(exp-1023)
    #print number


    additional_data = '\xff'
    pack_test_cases = [
        #{'value': 0.0001111111,   'schema': '\x30', 'data': '\xf6\x00\x10\xf4\x47'},  # -10 1111111
        #{'value': -0.0001111111,  'schema': '\x30', 'data': '\xf6\xff\xef\x0b\xb9'},  # -10 -1111111
        #{'value': 1.00000001,     'schema': '\x30', 'data': '\xf8\x45\xf5\xe1\x01'},  # -8 100000001
        #{'value': -1.00000001,    'schema': '\x30', 'data': '\xf8\xfa\x0a\x1e\xff'},  # -8 -100000001
        #{'value': 10000000.0,     'schema': '\x20', 'data': '\x07\x01'            },  # 7 1
        #{'value': -10000000.0,    'schema': '\x20', 'data': '\x07\xff'            },  # 7 -1
        #{'value': 1.2323435e-19,  'schema': '\x30', 'data': '\xe6\x00\xbc\x0a\x6b'},  # -26 12323435
        #{'value': -1.2323435e-19, 'schema': '\x30', 'data': '\xe6\xff\x43\xf5\x95'},  # -26 -12323435
        #{'value': 1.1111e+19,     'schema': '\x28', 'data': '\x0f\x2b\x67'        },  # 15 11111
        #{'value': -1.1111e+19,    'schema': '\x28', 'data': '\x0f\xd4\x99'        },  # 15 -11111
        ## TODO nan inf -inf
    ]
    for case in pack_test_cases:
        schema, data = Float().pack(case['value'])
        if schema != case['schema']:
            print 'Error pack schema', \
                "value:",  case['value'], \
                "got schema:", schema.encode('hex'), \
                "expected schema:", case['schema'].encode('hex')

        if data != case['data']:
            print 'Error pack data', \
                "value", case['value'], \
                "got data:", data.encode('hex'), \
                "expected data", case['data'].encode('hex')

    for case in pack_test_cases:
        value, schema_tail, data_tail = Float().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        if value != case['value']:
            print 'Error unpack value', \
                "expected value:",  case['value'], \
                "got value:", value
        if schema_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                "value", case['value'], \
                "got schema_tail:", schema_tail.encode('hex'), \
                "expected schema_tail:", additional_data.encode('hex')
        if data_tail != additional_data:
            print 'Error unpack wrong schema_tail', \
                "value", case['value'], \
                "got data_tail:", data_tail.encode('hex'), \
                "expected data_tail:", additional_data.encode('hex')


def tests():
    print 'test start'
    #test_string()
    #test_integer()
    #test_boolean()
    test_float()

    additional_data = '\xff'

    '''
    print '-' * 10
    print 'Float'

    pack_test = [
        {'value': 0.0001111111,   'schema': '0x00', 'data': '\x8a\x40\x10\xf4\x47'},  # -10 1111111
        {'value': -0.0001111111,  'schema': '0x00', 'data': '\x8a\xc0\x10\xf4\x47'},  # -10 -1111111
        {'value': 1.00000001,     'schema': '0x00', 'data': '\x88\x45\xf5\xe1\x01'},  # -8 100000001
        {'value': -1.00000001,    'schema': '0x00', 'data': '\x88\xc5\xf5\xe1\x01'},  # -8 -100000001
        {'value': 10000000.0,     'schema': '0x00', 'data': '\x07\x01'            },  # 7 1
        {'value': -10000000.0,    'schema': '0x00', 'data': '\x07\x81'            },  # 7 -1
        {'value': 1.2323435e-19,  'schema': '0x00', 'data': '\x9a\x40\xbc\x0a\x6b'},  # -26 12323435
        {'value': -1.2323435e-19, 'schema': '0x00', 'data': '\x9a\xc0\xbc\x0a\x6b'},  # -26 -12323435
        {'value': 1.1111e+19,     'schema': '0x00', 'data': '\x0f\x40\x00\x2b\x67'},  # 15 11111
        {'value': -1.1111e+19,    'schema': '0x00', 'data': '\x0f\xc0\x00\x2b\x67'},  # 15 -11111
    ]

    for case in pack_test:
        schema, data = Float(number).pack
        if data != data:
            print 'False pack', number, Float(number).pack
        float_number, rest_part_of_data = Float(data+additional_data).unpack
        if str(float_number) != str(number):
            print 'False unpack', number
        if rest_part_of_data != additional_data:
            print 'False rest data'

    print '-' * 10
    print 'Bool None'

    for variable, data in Boolean.variables.items():
        _, pack_bool = Boolean(variable).pack
        if pack_bool != data:
            print 'False pack', variable

        unpack_variable, rest_part_of_data = Boolean(data+additional_data).unpack
        if unpack_variable != variable:
            print 'False unpack', number
        if rest_part_of_data != additional_data:
            print 'False rest data'

    print '-' * 10
    print 'String'

    variables = [
        ['123qweQWE', '\x09123qweQWE'],
    ]

    for variable, data in variables:
        _, pack_str = String(variable).pack
        if pack_str != data:
            print 'False pack', [variable, String(variable).pack]

        unpack_variable, rest_part_of_data = String(data=data+additional_data).unpack
        if unpack_variable != variable:
            print 'False unpack', number
        if rest_part_of_data != additional_data:
            print 'False rest data'


    print '-' * 10
    print 'List'

    variables = [
        #              map                 data
        [[1, 2, '3'], '\x05\x03\x00\x00\x03\x01\x02\x01\x33'],
    ]

    for variable, data in variables:
        print variable
        data_map, data = List(variable).pack
        if data_map + data != data:
            print 'False pack', variable, (data_map + data).encode('hex')

        unpack_variable, rest_part_of_data = List(data+additional_data).unpack
        if unpack_variable != variable:
            print 'False unpack', variable, unpack_variable
        if rest_part_of_data != additional_data:
            print 'False rest data'
    '''

    print '-' * 10
    print 'test end'


if __name__ == '__main__':
    tests()
