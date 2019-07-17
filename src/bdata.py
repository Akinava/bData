# -*- coding: utf-8 -*-

import struct
import json
from decimal import Decimal


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__version__ = [0, 0]


struct_format_sign = ['b', 'h', 'i', 'q']
struct_format_unsign = ['B', 'H', 'I', 'Q']
byte_order = '>'


def pack(obj):
    tp = Type().define_by_variable(obj)
    schema, data = tp().pack(obj)
    pack_data = pack_self_define_length(len(schema)) + \
                schema + \
                pack_self_define_length(len(data)) + \
                data
    return pack_data


def unpack(data):
    length, data_tail = unpack_self_define_length(data)
    schema = data_tail[: length]
    data_tail = data_tail[length: ]
    length, data_tail = unpack_self_define_length(data_tail)
    data = data_tail[: length]

    cls = Type().unpack(schema)
    obj = cls()
    value, _, _ = obj.unpack(schema, data)
    return value


def pack_self_define_length(number):
    # bytes    8     4     2    1
    # sign  0xff, 0xfe, 0xfd 0xfc
    if number <= 0xfc:
        return chr(number)
    if number <= 0xffff:
        return '\xfd' + struct.pack(byte_order + 'H', number)
    if number <= 0xffffffff:
        return '\xfe' + struct.pack(byte_order + 'I', number)
    if number <= 0xffffffffffffffff:
        return '\xff' + struct.pack(byte_order + 'Q', number)


def unpack_self_define_length(data):
    sign = ord(data[0])
    data = data[1: ]
    if sign <= 0xfc:
        return sign, data
    if sign == 0xfd:
        return struct.unpak(byte_order + 'H', data[: 2]), data[2: ]
    if sign == 0xfe:
        return struct.unpak(byte_order + 'I', data[: 4]), data[4: ]
    if sign == 0xff:
        return struct.unpak(byte_order + 'Q', data[: 8]), data[8: ]


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



class Byte:
    def __init__(self, variable=0):
        if isinstance(variable, int):
            self.variable = variable
        if isinstance(variable, str):
            self.variable = ord(variable)

    def shift_bits(self, bit_number):
        self.variable <<= bit_number
        return self

    def get(self):
        return chr(self.variable)

    def put_number_on_place(self, number, place):
        self.variable = self.variable|(number<<place)
        return self

    def define_bits_by_number(self, number):
        bits = 0
        while (1<<bits)-1 < number:
            bits += 1
        return bits

    def check_bit(self, bit_number):
        return self.variable & (1 << bit_number)

    def number_or(self, byte):
        self.variable |= byte
        return self

    def get_number_by_edge(self, low_bit, length):
        return (self.variable >> low_bit) & ((1 << length) - 1)

    def char_and(self, char):
        self.variable & ord(char)
        return self


class SchemaHandler:
    def pack_sign_of_size(self, schema, sign_of_size):
        return Byte(schema).put_number_on_place(
            number=sign_of_size,
            place=Type.schema_bit_length_bit).get()

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
        self.sign_of_size = define_hex_size_of_sign_number(self.variable)

    def __pack_type(self):
        self.schema = Type().pack(self)

    def __pack_sign_of_size(self):
        self.schema = SchemaHandler().pack_sign_of_size(self.schema, self.sign_of_size)

    def __pack_schema(self):
        self.__pack_type()
        self.__pack_sign_of_size()

    def __pack_data(self):
        self.__define_sign_of_size()
        fmt = byte_order+struct_format_sign[self.sign_of_size]
        self.data = struct.pack(fmt, self.variable)

    def pack(self, number):
        self.variable = number
        self.__pack_data()
        self.__pack_schema()
        return self.schema, self.data

    def __unpack_sign_of_size(self):
        self.sign_of_size = SchemaHandler().unpack_sign_of_size(self.schema[0])

    def __unpack_schema(self):
        self.__unpack_sign_of_size()
        self.schema_tail = self.schema[1:]
        self.schema = self.schema[0]

    def __unpack_data(self):
        data_lengh = 2**self.sign_of_size
        fmt = byte_order + struct_format_sign[self.sign_of_size]
        self.variable, = struct.unpack(fmt, self.data[:data_lengh])
        self.data_tail = self.data[data_lengh:]

    def unpack(self, schema, data):
        self.schema = schema
        self.data = data
        self.__unpack_schema()
        self.__unpack_data()
        return self.variable, self.schema_tail, self.data_tail

    def get_schema(self):
        return self.schema


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
        self.schema = SchemaHandler().pack_sign_of_size(self.schema, self.sign_of_mantissa_size)

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
        self.schema = self.schema[0]

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

    def get_schema(self):
        return self.schema


class String:
    def __check_variable_size_is_correct(self):
        if len(self.data) >= self.length:
            return
        raise Exception('data size less then {}'.format(self.length))

    def __pack_type(self):
        self.schema = Type().pack(self)

    def __pack_sign_of_size(self):
        self.schema = SchemaHandler().pack_sign_of_size(self.schema, self.sign_of_size)

    def __pack_length(self):
        fmt = byte_order+struct_format_unsign[self.sign_of_size]
        self.schema += struct.pack(fmt, self.length)

    def __define_sign_of_size(self):
        self.length = len(self.variable)
        self.sign_of_size = define_hex_size_of_unsign_number(self.length)

    def __pack_schema(self):
        self.__pack_type()
        self.__pack_sign_of_size()
        self.__pack_length()

    def __pack_data(self):
        self.__define_sign_of_size()
        self.data = self.variable

    def pack(self, variable):
        self.variable = variable
        self.__pack_data()
        self.__pack_schema()
        return self.schema, self.data

    def __unpack_sign_of_size(self):
        self.sign_of_size = SchemaHandler().unpack_sign_of_size(self.schema[0])

    def __unpack_length(self):
        fmt = byte_order + struct_format_unsign[self.sign_of_size]
        schema_size_length = 2 ** self.sign_of_size
        length_bits_start = 1
        length_bits_end = length_bits_start + schema_size_length
        length_bits = self.schema[length_bits_start: length_bits_end]
        self.schema_tail = self.schema[length_bits_end: ]
        self.length, = struct.unpack(fmt, length_bits)
        self.schema = self.schema[ :length_bits_end]

    def __unpack_schema(self):
        self.__unpack_sign_of_size()
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

    def get_schema(self):
        return self.schema


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

    def get_schema(self):
        self.schema[0]


class List:
    '''
    bit
      7 unequeal/equal type objects                    0/1
    '''

    def __pack_data(self):
        self.__define_sign_of_size()
        self.__pack_list()
        self.__join_data()

    def __join_data(self):
        self.data = "".join(self.data_list)

    def __pack_list(self):
        self.schema_list, self.data_list = [], []
        for item in self.variable:
            self.__pack_obj(item)

    def __pack_obj(self, item):
        tp = Type().define_by_variable(item)
        schema, data = tp().pack(item)
        self.schema_list.append(schema)
        self.data_list.append(data)

    def __define_sign_of_size(self):
        self.length = len(self.variable)
        self.sign_of_size = define_hex_size_of_unsign_number(self.length)

    def __pack_schema(self):
        self.__pack_type()
        self.__pack_sign_of_size()
        self.__compress_items_schema()
        self.__pack_length()
        self.__pack_type_items()

    def __pack_sign_of_size(self):
        self.schema = SchemaHandler().pack_sign_of_size(self.schema, self.sign_of_size)

    def __pack_length(self):
        fmt = byte_order+struct_format_unsign[self.sign_of_size]
        self.schema += struct.pack(fmt, self.length)

    def __pack_type(self):
        self.schema = Type().pack(self)

    def __pack_type_items(self):
        self.schema += ''.join(self.schema_list)

    def __set_type_of_variables_is_equal(self):
        self.schema = Byte(self.schema).put_number_on_place(
            number = Type.items_are_equal,
            place = Type.schema_equal_bit
            ).get()

    def __compress_items_schema(self):
        if len(self.schema_list) < 2:
            return

        if len(list(set(self.schema_list))) == 1:
            self.schema_list = [self.schema_list[0]]
            self.__set_type_of_variables_is_equal()

    def pack(self, variable):
        self.variable = variable
        self.__pack_data()
        self.__pack_schema()
        return self.schema, self.data

    def __unpack_schema(self):
        self.__check_schema_compressed()
        self.__unpack_sign_of_size()
        self.__unpack_length()

    def __check_schema_compressed(self):
        self.items_are_equal = False
        if Byte(self.schema[0]).check_bit(Type.schema_equal_bit) == Type.items_are_equal:
            self.items_are_equal = True

    def __unpack_length(self):
        fmt = byte_order + struct_format_unsign[self.sign_of_size]
        schema_size_length = 2 ** self.sign_of_size
        length_bits_start = 1
        length_bits_end = length_bits_start + schema_size_length
        length_bits = self.schema[length_bits_start: length_bits_end]
        self.schema_tail = self.schema[length_bits_end: ]
        self.length, = struct.unpack(fmt, length_bits)
        self.schema = self.schema[ :length_bits_end]

    def __unpack_sign_of_size(self):
        self.sign_of_size = SchemaHandler().unpack_sign_of_size(self.schema[0])

    def __uncompress_items_schema(self, item_index, obj):
        last_index = self.length - 1
        if self.items_are_equal and item_index != last_index:
            self.schema_tail = obj.get_schema() + self.schema_tail

    def __unpack_obj(self):
        cls = Type().unpack(self.schema_tail)
        obj = cls()
        value, self.schema_tail, self.data_tail = obj.unpack(self.schema_tail, self.data_tail)
        self.variable.append(value)
        return obj

    def __unpack_data(self):
        self.data_tail = self.data
        self.variable = []
        for item_index in xrange(self.length):
            obj = self.__unpack_obj()
            self.__uncompress_items_schema(item_index, obj)

    def unpack(self, schema, data):
        self.schema = schema
        self.data = data
        self.__unpack_schema()
        self.__unpack_data()
        return self.variable, self.schema_tail, self.data_tail

    def get_schema(self):
        return self.schema


class Dictionary:
    '''
    keys type and values type are unequal        = 0
    keys type are equal                          = 1
    value type are equal                         = 2
    keys type are equal and value type are equal = 3
    '''
    def __pack_data(self):
        self.__define_sign_of_size()
        self.__pack_dict()
        self.__join_data()

    def __join_data(self):
        self.data = "".join(self.data_list)

    def __define_sign_of_size(self):
        self.length = len(self.variable)
        self.sign_of_size = define_hex_size_of_unsign_number(self.length)

    def __pack_dict(self):
        self.schema_keys_list, self.schema_values_list, self.data_list = [], [], []
        for item in self.variable.items():
            self.__pack_obj(item)

    def __pack_obj(self, item):
        key, value = item
        schema, data = self.__pack_item(key)
        self.schema_keys_list.append(schema)
        self.data_list.append(data)
        schema, data = self.__pack_item(value)
        self.schema_values_list.append(schema)
        self.data_list.append(data)

    def __pack_item(self, item):
        tp = Type().define_by_variable(item)
        return tp().pack(item)

    def __pack_schema(self):
        self.__pack_type()
        self.__pack_sign_of_size()
        self.__define_compress_value()
        self.__compress_keys_schema()
        self.__compress_values_schema()
        self.__pack_compress_flag()
        self.__pack_length()
        self.__pack_type_items()

    def __pack_type_items(self):
        if self.compress_flag != Type.obj_are_unequal:
            self.__pack_first_obj_schema()
        self.__pack_rest_obj_schema()

    def __pack_first_obj_schema(self):
        self.schema += (self.schema_keys_list[0] + self.schema_values_list[0])
        self.schema_keys_list = self.schema_keys_list[1: ]
        self.schema_values_list = self.schema_values_list[1: ]

    def __pack_compress_schema(self, schema_list, index):
        if index < len(schema_list):
            return schema_list[index]
        return ''

    def __pack_rest_obj_schema(self):
        for index in xrange(len(self.schema_keys_list or self.schema_values_list)):
            key_schema = self.__pack_compress_schema(self.schema_keys_list, index)
            val_schema = self.__pack_compress_schema(self.schema_values_list, index)
            self.schema += (key_schema + val_schema)

    def __pack_length(self):
        fmt = byte_order+struct_format_unsign[self.sign_of_size]
        self.schema += struct.pack(fmt, self.length)

    def __pack_compress_flag(self):
        self.schema = Byte(self.schema).put_number_on_place(
            number = self.compress_flag,
            place = Type.schema_equal_bit
            ).get()

    def __define_compress_value(self):
        self.compress_flag = 0

    def __pack_type(self):
        self.schema = Type().pack(self)

    def __pack_sign_of_size(self):
        self.schema = SchemaHandler().pack_sign_of_size(self.schema, self.sign_of_size)

    def __compress_keys_schema(self):
        self.schema_keys_list = self.__compress_obj_schema(self.schema_keys_list, Type.keys_are_equal)

    def __compress_values_schema(self):
        self.schema_values_list = self.__compress_obj_schema(self.schema_values_list, Type.values_are_equal)

    def __compress_obj_schema(self, obj_list, obj_equal_flag):
        if len(obj_list) < 2 or len(list(set(obj_list))) != 1:
            return obj_list
        self.__set_obj_is_equal(obj_equal_flag)
        return [obj_list[0]]

    def __set_obj_is_equal(self, obj_equal_flag):
        self.compress_flag += obj_equal_flag

    def pack(self, variable):
        self.variable = variable
        self.__pack_data()
        self.__pack_schema()
        return self.schema, self.data

    def __unpack_schema(self):
        self.__check_schema_compressed()
        self.__unpack_sign_of_size()
        self.__unpack_length()

    def __check_schema_compressed(self):
        length_of_bits = Byte().define_bits_by_number(Type.keys_are_equal + Type.values_are_equal)
        sign_of_compressed_schema = Byte(self.schema[0]).get_number_by_edge(Type.schema_equal_bit, length_of_bits)
        self.keys_are_equal = True if sign_of_compressed_schema & Type.keys_are_equal else False
        self.values_are_equal = True if sign_of_compressed_schema & Type.values_are_equal else False

    def __unpack_sign_of_size(self):
        self.sign_of_size = SchemaHandler().unpack_sign_of_size(self.schema[0])

    def __unpack_length(self):
        fmt = byte_order + struct_format_unsign[self.sign_of_size]
        schema_size_length = 2 ** self.sign_of_size
        length_bits_start = 1
        length_bits_end = length_bits_start + schema_size_length
        length_bits = self.schema[length_bits_start: length_bits_end]
        self.schema_tail = self.schema[length_bits_end: ]
        self.length, = struct.unpack(fmt, length_bits)
        self.schema = self.schema[ :length_bits_end]

    def __unpack_data(self):
        self.data_tail = self.data
        self.variable = {}
        for item_index in xrange(self.length):
            self.__uncompress_keys_schema(item_index)
            key_obj = self.__unpack_obj()
            self.__uncompress_values_schema(item_index)
            val_obj = self.__unpack_obj()
            self.__append_variable(key_obj, val_obj)
            self.__save_obj_type(key_obj, val_obj, item_index)


    def __append_variable(self, key_obj, val_obj):
        self.variable[key_obj.variable] = val_obj.variable

    def __uncompress_keys_schema(self, item_index):
        if self.keys_are_equal is False or item_index == 0:
            return
        self.schema_tail = self.compressed_keys_schema + self.schema_tail

    def __uncompress_values_schema(self, item_index):
        if self.values_are_equal is False or item_index == 0:
            return
        self.schema_tail = self.compressed_values_schema + self.schema_tail

    def __save_obj_type(self, key_obj, val_obj, item_index):
        if item_index != 0:
            return
        if self.keys_are_equal is True:
            self.compressed_keys_schema = key_obj.get_schema()
        if self.values_are_equal is True:
            self.compressed_values_schema = val_obj.get_schema()

    def __unpack_obj(self):
        cls = Type().unpack(self.schema_tail)
        obj = cls()
        _, self.schema_tail, self.data_tail = obj.unpack(self.schema_tail, self.data_tail)
        return obj

    def unpack(self, schema, data):
        self.schema = schema
        self.data = data
        self.__unpack_schema()
        self.__unpack_data()
        return self.variable, self.schema_tail, self.data_tail

    def get_schema(self):
        self.schema


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
    schema_type_bit = 5
    schema_bit_length_bit = 3
    schema_max_sign_of_size = 3

    obj_are_unequal = 0
    items_are_equal = 1
    keys_are_equal = 1
    values_are_equal = 2
    schema_equal_bit = 0

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
    )

    def define_by_variable(self, variable):
        for tp_real, tp_bdata in self.types_mapping:
            if isinstance(variable, tp_real):
                return tp_bdata
        raise Exception("Error: can't define type of data {}".format(type(variable)))

    def pack(self, obj):
        for class_type in self.types_index:
            if isinstance(obj, class_type):
                obj_index = self.types_index.index(class_type)
                return Byte(obj_index).shift_bits(Type.schema_type_bit).get()
        raise Exception('wrong type data {}'.format(obj))

    def unpack(self, schema):
        length_of_bits = Byte().define_bits_by_number(len(Type.types_index))
        type_index = Byte(schema[0]).get_number_by_edge(Type.schema_type_bit, length_of_bits)
        return Type.types_index[type_index]
