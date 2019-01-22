#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from decimal import Decimal
import struct


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


class Integer:
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

    @classmethod
    def __check_number_size_is_correct(self):
        if self.number <= self.maximum_value and \
           self.number >= -1 * self.maximum_value:
            return
        raise Exception('requires -{value:x} <= number <= {value:x}'.format(value=self.maximum_value))

    @classmethod
    def __read_bit(self, byte, bit_number):
        return 1 if byte & (1 << (bit_number)) else 0

    @classmethod
    def __read_bits(self, byte, hight_bit, low_bit):
        result = 0
        for bit_number in range(hight_bit, low_bit-1, -1):
            print bit_number, self.__read_bit(byte, bit_number)
            result <<= 1
            if self.__read_bit(byte, bit_number):
                result |= 1
            print result
        return result

    @classmethod
    def __set_sign(self):
        if self.number < 0:
            return 1 << self.bit_sign
        return 0

    @classmethod
    def __remove_sigh(self):
        if self.number < 0:
            self.number *= -1

    @classmethod
    def __define_number_length_in_bytes(self):
        length = 0
        max_value = self.first_byte_maxixum_value
        while self.number > max_value:
            length += 1
            max_value = (self.first_byte_maxixum_value << 8 * ((2 ** length) - 1)) + \
                        (1 << 8 * ((2 ** length) - 1)) - 1
        return length

    @classmethod
    def __set_bytes_length(self):
        length = self.__define_number_length_in_bytes()
        self.data |= (length << self.bit_size_low)
        self.data <<= (8 * ((2 ** length) - 1))

    @classmethod
    def __put_number(self):
        self.data |= self.number

    @classmethod
    def __convert_number_to_hex(self):
        self.data = '{:02x}'.format(self.data).decode('hex')

    @classmethod
    def __define_bytes_length(self):
        size_mask = (1 << self.bit_size_high) + (1 << self.bit_size_low)
        return 2 ** ((ord(self.data[0]) & size_mask) >> self.bit_size_low)

    @classmethod
    def __get_rest_part(self, length):
        return self.data[length: ]

    @classmethod
    def __get_number(self, length):
        number_mask = ~((1 << self.bit_sign) + \
                        (1 << self.bit_size_high) + \
                        (1 << self.bit_size_low)) & 0xff
        self.number = ord(self.data[0]) & number_mask

        for index in xrange(1, length):
            self.number <<= 8
            self.number |= ord(self.data[index])

    @classmethod
    def __get_sigh(self):
        self.number *= -1 if ord(self.data[0]) & (1 << self.bit_sign) else 1

    @classmethod
    def __check_data_size_is_correct(self, length):
        if len(self.data) >= length:
            return
        raise Exception('data length less then {}'.format(length))


    @classmethod
    def pack(self, number):
        self.number = number
        self.__check_number_size_is_correct()
        self.data = self.__set_sign()
        self.__remove_sigh()
        self.__set_bytes_length()
        self.__put_number()
        self.__convert_number_to_hex()
        return self.data

    @classmethod
    def unpack(self, data):
        self.data = data
        length = self.__define_bytes_length()
        self.__check_data_size_is_correct(length)
        self.__get_number(length)
        self.__get_sigh()
        return self.number, self.__get_rest_part(length)


class LongInteger:
    def pack(self, numer):
        pass

    def unpack(self, data):
        pass


class Float:
    def pack(self, numer):
        pass

    def unpack(self, data):
        pass

class Boolean:
    def pack(self, numer):
        pass

    def unpack(self, data):
        pass


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
    """
    # test Integer
    pack_test_cases = [
        [0, '\x00'],
        [0x1f, '\x1f'],
        [-0x1f, '\x9f'],
        [0x1fff, '\x3f\xff'],
        [-0x1fff, '\xbf\xff'],
        [0x1fffffff, '\x5f\xff\xff\xff'],
        [-0x1fffffff, '\xdf\xff\xff\xff'],
        [0x1fffffffffffffff, '\x7f\xff\xff\xff\xff\xff\xff\xff'],
        [-0x1fffffffffffffff, '\xff\xff\xff\xff\xff\xff\xff\xff'],
    ]

    additional_data = '\xff'
    for number, data in pack_test_cases:
        print Integer.pack(number) == data
        unpack_int, rest_data = Integer.unpack(data + additional_data)
        print unpack_int == number
        print rest_data == additional_data

    """
