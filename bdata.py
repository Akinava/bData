#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from decimal import Decimal
import struct


__author__ = "Akinava"
__author_email__ = "akinava@gmail.com"
__version__ = [0, 0]


class NOT_FIND:
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


not_find = NOT_FIND()


class INTEGER:
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
    def __check_size_is_correct(self, number):
        if number <= self.maximum_value and \
           number >= -1 * self.maximum_value:
            return
        raise Exception('requires -{value:x} <= number <= {value:x}'.format(value=self.maximum_value))
        return False

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
    def __set_sign(self, number):
        if number < 0:
            return 1 << self.bit_sign
        return 0

    @classmethod
    def __remove_sigh(self, number):
        if number < 0:
            return -1 * number
        return number

    @classmethod
    def __define_number_length_in_bytes(self, number):
        length = 0
        max_value = self.first_byte_maxixum_value
        while number > max_value:
            length += 1
            max_value = (self.first_byte_maxixum_value << 8 * ((2 ** length) - 1)) + \
                        (1 << 8 * ((2 ** length) - 1)) - 1
        return length


    @classmethod
    def __set_bytes_length(self, number, data):
        length = self.__define_number_length_in_bytes(number)
        data |= (length << self.bit_size_low)
        data <<= (8 * (length ** 2))
        return data

    @classmethod
    def __pack_number(self, number, data):
        data |= number
        return data

    @classmethod
    def __convert_number_to_hex(self, data):
        return '{:02x}'.format(data).decode('hex')

    @classmethod
    def pack(self, number):
        self.__check_size_is_correct(number)
        data = self.__set_sign(number)
        number = self.__remove_sigh(number)
        data = self.__set_bytes_length(number, data)
        data = self.__pack_number(number, data)
        return self.__convert_number_to_hex(data)

    @classmethod
    def unpack(data):
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


class BINT:

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

    int = -0x2550000000
    print INTEGER.pack(int).encode('hex')

    #print hex(STRUCT.small_int_maximum_size)


    #d = BDATA({"q": {"w": "e"}})

    # pack maps
    # import/export maps
    # send receive maps
    # pack unpack bdata

    #print [d._bin]
    #print [d._json]
    #a = d.rrr.nnn
    #print a

    #js_data = d.__json
    #bd = d.__bdata()
    #d._from_bdata("\x00\x00")
    #d._from_bdata("\x03\x02\x05\x00\02\05\x68\x65\x6c\x6c\x6f\x02\x6b\x65\x79\x01\x09")  # {0: "hello", "key": 9}
