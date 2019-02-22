#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
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
        self.variable = variable

    def get(self):
        return self.variable

    def set_bit(self, bit_number):
        self.variable |= 1 << bit_number
        return self.variable

    def make_mask(self, mask_size_in_byte=1):
        self.variable = ~self.variable & (1 << 8 * mask_size_in_byte) - 1
        return self.variable

    def shift_bits(self, shift_size):
        self.variable <<= shift_size
        return self.variable

    def shift_byte(self, shift_size):
        self.variable <<= 8 * shift_size
        return self.variable

    def get_maximal_value(self, start_bit, bytes=1):
        self.set_bit(start_bit+1)
        self.shift_byte(bytes-1)
        self.variable -= 1
        return self.variable


class IntStrConverter:
    def __init__(self, variable):
        self.variable = variable

    def convert_int_to_data(self, length=1):
        hex_string = '{:x}'.format(self.variable)
        if len(hex_string) % 2: hex_string = '0' + hex_string

        if len(hex_string) / 2 < length:
            hex_string = '00' * (length - len(hex_string) / 2) + hex_string

        return hex_string.decode('hex')

    def convert_data_to_int(self):
        return int(self.variable.encode('hex'), 16)


class Integer:
    '''
    schema
    765 bits
    000 reserverd for type bits

     432 bits
    ~000~ regular length 1 byte
    ~001~ regular length 2 byte
    ~010~ regular length 4 byte
    ~011~ regular length 8 byte
    ~10~  outsize length define aftert this bits
    ~11~  length define in data

    21 bits define outsize length in bytes if outsize length gefined in schema
    00 outsize length 1 byte
    01 outsize length 2 byte
    10 outsize length 4 byte
    11 outsize length 8 byte

    0 bit
    0 reserved

    outsize length of number in bytes defined as (length - max_regular_length - 1)
    because regular length include length ap to 8 bytes
    '''

    schema_bit_length_is_outsize = 4
    schema_bit_length_define_in_data = 3
    schema_bit_length_low_bit = 2
    schema_bit_outsize_length_low_bit = 1

    '''
    data
    7 reserved for sigh bit
    6 define/undefine outsize length depends on bit 4 in schema
    5 length of number/length depends on bit 6
    4 length of number/length depends on bit 6
    rest part number or length of number outsize length
    '''

    data_sigh_bit = 7
    data_length_is_outsize_bit = 6  # if this bit set as 1 no need in data_high_size_bit and data_low_size_bits
    data_length_low_bit = 4

    regular_length_bits_value = (0, 1, 2, 3)
    regular_length_list =       (1, 2, 4, 8)
    max_regular_length = max(regular_length_list)
    max_regular_number_length_in_schema = (0x7f, 0x7fff+0x7f, 0x7fffffff+0x7fff+0x7f, 0x7fffffffffffffff+0x7fffffff+0x7fff+0x7f)
    max_regular_number_length_in_data = (0x0f, 0x0fff+0x0f, 0x0fffffff+0x0fff+0x0f, 0x0fffffffffffffff+0x0fffffff+0x0fff+0x0f)

    def __init__(self, length_in_schema=True):
        self.length_in_schema = length_in_schema

    def __make_schema(self):
        self.__put_type_in_schema()
        if not self.length_in_schema:
            self.__set_in_schema_length_in_data()
        else:
            self.__put_length_in_schema()
        return IntStrConverter(self.schema_int).convert_int_to_data()

    def __put_length_in_schema(self):
        self.__get_length_in_bytes()
        if self.length_in_bytes > self.max_regular_length:
            self.__put_outsize_length_in_schema()
        else:
            self.__put_regular_length_in_schema()

    def __get_length_bits(self):
        length_index = self.regular_length_list.index(self.length_in_bytes)
        return self.regular_length_bits_value[length_index]

    def __put_regular_length_in_schema(self):
        length_bits = self.__get_length_bits()
        length_byte = Byte(length_bits)
        length_byte.shift_bits(self.schema_bit_length_low_bit)
        self.schema_int |= length_byte.get()

    def __set_outsize_length_schema_bit(self):
        outsize_length_in_schema_byte = Byte()
        outsize_length_in_schema_byte.set_bit(self.schema_bit_length_is_outsize)
        self.schema_int |= outsize_length_in_schema_byte.get()

    def __put_outsize_length_in_schema(self):
        self.__set_outsize_length_schema_bit()
        outsize_length_int = self.length_in_bytes - self.max_regular_length - 1

        outsize_length_bytes = len(IntStrConverter(outsize_length_int).convert_int_to_data())
        for length in self.regular_length_list:
            if outsize_length_bytes > length:
                continue
            outsize_length_bytes = length
            outsize_length_bits_index = self.regular_length_list.index(outsize_length_bytes)
            outsize_length_bits = self.regular_length_bits_value[outsize_length_bits_index]

            outsize_length_byte = Byte(outsize_length_bits)
            outsize_length_byte.shift_bits(self.schema_bit_outsize_length_low_bit)
            self.schema_int |= outsize_length_byte.get()

            schema_bytes = Byte(self.schema_int)
            schema_bytes.shift_byte(outsize_length_bytes)
            self.schema_int = schema_bytes.get()
            self.schema_int |= outsize_length_int
            break

    def __remove_number_sign(self):
        return self.number if self.number > 0 else -self.number

    def __data_start_bit(self):
        if self.length_in_schema:
            return self.data_sigh_bit - 1
        return self.data_length_low_bit - 1

    def __get_length_in_bytes(self):
        start_bit = self.__data_start_bit()
        number = self.__remove_number_sign()

        for length in self.regular_length_list:
            maximum_value_byte = Byte()
            maximum_value_byte.get_maximal_value(start_bit, length)
            maximum_value = maximum_value_byte.get()
            if self.__check_variable_is_compliance_border(number, maximum_value):
                self.length_in_bytes = length
                return

        self.length_in_bytes = len(IntStrConverter(number).convert_int_to_data())

        maximum_value_byte = Byte()
        maximum_value_byte.get_maximal_value(start_bit, 1)
        maximum_value = maximum_value_byte.get()
        number_first_byte = ord(IntStrConverter(number).convert_int_to_data()[0])
        if not self.__check_variable_is_compliance_border(number_first_byte, maximum_value):
            self.length_in_bytes += 1

    def __set_in_schema_length_in_data(self):
        length_is_outsize_bit = Byte()
        length_is_outsize_bit.set_bit(self.schema_bit_length_is_outsize)
        self.schema_int |= length_is_outsize_bit.get()

        length_define_in_data_bit = Byte()
        length_define_in_data_bit.set_bit(self.schema_bit_length_define_in_data)
        self.schema_int |= length_define_in_data_bit.get()

    def __put_type_in_schema(self):
        self.schema_int = Type(self).type_index

    def __check_variable_is_compliance_border(self, variable, border):
        if variable > border:
            return False
        return True

    def __put_outsize_length_to_data(self):
        # TODO
        pass

    def __put_sigh_to_data(self):
        if self.number < 0:
            number_byte = Byte()
            number_byte.set_bit(self.data_sigh_bit)
            self.data_int |= number_byte.get()
            self.number *= -1

    def __put_length_to_data(self):
        if self.length_in_bytes > self.max_regular_length:
            self.__put_outsize_length_to_data()
        else:
            self.__put_regular_length_in_data()

    def __put_regular_length_in_data(self):
        length_bits = self.__get_length_bits()
        length_byte = Byte(length_bits)
        length_byte.shift_bits(self.data_length_low_bit)
        self.data_int |= length_byte.get()

    def __make_data(self):
        self.data_int = 0

        if not self.length_in_schema:
            self.__get_length_in_bytes()
            self.__put_length_to_data()


        self.__put_sigh_to_data()
        number_byte = Byte(self.data_int)
        number_byte.shift_byte(self.length_in_bytes-1)
        self.data_int = number_byte.get()

        if self.length_in_schema or self.number <= self.max_regular_number_with_length_in_data:
            return IntStrConverter(self.data_int | self.number).convert_int_to_data(self.length_in_bytes)

        return IntStrConverter(self.data_int).convert_int_to_data() + IntStrConverter(self.number).convert_int_to_data()

    def pack(self, value):
        self.number = value
        return self.__make_schema(), self.__make_data()

    def unpack(self, schema, data):
        self.schema = schema
        self.data = data
        self.__unpack_schema()
        self.__unpack_data()
        return self.number, self.rest_schema, self.rest_data


class Float:
    def __init__(self, variable):
        if isinstance(variable, (float, Decimal)):
           self.number = variable
        if isinstance(variable, str):
            self.data = variable

    def __get_mantissa_and_exponent_from_number(self):
        self.__check_exponent()
        self.__check_dot()
        self.__cut_right_zeros()
        self.mantissa = int(self.mantissa)

    def __cut_right_zeros(self):
        self.exponent += len(self.mantissa) - len(self.mantissa.rstrip('0'))
        self.mantissa = self.mantissa.rstrip('0')

    def __check_exponent(self):
        if 'e' in str(self.number):
            self.mantissa, self.exponent = str(self.number).split('e')
        else:
            self.mantissa = str(self.number)
            self.exponent = '0'

    def __check_dot(self):
        if '.' in self.mantissa:
            self.exponent = int(self.exponent) - len(self.mantissa) + self.mantissa.index('.') + 1
            self.mantissa = self.mantissa.replace('.', '')
        else:
            self.exponent = int(self.exponent)

    def __put_exponent_to_data(self):
        _, exponent_in_data_format = Integer(self.exponent).pack
        self.data = exponent_in_data_format

    def __put_mantissa_to_data(self):
        _, mantissa_in_data_format = Integer(self.mantissa).pack
        self.data += mantissa_in_data_format

    def __get_exponent_from_data(self):
        self.exponent, self.data = Integer(self.data).unpack

    def __get_mantissa_from_data(self):
        self.mantissa, self.data = Integer(self.data).unpack

    def __build_float(self):
        self.number = float(self.mantissa * 10 ** self.exponent)

    @property
    def pack(self):
        self.__get_mantissa_and_exponent_from_number()
        self.__put_exponent_to_data()
        self.__put_mantissa_to_data()
        self.map = Type(self).pack
        return self.map, self.data

    @property
    def unpack(self):
        self.__get_exponent_from_data()
        self.__get_mantissa_from_data()
        self.__build_float()
        return self.number, self.data

class String:
    def __init__(self, variable='', data=''):
        if data == '':
            self.variable = variable
        else:
            self.data = data

    def __check_variable_size_is_correct(self):
        if len(self.data) >= self.length:
            return
        raise Exception('data length less then {}'.format(self.length))

    def __put_length_to_data(self):
        _, length_in_data_format = Integer(len(self.variable)).pack
        self.data = length_in_data_format

    def __put_variablr_to_data(self):
        self.data += self.variable

    def __get_length_in_data(self):
        self.length, self.data = Integer(self.data).unpack

    def __get_variable_from_data(self):
        self.variable = self.data[0: self.length]
        self.data = self.data[self.length: ]

    @property
    def pack(self):
        self.__put_length_to_data()
        self.__put_variablr_to_data()
        self.map = Type(self).pack
        return self.map, self.data

    @property
    def unpack(self):
        self.__get_length_in_data()
        self.__check_variable_size_is_correct()
        self.__get_variable_from_data()
        return self.variable, self.data


class Boolean:
    variables = {
        False: '\x00',
        True:  '\x01',
        None:  '\xff',
    }

    def __init__(self, variable):
        if isinstance(variable, (bool, type(None))):
            self.variable = variable
        if isinstance(variable, str):
            self.data = variable

    @property
    def pack(self):
        self.map = Type(self).pack
        return self.map, self.variables[self.variable]

    @property
    def unpack(self):
        self.variable = self.variables.keys()[
            self.variables.values().index(self.data[0])
        ]
        rest_part_of_data = self.data[1: ]
        return self.variable, rest_part_of_data


class List(IntStrConverter):
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
    equal_objects =   1
    unequal_objects = 0
    bit =             7
    '''

    def pack(self, numer):
        pass

    def unpack(self, data):
        pass


class Contraction:
    def __init__(self, *args):
        self.contractions = []
        for item in args:
            self.contractions.append(item)

    def add_contraction(self, item):
        self.contractions.append(item)

    def pack(self, item):
        pass

    def unpack(self, item):
        pass


class Type:
    '''
    # type bits mark as 1
    11100000
    '''
    type_low_bit = 5

    types_mapping = (
        (int,        Integer),
        (long,       Integer),
        (float,      Float),
        (str,        String),
        (bool,       Boolean),
        (type(None), Boolean),
        (list,       List),
        # set:
        # tuple:
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

    def __init__(self, variable):

        if isinstance(variable, str):
            self.data = variable
        else:
            self.__define_type(variable)

    def __define_type(self, variable):
        for real_type, data_type in self.types_mapping:
            if not isinstance(variable, real_type) and not isinstance(variable, data_type):
                continue
            self.int_data = self.types_index.index(data_type)
            break

    @property
    def type_index(self):
        return self.int_data << self.type_low_bit

    '''
    @property
    def pack(self):
        return self.data
    '''

    @property
    def unpack(self):
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


def tests():
    print 'test start'

    additional_data = '\xff'

    print '-' * 10
    print 'Integer'

    pack_test_cases = [
        #{'value': 0, 'length_in_schema': True, 'schema': '\x00', 'data': '\x00'},
        #{'value': 0x7f, 'length_in_schema': True, 'schema': '\x00', 'data': '\x7f'},
        #{'value': -0x7f, 'length_in_schema': True, 'schema': '\x00', 'data': '\xff'},
        #{'value': 0xff, 'length_in_schema': True, 'schema': '\x04', 'data': '\x00\xff'},
        #{'value': -0xff, 'length_in_schema': True, 'schema': '\x04', 'data': '\x80\xff'},
        #{'value': 0x7fff, 'length_in_schema': True, 'schema': '\x04', 'data': '\x7f\xff'},
        #{'value': -0x7fff, 'length_in_schema': True, 'schema': '\x04', 'data': '\xff\xff'},
        #{'value': 0xffff, 'length_in_schema': True, 'schema': '\x08', 'data': '\x00\x00\xff\xff'},
        #{'value': -0xffff, 'length_in_schema': True, 'schema': '\x08', 'data': '\x80\x00\xff\xff'},
        #{'value': 0x7fffffff, 'length_in_schema': True, 'schema': '\x08', 'data': '\x7f\xff\xff\xff'},
        #{'value': -0x7fffffff, 'length_in_schema': True, 'schema': '\x08', 'data': '\xff\xff\xff\xff'},
        #{'value': 0xffffffff, 'length_in_schema': True, 'schema': '\x0c', 'data': '\x00\x00\x00\x00\xff\xff\xff\xff'},
        #{'value': -0xffffffff, 'length_in_schema': True, 'schema': '\x0c', 'data': '\x80\x00\x00\x00\xff\xff\xff\xff'},
        #{'value': 0x7fffffffffffffff, 'length_in_schema': True, 'schema': '\x0c', 'data': '\x7f\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0x7fffffffffffffff, 'length_in_schema': True, 'schema': '\x0c', 'data': '\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0xffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x00', 'data': '\x00\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0xffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x00', 'data': '\x80\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0x0fffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x00', 'data': '\x0f\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0x0fffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x00', 'data': '\x8f\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0x7fffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x00', 'data': '\x7f\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0x7fffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x00', 'data': '\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0xffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x01', 'data': '\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0xffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x01', 'data': '\x80\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0x7fffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x01', 'data': '\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0x7fffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x01', 'data': '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0xffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x02', 'data': '\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0xffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x02', 'data': '\x80\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0x7fffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x02', 'data': '\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0x7fffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x02', 'data': '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0xffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x03', 'data': '\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0xffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x03', 'data': '\x80\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0x7fffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x03', 'data': '\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0x7fffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x03', 'data': '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0xffffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x04', 'data': '\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0xffffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x04', 'data': '\x80\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0x7fffffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x04', 'data': '\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0x7fffffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x04', 'data': '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0x7fffffffffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x06', 'data': '\x7f\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0x7fffffffffffffffffffffffffffff, 'length_in_schema': True, 'schema': '\x10\x06', 'data': '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0, 'length_in_schema': False, 'schema': '\x18', 'data': '\x00'},
        #{'value': 0x0f, 'length_in_schema': False, 'schema': '\x18', 'data': '\x0f'},
        #{'value': -0x0f, 'length_in_schema': False, 'schema': '\x18', 'data': '\x8f'},
        #{'value': 0xff, 'length_in_schema': False, 'schema': '\x18', 'data': '\x10\xff'},
        #{'value': -0xff, 'length_in_schema': False, 'schema': '\x18', 'data': '\x90\xff'},
        #{'value': 0x0fff, 'length_in_schema': False, 'schema': '\x18', 'data': '\x1f\xff'},
        #{'value': -0x0fff, 'length_in_schema': False, 'schema': '\x18', 'data': '\x9f\xff'},
        #{'value': 0x0fffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\x2f\xff\xff\xff'},
        #{'value': -0x0fffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\xaf\xff\xff\xff'},
        #{'value': 0x0fffffffffffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\x3f\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0x0fffffffffffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\xbf\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0xffffffffffffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\x40\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0xffffffffffffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\xc0\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0xfffffffffffffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\x41\x0f\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0xfffffffffffffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\xc1\x0f\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': 0xffffffffffffffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\x41\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
        #{'value': -0xffffffffffffffffff, 'length_in_schema': False, 'schema': '\x18', 'data': '\xc1\xff\xff\xff\xff\xff\xff\xff\xff\xff'},
    ]

    for case in pack_test_cases:
        schema, data = Integer(length_in_schema=case['length_in_schema']).pack(case['value'])
        if schema != case['schema']:
            print 'Error pack schema', hex(case['value']), schema.encode('hex'), case['schema'].encode('hex')

        if data != case['data']:
            print 'Error pack data', hex(case['value']), data.encode('hex'), case['data'].encode('hex')

    '''

    VARIABLE, SCHEMA, DATA = 0, 1, 2
    additional_data = '\xff'

    print '-' * 10
    print 'Integer'

    pack_test_cases = [
        {'variable': 0, 'schema': '\x00', 'data':'\x00'},
        {'variable': 0x0f, 'schema': '\x00', 'data': '\x0f'},
        {'variable': -0x0f, 'schema': '\x00', 'data': '\x8f'},
        [0xfff, '\x21\xff'],
        [0x1fff, '\x3f\xff'],
        [-0x1fff, '\xbf\xff'],
        [0x1fffffff, '\x5f\xff\xff\xff'],
        [-0x1fffffff, '\xdf\xff\xff\xff'],
        [0x1fffffffffffffff, '\x7f\xff\xff\xff\xff\xff\xff\xff'],
        [-0x1fffffffffffffff, '\xff\xff\xff\xff\xff\xff\xff\xff'],
    ]

    for test_case in pack_test_cases:
        schema, data = Integer(test_case['variable']).pack
        if test_case['schema'] != schema:
            print 'False schema', hex(test_case['variable'])
        if test_case['data']  != data:
            print 'False data', hex(test_case['variable'])

        variable, rest_part_of_data = Integer(test_case['schema'] + tast_case['data'] + additional_data).unpack
        if variable != test_case['variable']:
            print 'False unpack variable', hex(number)
        if rest_part_of_data != additional_data:
            print 'False rest data', hex(number)
    '''
    '''
    try:
        Integer(0x2fffffffffffffff).pack
        print 'False pack exception'
    except:
        pass

    try:
        Integer('\xff').unpack
        print 'False unpack exception'
    except:
        pass

    print '-' * 10
    print 'LongInteger'

    pack_test = [0x2ffffffffffffffff, '\x09\x02\xff\xff\xff\xff\xff\xff\xff\xff']
    _, pack_int = LongInteger(pack_test[0]).pack
    if pack_int != pack_test[1]:
         print 'False pack', hex(pack_test[0])

    long_int, rest_part_of_data =  LongInteger(pack_test[1]+additional_data).unpack
    if long_int != pack_test[0] or rest_part_of_data != additional_data:
        print 'False unpack', hex(pack_test[0])

    pack_test = [-0x2ffffffffffffffff, '\x89\x02\xff\xff\xff\xff\xff\xff\xff\xff']
    _, pack_int = LongInteger(pack_test[0]).pack
    if pack_int != pack_test[1]:
        print 'False pack', hex(pack_test[0])

    long_int, rest_part_of_data =  LongInteger(pack_test[1]+additional_data).unpack
    if long_int != pack_test[0] or rest_part_of_data != additional_data:
        print 'False unpack', hex(pack_test[0]), hex(long_int)

    try:
        LongInteger('').unpack
        print 'False LongInteger unpack empty string exception'
    except:
        pass

    try:
        LongInteger('\x89\x02\xff').unpack
        print 'False LongInteger unpack wrong length string exception'
    except:
        pass

    print '-' * 10
    print 'Float'

    pack_test = [
        [0.0001111111,   '\x8a\x40\x10\xf4\x47'],  # -10 1111111
        [-0.0001111111,  '\x8a\xc0\x10\xf4\x47'],  # -10 -1111111
        [1.00000001,     '\x88\x45\xf5\xe1\x01'],  # -8 100000001
        [-1.00000001,    '\x88\xc5\xf5\xe1\x01'],  # -8 -100000001
        [10000000.0,     '\x07\x01'],              # 7 1
        [-10000000.0,    '\x07\x81'],              # 7 -1
        [1.2323435e-19,  '\x9a\x40\xbc\x0a\x6b'],  # -26 12323435
        [-1.2323435e-19, '\x9a\xc0\xbc\x0a\x6b'],  # -26 -12323435
        [1.1111e+19,     '\x0f\x40\x00\x2b\x67'],  # 15 11111
        [-1.1111e+19,    '\x0f\xc0\x00\x2b\x67'],  # 15 -11111
    ]

    for number, data in pack_test:
        _, pack_float = Float(number).pack
        if pack_float != data:
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
