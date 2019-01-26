#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import json
from decimal import Decimal


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


class IntStrConverter:
    """
    self.number | number to/from converting
    self.data   | hex on int format
    self.string | hex string
    """

    def convert_int_to_str(self):
        hex_string = "{:x}".format(self.data)
        if len(hex_string) % 2: hex_string = "0" + hex_string
        self.string = hex_string.decode("hex")

    def convert_str_to_int(self):
        self.data = int(self.string.encode("hex"), 16)


class Integer(IntStrConverter):
    """
    types:
    small int
    certain length big int

    0b00000000
      sss
      iii
      gzz
      nee

    size bits:
    00 1 byte  +/- 0x1f
    01 2 bytes +/- 0x1fff
    10 4 bytes +/- 0x1fffffff
    11 8 bytes +/- 0x1fffffffffffffff
    """

    # bit
    bit_sign = 7
    bit_size_high = 6
    bit_size_low = 5
    bit_significant_high = 4
    bit_significant_low = 0

    # byte size
    maximum_bytes = 8
    first_byte_maxixum_value = (1 << (bit_significant_high + 1)) - 1
    maximum_value = (first_byte_maxixum_value << (8 * (maximum_bytes - 1))) + \
                             (1 << (8 * (maximum_bytes - 1))) - 1

    def __init__(self, varable):
        if isinstance(varable, (int, long)):
            self.number = varable
        if isinstance(varable, str):
            self.string = varable

    def __check_number_size_is_correct(self):
        if self.number <= self.maximum_value and \
           self.number >= -1 * self.maximum_value:
            return
        raise Exception("requires -{value:x} <= number <= {value:x}".format(value=self.maximum_value))

    def __check_data_size_is_correct(self):
        if len(self.string) >= self.length:
            return
        raise Exception("data length less then {}".format(self.length))

    def __make_mask(self, bit):
        return (1 << bit) << (8 * (self.length - 1))

    def __put_sign_to_string(self):
        self.data = 0
        if self.number < 0:
            self.data = 1 << self.bit_sign

    def __remove_number_sigh(self):
        if self.number < 0:
            self.number *= -1

    def __define_sigh_in_data(self):
        if self.__make_mask(self.bit_sign) & self.data:
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
        self.data |= (self.length << self.bit_size_low)
        self.data <<= (8 * ((2 ** self.length) - 1))

    def __put_number(self):
        self.data |= self.number

    def __define_bytes_length(self):
        size_mask = (1 << self.bit_size_high) | (1 << self.bit_size_low)
        self.length = 2 ** ((ord(self.string[0]) & size_mask) >> self.bit_size_low)

    def __get_string(self):
        rest_part_of_string = self.string[self.length: ]
        self.string = self.string[0: self.length]
        return rest_part_of_string

    def __clean_number(self):
        sigh_mask = self.__make_mask(self.bit_sign)
        size_mask = self.__make_mask(self.bit_size_high) | self.__make_mask(self.bit_size_low)
        number_mask = ~(sigh_mask | size_mask) & (1 << 8 * self.length) - 1
        self.number = self.data & number_mask

    @property
    def pack(self):
        self.__check_number_size_is_correct()
        self.__put_sign_to_string()
        self.__remove_number_sigh()
        self.__set_bytes_length()
        self.__put_number()
        self.convert_int_to_str()
        return self.string

    @property
    def unpack(self):
        self.__define_bytes_length()
        self.__check_data_size_is_correct()
        rest_part_of_data = self.__get_string()
        self.convert_str_to_int()
        self.__clean_number()
        self.__define_sigh_in_data()
        return self.number, rest_part_of_data


class LongInteger(IntStrConverter):
    def __init__(self, varable):
        if isinstance(varable, (int, long)):
            self.number = varable
        if isinstance(varable, str):
            self.string = varable

    def __check_data_size_is_correct(self):
        if len(self.string) >= self.length:
            return
        raise Exception("data length less then {}".format(self.length))

    def __check_string_has_data(self):
        if self.string != "":
            return
        raise Exception("data is empty")

    def __get_sigh(self):
        self.sigh = 1
        if self.number < 0:
            self.sigh = -1

    def __remove_number_sigh(self):
        if self.number < 0:
            self.data *= -1

    def __get_sigh_from_length(self):
        self.sigh = 1
        if self.length < 0:
            self.sigh = -1
            self.length *= -1

    def __set_sigh_of_number(self):
        self.number = self.data * self.sigh

    def __define_length_in_bytes(self):
        self.length = len(self.string)

    def __put_sigh_to_string(self):
        self.length *= self.sigh

    def __add_length(self):
        self.string = Integer(self.length).pack + self.string

    def __get_length_in_string(self):
        self.length, self.string = Integer(self.string).unpack

    def __get_number(self):
        rest_part_of_string = self.string[self.length: ]
        self.string = self.string[0: self.length]
        self.convert_str_to_int()
        return rest_part_of_string

    @property
    def pack(self):
        self.data = self.number
        self.__get_sigh()
        self.__remove_number_sigh()
        self.convert_int_to_str()
        self.__define_length_in_bytes()
        self.__put_sigh_to_string()
        self.__add_length()
        return self.string

    @property
    def unpack(self):
        self.__check_string_has_data()
        self.__get_length_in_string()
        self.__get_sigh_from_length()
        self.__check_data_size_is_correct()
        rest_part_of_string = self.__get_number()
        self.__set_sigh_of_number()
        return self.number, rest_part_of_string


class Float:
    def __init__(self, varable):
        if isinstance(varable, (float, Decimal)):
            self.number = varable
        if isinstance(varable, str):
            self.string = varable

    def __get_mantissa_and_exponent(self):
        self.__check_exponent()
        self.__check_dot()
        self.__cut_right_zeros()
        self.mantissa = int(self.mantissa)

    def __cut_right_zeros(self):
        self.exponent += len(self.mantissa) - len(self.mantissa.rstrip("0"))
        self.mantissa = self.mantissa.rstrip("0")

    def __check_exponent(self):
        if "e" in str(self.number):
            self.mantissa, self.exponent = str(number).split("e")
        else:
            self.mantissa = str(number)
            self.exponent = "0"

    def __check_dot(self):
        if "." in self.mantissa:
            self.exponent = int(self.exponent) - len(self.mantissa) + self.mantissa.index(".") + 1
            self.mantissa = self.mantissa.replace(".", "")
        else:
            self.exponent = int(self.exponent)

    def __add_exponent(self):
        self.string = Integer(self.exponent).pack

    def __add_mantissa(self):
        self.string += Integer(self.mantissa).pack

    @property
    def pack(self):
        self.__get_mantissa_and_exponent()
        self.__add_exponent()
        self.__add_mantissa()
        return self.string

    @property
    def unpack(self):
        pass


class Boolean:
    variables = {
        False: "\x00",
        True:  "\x01",
        None:  "\xff",
    }

    def __init__(self, varable):
        if isinstance(varable, (bool, type(None))):
            self.varable = varable
        if isinstance(varable, str):
            self.string = string

    @property
    def pack(self):
        return variables[self.variable]

    @property
    def unpack(self):
        self.varable = self.variables.keys()[
            self.variables.values().index(self.string[0])
        ]
        rest_string = data[1: ]
        return self.varable, rest_string


class List:
    def pack(self, numer):
        pass

    def unpack(self, data):
        pass


class Dictionary:
    def pack(self, numer):
        pass

    def unpack(self, data):
        pass


class CONTRACTION:
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


if __name__ == "__main__":
    print "test start"

    additional_data = "\xff"

    print "-" * 10
    print "Integer"

    pack_test_cases = [
        [0, "\x00"],
        [0x1f, "\x1f"],
        [-0x1f, "\x9f"],
        [0x1ff, "\x21\xff"],
        [0x1fff, "\x3f\xff"],
        [-0x1fff, "\xbf\xff"],
        [0x1fffffff, "\x5f\xff\xff\xff"],
        [-0x1fffffff, "\xdf\xff\xff\xff"],
        [0x1fffffffffffffff, "\x7f\xff\xff\xff\xff\xff\xff\xff"],
        [-0x1fffffffffffffff, "\xff\xff\xff\xff\xff\xff\xff\xff"],
    ]

    for number, data in pack_test_cases:
        if Integer(number).pack != data:
            print "pack", hex(number)
        unpack_int, rest_data = Integer(data+additional_data).unpack
        if unpack_int != number:
            print "unpack", hex(number)
        if rest_data != additional_data:
            print "rest data", hex(number)

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
    if LongInteger(pack_test[0]).pack != pack_test[1]:
         print "False pack", hex(pack_test[0])

    long_int, rest_data =  LongInteger(pack_test[1]+additional_data).unpack
    if long_int != pack_test[0] or rest_data != additional_data:
        print "False unpack", hex(pack_test[0])

    pack_test = [-0x2ffffffffffffffff, "\x89\x02\xff\xff\xff\xff\xff\xff\xff\xff"]
    if LongInteger(pack_test[0]).pack != pack_test[1]:
        print "False pack", hex(pack_test[0])

    long_int, rest_data =  LongInteger(pack_test[1]+additional_data).unpack
    if long_int != pack_test[0] or rest_data != additional_data:
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
        if Float(number).pack != data:
            print "False pack", number
        float_number, rest_data = Float(data+additional_data).unpack
        if float_number != number:
            print "False unpack", number
        if rest_data != additional_data:
            print "False rest data"

    print "-" * 10
    print "Bool None"

    for variable, data in Boolean.variables.items():
        if Boolean(varable).pack != data:
            print "False pack", variable

    print "-" * 10
    print "test end"


"""
class Float:
    @classmethod
    def man(self, number):
        return Decimal(number).scaleb(-self.exp(number)).normalize()

    @classmethod
    def exp(self, number):
        (sign, digits, exponent) = Decimal(number).as_tuple()
        return len(digits) + exponent - 1
"""
