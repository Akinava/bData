#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import json
from decimal import Decimal
from collections import namedtuple


__author__ = "Akinava"
__author_email__ = "akinava@gmail.com"
__version__ = [0, 0]


class NotFound:
    def __str__(self):
        return "NOT_FIND"

    def __unicode__(self):
        return "NOT_FIND"

    def __repr__(self):
        return "NOT_FIND"

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
    def __init__(self):
        self.variable = 0

    def get(self):
        return self.variable

    def set_bit(bit_number):
        self.variable |= 1 << bit_number

    def unset_bit(bit_number):
        self.variable &= ~(1 << bit_number) & (1 << 8) - 1

    def get_mask(self, mask_size_in_byte=1):
        return ~self.variable & (1 << 8 * mask_size_in_byte) - 1

    def shift_byte(self, shift_size):
        self.variable <<= 8 * shift_size


class IntStrConverter:
    """
    self.number   | number to/from converting
    self.int_data | hex on int format
    self.data     | hex string
    """
    def __init__(self, variable):
        self.variable = variable

    def convert_int_to_data(self):
        hex_string = "{:x}".format(self.variable)
        if len(hex_string) % 2: hex_string = "0" + hex_string
        return hex_string.decode("hex")

    def convert_data_to_int(self):
        return int(self.variable.encode("hex"), 16)


class Integer(IntStrConverter):
    schema_low_mapping_bit = 0
    schema_option = namedtuple(
        'schema', [
            'bytes_length',
            'lenth_in_schema',
    ])

    schema_bits_mapping = {
        0: schema_option(1, True),
        1: schema_option(2, True),
        2: schema_option(4, True),
        3: schema_option(8, True),
        4: schema_option(0, True),
        5: schema_option(0, False),
        # 6: reserved,
        # 7: reserved,
    }

    # data bits
    data_sigh_bit = 7
    data_low_size_bits = 4
    """

    """
    first_byte_maxixum_value = (1 << (data_significant_high_bit + 1)) - 1
    maximum_value = (first_byte_maxixum_value << (8 * (maximum_bytes - 1))) + \
                             (1 << (8 * (maximum_bytes - 1))) - 1
    """
    def __init__(self, variable, length_in_schema=True):
        if isinstance(variable, (int, long)):
            self.number = variable
        if isinstance(variable, str):
            self.data = variable
        self.length_in_schema = length_in_schema

    def __make_schema(self):
        self.schema = Type(self).type_index
        if self.length_in_schema:

        self.__define_length_in_bytes()


    def __define_length_in_bytes(self):
        maximum_value_in_first_byte = 0


    @property
    def pack(self):
        return self.__make_schema(), self.__make_data()

    """
    def __check_number_size_is_correct(self):
        if self.number <= self.maximum_value and \
           self.number >= -1 * self.maximum_value:
            return
        raise Exception("requires -{value:x} <= number <= {value:x}".format(value=self.maximum_value))

    def __check_data_size_is_correct(self):
        if len(self.data) >= self.length:
            return
        raise Exception("data length less then {}".format(self.length))

    def __make_mask(self, bit):
        return (1 << bit) << (8 * (self.length - 1))

    def __put_sign_to_data(self):
        self.int_data = 0
        if self.number < 0:
            self.int_data = 1 << self.bit_sign

    def __remove_number_sigh(self):
        if self.number < 0:
            self.number *= -1

    def __define_sigh_in_data(self):
        if self.__make_mask(self.bit_sign) & self.int_data:
            self.number *= -1

    def __define_number_length_in_bytes(self):
        self.length = 0
        max_value = self.first_byte_maxixum_value
        while self.number > max_value:
            self.length += 1
            max_value = (self.first_byte_maxixum_value << 8 * ((2 ** self.length) - 1)) + \
                        (1 << 8 * ((2 ** self.length) - 1)) - 1

    def __set_bytes_length(self):
        self.__define_number_length_in_bytes()
        self.int_data |= (self.length << self.bit_size_low)
        self.int_data <<= (8 * ((2 ** self.length) - 1))

    def __put_number(self):
        self.int_data |= self.number

    def __define_bytes_length(self):
        size_mask = (1 << self.bit_size_high) | (1 << self.bit_size_low)
        self.length = 2 ** ((ord(self.data[0]) & size_mask) >> self.bit_size_low)

    def __get_data(self):
        rest_part_of_data = self.data[self.length: ]
        self.data = self.data[0: self.length]
        return rest_part_of_data

    def __clean_number(self):
        sigh_mask = self.__make_mask(self.bit_sign)
        size_mask = self.__make_mask(self.bit_size_high) | self.__make_mask(self.bit_size_low)
        number_mask = ~(sigh_mask | size_mask) & (1 << 8 * self.length) - 1
        self.number = self.int_data & number_mask

    @property
    def pack(self):
        self.__check_number_size_is_correct()
        self.__put_sign_to_data()
        self.__remove_number_sigh()
        self.__set_bytes_length()
        self.__put_number()
        self.convert_int_to_data()
        self.map = Type(self).pack
        return self.map, self.data

    @property
    def unpack(self):
        self.__define_bytes_length()
        self.__check_data_size_is_correct()
        rest_part_of_data = self.__get_data()
        self.convert_data_to_int()
        self.__clean_number()
        self.__define_sigh_in_data()
        return self.number, rest_part_of_data


class LongInteger(IntStrConverter):
    def __init__(self, variable):
        if isinstance(variable, (int, long)):
            self.number = variable
        if isinstance(variable, str):
            self.data = variable

    def __check_data_size_is_correct(self):
        if len(self.data) >= self.length:
            return
        raise Exception("data length less then {}".format(self.length))

    def __check_data_has_data(self):
        if self.data != "":
            return
        raise Exception("data is empty")

    def __get_number_sigh(self):
        self.sigh = 1
        if self.number < 0:
            self.sigh = -1

    def __remove_int_data_sigh(self):
        if self.number < 0:
            self.int_data *= -1

    def __get_sigh_from_length(self):
        self.sigh = 1
        if self.length < 0:
            self.sigh = -1

    def __remove_sigh_from_length(self):
        self.length *= self.sigh

    def __set_sigh_of_number(self):
        self.number = self.int_data * self.sigh

    def __define_length_in_bytes(self):
        self.length = len(self.data)

    def __put_sigh_to_data(self):
        self.length *= self.sigh

    def __put_length_to_data(self):
        _, length_pack = Integer(self.length).pack
        self.data = length_pack + self.data

    def __get_length_in_data(self):
        self.length, self.data = Integer(self.data).unpack

    def __get_number(self):
        rest_part_of_data = self.data[self.length: ]
        self.data = self.data[0: self.length]
        self.convert_data_to_int()
        return rest_part_of_data

    @property
    def pack(self):
        self.int_data = self.number
        self.__get_number_sigh()
        self.__remove_int_data_sigh()
        self.convert_int_to_data()
        self.__define_length_in_bytes()
        self.__put_sigh_to_data()
        self.__put_length_to_data()
        self.map = Type(self).pack
        return self.map, self.data

    @property
    def unpack(self):
        self.__check_data_has_data()
        self.__get_length_in_data()
        self.__get_sigh_from_length()
        self.__remove_sigh_from_length()
        self.__check_data_size_is_correct()
        rest_part_of_data = self.__get_number()
        self.__set_sigh_of_number()
        return self.number, rest_part_of_data


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
        self.exponent += len(self.mantissa) - len(self.mantissa.rstrip("0"))
        self.mantissa = self.mantissa.rstrip("0")

    def __check_exponent(self):
        if "e" in str(self.number):
            self.mantissa, self.exponent = str(self.number).split("e")
        else:
            self.mantissa = str(self.number)
            self.exponent = "0"

    def __check_dot(self):
        if "." in self.mantissa:
            self.exponent = int(self.exponent) - len(self.mantissa) + self.mantissa.index(".") + 1
            self.mantissa = self.mantissa.replace(".", "")
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
    def __init__(self, variable="", data=""):
        if data == "":
            self.variable = variable
        else:
            self.data = data

    def __check_variable_size_is_correct(self):
        if len(self.data) >= self.length:
            return
        raise Exception("data length less then {}".format(self.length))

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
        False: "\x00",
        True:  "\x01",
        None:  "\xff",
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
        self.map, self.data = "", ""
        for items in self.variable:
            self.__pack_item(items)
        return self.map, self.data

    @property
    def unpack(self):
        return self.variable


class Dictionary:
    """
    equal_objects =   1
    unequal_objects = 0
    bit =             7
    """

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


class Type(IntStrConverter):
    """
    # type bits mark as 1
    11100000
    """
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
            self.convert_int_to_data()
            break

    @property
    def type_index(self):
        self.int_data << self.type_low_bit

    """
    @property
    def pack(self):
        return self.data
    """

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

    """
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


    """



    #    2: int,          # positiv integer
    #    3: int,          # negativ integer
    #    4: int,          # positiv integet positiv exp
    #    5: int,          # negativ integer positiv exp
    #    6: int,          # positiv integet negativ exp
    #    7: int,          # negativ integer negativ exp

    def pack(self, value):
        if not isinstance(value, (int, long, float, Decimal)):
            print "Error: not a number"
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
        "\x00": False,
        "\x01": True,
    }

    @classmethod
    def pack(self, x):
        return {v: k for k, v in BBOOL.TYPES.items()}[x]

    @classmethod
    def unpack(self, x):
        return BBOOL.TYPES[x]


class BDATA:
    def __init__(self, data, force=True):
        self.__dict__["__path"] = []
        self.__dict__["__force"] = force

        if isinstance(data, (str, unicode)):
            self.__parse_bin(data)
            return

        if isinstance(data, (dict, list)):
            self.__dict__["__data"] = data
            return

    def __getattr__(self, attr):
        self.__dict__["__path"].append(attr)
        return self

    def __getitem__(self, item):
        self.__dict__["__path"].append(item)
        return self

    def __setattr__(self, attr, value):
        self.__dict__["__path"].append(attr)
        if not self.__get_node() is not_find or self.__dict__["__force"] is True:
            self.__dict__["__data"] = self.__put_node(value)
        self.__dict__["__path"] = []

    def __setitem__(self, item, value):
        self.__dict__["__path"].append(item)
        if not self.__get_node() is not_find or self.__dict__["__force"] is True:
            self.__dict__["__data"] = self.__put_node(value)
        self.__dict__["__path"] = []

    def __eq__(self, item):
        return self.__dict__["__data"] == item

    def __str__(self):
        return json.dumps(self.__dict__["__data"], indent=2)

    def __unicode__(self):
        return json.dumps(self.__dict__["__data"], indent=2)

    def __repr__(self):
        return json.dumps(self.__dict__["__data"], indent=2)

    def __call__(self):
        return not_find

    def __check_data_key(self, data, key):
        if isinstance(data, dict) and key in data.keys() or \
           isinstance(data, (list, tuple)) and isinstance(key, (int, long)) and len(data) > key:
            return
        return not_find

    def __get_node(self):
        data = self.__dict__["__data"]
        for x in self.__dict__["__path"]:
            check = self.__check_data_key(data, x)
            if check is not_find:
                return not_find
            data = data[x]
        return data

    def __put_node(self, value, obj=not_find, path=None):
        if obj is not_find:
            obj = self.__dict__["__data"]
        if path is None:
            path = self.__dict__["__path"]

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
        self.__dict__["__path"] = []
        if isinstance(copy, (dict, list)):
            return BDATA(copy)
        if copy is not_find:
            return bad_response
        return copy

    @property
    def _bin(self):
        return ""

    @property
    def _json(self):
        js = self.__get_node()
        self.__dict__["__path"] = []
        return js


def tests():
    print "test start"

    VARIABLE, SCHEMA, DATA = 0, 1, 2
    additional_data = "\xff"

    print "-" * 10
    print "Integer"

    pack_test_cases = [
        [0, "\x00", "\x00"],
        [0x0f, "\x00", "\x0f"],
        [-0x0f, "\x00", "\x8f"],
        [0xfff, "\x21\xff"],
        [0x1fff, "\x3f\xff"],
        [-0x1fff, "\xbf\xff"],
        [0x1fffffff, "\x5f\xff\xff\xff"],
        [-0x1fffffff, "\xdf\xff\xff\xff"],
        [0x1fffffffffffffff, "\x7f\xff\xff\xff\xff\xff\xff\xff"],
        [-0x1fffffffffffffff, "\xff\xff\xff\xff\xff\xff\xff\xff"],
    ]

    for number, data in pack_test_cases:
        _, pack_int = Integer(number).pack
        if pack_int != data:
            print "False pack", hex(number), Integer(number).pack
        unpack_int, rest_part_of_data = Integer(data+additional_data).unpack
        if unpack_int != number:
            print "False unpack", hex(number)
        if rest_part_of_data != additional_data:
            print "False rest data", hex(number)

    """
    try:
        Integer(0x2fffffffffffffff).pack
        print "False pack exception"
    except:
        pass

    try:
        Integer("\xff").unpack
        print "False unpack exception"
    except:
        pass

    print "-" * 10
    print "LongInteger"

    pack_test = [0x2ffffffffffffffff, "\x09\x02\xff\xff\xff\xff\xff\xff\xff\xff"]
    _, pack_int = LongInteger(pack_test[0]).pack
    if pack_int != pack_test[1]:
         print "False pack", hex(pack_test[0])

    long_int, rest_part_of_data =  LongInteger(pack_test[1]+additional_data).unpack
    if long_int != pack_test[0] or rest_part_of_data != additional_data:
        print "False unpack", hex(pack_test[0])

    pack_test = [-0x2ffffffffffffffff, "\x89\x02\xff\xff\xff\xff\xff\xff\xff\xff"]
    _, pack_int = LongInteger(pack_test[0]).pack
    if pack_int != pack_test[1]:
        print "False pack", hex(pack_test[0])

    long_int, rest_part_of_data =  LongInteger(pack_test[1]+additional_data).unpack
    if long_int != pack_test[0] or rest_part_of_data != additional_data:
        print "False unpack", hex(pack_test[0]), hex(long_int)

    try:
        LongInteger("").unpack
        print "False LongInteger unpack empty string exception"
    except:
        pass

    try:
        LongInteger("\x89\x02\xff").unpack
        print "False LongInteger unpack wrong length string exception"
    except:
        pass

    print "-" * 10
    print "Float"

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
            print "False pack", number, Float(number).pack
        float_number, rest_part_of_data = Float(data+additional_data).unpack
        if str(float_number) != str(number):
            print "False unpack", number
        if rest_part_of_data != additional_data:
            print "False rest data"

    print "-" * 10
    print "Bool None"

    for variable, data in Boolean.variables.items():
        _, pack_bool = Boolean(variable).pack
        if pack_bool != data:
            print "False pack", variable

        unpack_variable, rest_part_of_data = Boolean(data+additional_data).unpack
        if unpack_variable != variable:
            print "False unpack", number
        if rest_part_of_data != additional_data:
            print "False rest data"

    print "-" * 10
    print "String"

    variables = [
        ['123qweQWE', '\x09123qweQWE'],
        ['йух123qwe', '\x0cйух123qwe'],
    ]

    for variable, data in variables:
        _, pack_str = String(variable).pack
        if pack_str != data:
            print "False pack", [variable, String(variable).pack]

        unpack_variable, rest_part_of_data = String(data=data+additional_data).unpack
        if unpack_variable != variable:
            print "False unpack", number
        if rest_part_of_data != additional_data:
            print "False rest data"


    print "-" * 10
    print "List"

    variables = [
        #              map                 data
        [[1, 2, "3"], "\x05\x03\x00\x00\x03\x01\x02\x01\x33"],
    ]

    for variable, data in variables:
        print variable
        data_map, data = List(variable).pack
        if data_map + data != data:
            print "False pack", variable, (data_map + data).encode("hex")

        unpack_variable, rest_part_of_data = List(data+additional_data).unpack
        if unpack_variable != variable:
            print "False unpack", variable, unpack_variable
        if rest_part_of_data != additional_data:
            print "False rest data"
    """

    print "-" * 10
    print "test end"


if __name__ == "__main__":
    tests()
