#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import binascii
import json
import os
import sys


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


test_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(test_dir, '../src')
sys.path.append(src_dir)
import bdata


def test_integer():
    print('-' * 10)
    print('Integer')
    additional_data = b'\xff'
    cases = [
        # regular length 1 byte (b)
        {'value': 0, 'schema': b'\x00', 'data': b'\x00'},
        {'value': 0x7f, 'schema': b'\x00', 'data': b'\x7f'},
        {'value': -0x80, 'schema': b'\x00', 'data': b'\x80'},
        # regular length 2 byte (h)
        {'value': 0x80, 'schema': b'\x08', 'data': b'\x00\x80'},
        {'value': -0x81, 'schema': b'\x08', 'data': b'\xff\x7f'},
        {'value': 0x7fff, 'schema': b'\x08', 'data': b'\x7f\xff'},
        {'value': -(0x8000), 'schema': b'\x08', 'data': b'\x80\x00'},
        # regular length 4 bytes (l)
        {'value': 0x8000, 'schema': b'\x10', 'data': b'\x00\x00\x80\x00'},
        {'value': -(0x8001), 'schema': b'\x10', 'data': b'\xff\xff\x7f\xff'},
        {'value': 0x7fffffff, 'schema': b'\x10', 'data': b'\x7f\xff\xff\xff'},
        {'value': -(0x80000000), 'schema': b'\x10', 'data': b'\x80\x00\x00\x00'},
        # regular length 8 bytes (q)
        {'value': 0x80000000, 'schema': b'\x18', 'data': b'\x00\x00\x00\x00\x80\x00\x00\x00'},
        {'value': -(0x80000001), 'schema': b'\x18', 'data': b'\xff\xff\xff\xff\x7f\xff\xff\xff'},
        {'value': 0x7fffffffffffffff, 'schema': b'\x18', 'data': b'\x7f\xff\xff\xff\xff\xff\xff\xff'},
        {'value': -(0x8000000000000000), 'schema': b'\x18', 'data': b'\x80\x00\x00\x00\x00\x00\x00\x00'},
    ]
    test_cases(bdata.Integer, cases)


def test_boolean():
    print('-' * 10)
    print('Boolean')
    cases = [
        {'value': True, 'schema': b'\x60', 'data': b'\x01'},
        {'value': False, 'schema': b'\x60', 'data': b'\x00'},
        {'value': None, 'schema': b'\x60', 'data': b'\xff'},
    ]
    test_cases(bdata.Boolean, cases)


def test_string():
    print('-' * 10)
    print('String')
    additional_data = b'\xff'
    cases = [
        {'value': 'abc', 'schema': b'\x40\x03', 'data': b'abc'},
        {'value': '123', 'schema': b'\x40\x03', 'data': b'123'},
        {'value': 'Лис', 'schema': b'\x40\x06', 'data': 'Лис'.encode('utf8')},
        {'value': '123qweйцу', 'schema': b'\x40\x0c', 'data': '123qweйцу'.encode('utf8')},
        {'value': '0'*((1<<8)-1), 'schema': b'\x40'+b'\xff'*1, 'data': b'0'*((1<<8)-1)},
        {'value': '0'*((1<<16)-1), 'schema': b'\x48'+b'\xff'*2, 'data': b'0'*((1<<16)-1)},
        #{'value': '0'*((1<<32)-1), 'schema': b'\x50'+b'\xff'*4, 'data': b'0'*((1<<32)-1)},
        #{'value': '0'*((1<<33)-1), 'schema': b'\x70'+(b'\x00'*3)+b'\x01'+(b'\xff'*4), 'data': b'0'*((1<<33)-1)},
     ]

    # additional condition // [:10]
    for case in cases:
        schema, data = bdata.String().pack(case['value'])
        if schema != case['schema']:
            print('Error pack schema', \
                  'value:',  case['value'][:10], \
                  'got schema:', schema.hex(), \
                  'expected schema:', case['schema'].hex())
        if data != case['data']:
            print('Error pack data', \
                  'value', case['value'][:10], \
                  'got data:', data.hex()[:10], \
                  'expected data', case['data'].hex()[:10])

    for case in cases:
        value, schema_tail, data_tail = bdata.String().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        if value != case['value']:
            print('Error unpack value', \
                  'expected value:',  case['value'][:10], \
                  'got value:', value[:10])
        if schema_tail != additional_data:
            print('Error unpack wrong schema_tail', \
                  'value', case['value'][:10], \
                  'got schema_tail:', schema_tail.hex(), \
                  'expected schema_tail:', additional_data.hex())
        if data_tail != additional_data:
            print('Error unpack wrong schema_tail', \
                  'value', case['value'][:10], \
                  'got data_tail:', data_tail.hex(), \
                  'expected data_tail:', additional_data.hex())


def test_float():
    print('-' * 10)
    print('Float')

    additional_data = b'\xff'
    cases = [
        {'value': -0.0000000001,  'schema': b'\x20', 'data': b'\xf6\xff'            },  # -10  1
        {'value': 1e-10,          'schema': b'\x20', 'data': b'\xf6\x01'            },  # -10  1
        {'value': 1e+127,         'schema': b'\x20', 'data': b'\x7f\x01'            },  #  127 1
        {'value': 1e-128,         'schema': b'\x20', 'data': b'\x80\x01'            },  # -128 1
        {'value': 0.1,            'schema': b'\x20', 'data': b'\xff\x01'            },  # -1   1
        {'value': 0.222,          'schema': b'\x28', 'data': b'\xfd\x00\xde'        },  # -1   222
        {'value': -0.222,         'schema': b'\x28', 'data': b'\xfd\xff\x22'        },  # -1  -222
        {'value': 0.0001111111,   'schema': b'\x30', 'data': b'\xf6\x00\x10\xf4\x47'},  # -10  1111111
        {'value': -0.0001111111,  'schema': b'\x30', 'data': b'\xf6\xff\xef\x0b\xb9'},  # -10 -1111111
        {'value': 1.00000001,     'schema': b'\x30', 'data': b'\xf8\x05\xf5\xe1\x01'},  # -8   100000001
        {'value': -1.00000001,    'schema': b'\x30', 'data': b'\xf8\xfa\x0a\x1e\xff'},  # -8  -100000001
        {'value': 10000000.0,     'schema': b'\x20', 'data': b'\x07\x01'            },  #  7   1
        {'value': -10000000.0,    'schema': b'\x20', 'data': b'\x07\xff'            },  #  7  -1
        {'value': 1.2323435e-19,  'schema': b'\x30', 'data': b'\xe6\x00\xbc\x0a\x6b'},  # -26  12323435
        {'value': -1.2323435e-19, 'schema': b'\x30', 'data': b'\xe6\xff\x43\xf5\x95'},  # -26 -12323435
        {'value': 1.1111e+19,     'schema': b'\x28', 'data': b'\x0f\x2b\x67'        },  #  15  11111
        {'value': -1.1111e+19,    'schema': b'\x28', 'data': b'\x0f\xd4\x99'        },  #  15 -11111
        {'value': float('nan'),   'schema': b'\x38', 'data': b'\x80\x7f\xff\xff\xff\xff\xff\xff\xff'}, #
        {'value': float('-inf'),  'schema': b'\x38', 'data': b'\x80\x80\x00\x00\x00\x00\x00\x00\x00'}, #
        {'value': float('inf'),   'schema': b'\x38', 'data': b'\x80\x80\x00\x00\x00\x00\x00\x00\x01'}, #
    ]
    for case in cases:
        schema, data = bdata.Float().pack(case['value'])
        if schema != case['schema']:
            print('Error pack schema', \
                  'value:',  case['value'], \
                  'got schema:', schema.hex(), \
                  'expected schema:', case['schema'].hex())

        if data != case['data']:
            print('Error pack data', \
                  'value', case['value'], \
                  'got data:', data.hex(), \
                  'expected data', case['data'].hex())

    for case in cases:
        value, schema_tail, data_tail = bdata.Float().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        # additional condition // str(value) != str(case['value'])
        if value != case['value'] and str(value) != str(case['value']):
            print('Error unpack value', \
                  'expected value:',  [case['value']], type(case['value']), \
                  'got value:', [value], type(value))
        if schema_tail != additional_data:
            print('Error unpack wrong schema_tail', \
                  'value', case['value'], \
                  'got schema_tail:', schema_tail.hex(), \
                  'expected schema_tail:', additional_data.hex())
        if data_tail != additional_data:
            print('Error unpack wrong schema_tail', \
                  'value', case['value'], \
                  'got data_tail:', data_tail.hex(), \
                  'expected data_tail:', additional_data.hex())


def test_list():
    print('-' * 10)
    print('List')
    cases = [
        {'value': [], 'schema': b'\x80\x00', 'data': b''},
        {'value': [1, 1], 'schema': b'\x81\x02\x00', 'data': b'\x01\x01'},
        {'value': [1, None], 'schema': b'\x80\x02\x00\x60', 'data': b'\x01\xff'},
        {'value': ["Л", "и", "с"], 'schema': b'\x81\x03\x40\x02', 'data': 'Лис'.encode('utf8')},
        {'value': ["Лис", 0xffff, None], 'schema': b'\x80\x03\x40\x06\x10\x60', 'data': b'\xd0\x9b\xd0\xb8\xd1\x81\x00\x00\xff\xff\xff'},
        {'value': [], 'schema': b'\x80\x00', 'data': b''},
        {'value': [1, [1]], 'schema': b'\x80\x02\x00\x80\x01\x00', 'data': b'\x01\x01'},
    ]
    test_cases(bdata.List, cases)


def test_dict():
    print('-' * 10)
    print('Dict')
    cases = [
        {'value': {}, 'schema': b'\xa0\x00', 'data': b''},
        {'value': {0: 0}, 'schema': b'\xa0\x01\x00\x00', 'data': b'\x00\x00'},
        {'value': {0: 0, 1: 0, 2: 0}, 'schema': b'\xa3\x03\x00\x00', 'data': b'\x00\x00\x01\x00\x02\x00'},
        {'value': {0: 0, 1: None}, 'schema': b'\xa1\x02\x00\x00\x60', 'data': b'\x00\x00\x01\xff'},
        {'value': {0: 0, 1: "a"}, 'schema': b'\xa1\x02\x00\x00\x40\x01', 'data': b'\x00\x00\x01\x61'},
        {'value': {0: 0, "a": 0}, 'schema': b'\xa2\x02\x00\x00\x40\x01', 'data': b'\x00\x00\x61\x00'},
        {'value': {0: 0, "a": []}, 'schema': b'\xa0\x02\x00\00\x40\x01\x80\x00', 'data': b'\x00\x00\x61'},
        {'value': {0: 0, "a": [1, 1]}, 'schema': b'\xa0\x02\x00\x00\x40\x01\x81\x02\x00', 'data': b'\x00\x00\x61\x01\x01'},
        {'value': {1: [0, 1], 2: {1: 1}}, 'schema': b'\xa1\x02\x00\x81\x02\x00\xa0\x01\x00\x00', 'data': b'\x01\x00\x01\x02\x01\x01'},
    ]
    test_cases(bdata.Dictionary, cases)


def test_obj():
    print('-' * 10)
    print('Object')
    cases = [
        {'value': True,          'data': b'\x01\x01\x60\x01'},                    #  0
        {'value': [1],           'data': b'\x03\x01\x80\x01\x00\x01'},            # -3
        {'value': {},            'data': b'\x02\x00\xa0\x00'},                    # -2
        {'value': [],            'data': b'\x02\x00\x80\x00'},                    # -2
        {'value': [0, 1],        'data': b'\x03\x02\x81\x02\x00\x00\x01'},        # -1
        {'value': {0: 0},        'data': b'\x04\x02\xa0\x01\x00\x00\x00\x00'},    #  0
        {'value': {0: []},       'data': b'\x05\x01\xa0\x01\x00\x80\x00\x00'},    #  1
        {'value': {0: 0, 1: 0},  'data': b'\x04\x04\xa3\x02\x00\x00\x00\x00\x01\x00'},          #  6
        {'value': [1, 'a', 3.5], 'data': b'\x06\x04\x80\x03\x00\x40\x01\x20\x01\x61\xff\x23'},  #  1
        {'value': [1, 20, 3],    'data': b'\x03\x03\x81\x03\x00\x01\x14\x03' },                 #  2
        {'value': [1, 20, 3, -2],  'data': b'\x03\x04\x81\x04\x00\x01\x14\x03\xfe'},            #  5
        {'value': [1, 20, 3, '1'], 'data': binascii.unhexlify('07048004000000400101140331')},        #  2
        {'value': [1, 20, 3, '1', '0232'], 'data': binascii.unhexlify('09088005000000400140040114033130323332')},                                                  #  4
        {'value': [1, 20, 3, '1', '0232', 2, 3, {1:1, 4: 'q'}], 'data': binascii.unhexlify('110e8008000000400140040000a102000040010114033130323332020301010471')}, # 16
        {'value': 'qwertyqwerty', 'data': binascii.unhexlify('020c400c717765727479717765727479')},   # -2
        {'value': 0,              'data': b'\x01\x01\x00\x00'},                                 # -3
        {'value': 1000,           'data': b'\x01\x02\x08\x03\xe8'},                             # -1
        {'value': 0x7fffffff,     'data': b'\x01\x04\x10\x7f\xff\xff\xff'},                     #  3
        {'value': 100000.0,       'data': b'\x01\x02\x20\x05\x01'},                             #  3
        {'value': 11.01,          'data': b'\x01\x03\x28\xfe\x04\x4d'},                         # -1
        {'value': [11.01],        'data': b'\x03\x03\x80\x01\x28\xfe\x04\x4d'},                 # -1
        {'value': [11.01, 5.03],  'data': b'\x03\x06\x81\x02\x28\xfe\x04\x4d\xfe\x01\xf7'},     # -2
        {'value': [11.01, 5.03, 80.99], 'data': binascii.unhexlify('0309810328fe044dfe01f7fe1fa3')}, #  6
    ]

    for case in cases:
        data = bdata.pack(case['value'])
        value = bdata.unpack(data)

        if case['value'] != value:
            print('Error pack/unpack obj', \
                  'got value:', case['value'], \
                  'expected data:', value)

        if data != case['data']:
            print('Error pack obj', \
                  'value:', case['value'], \
                  'got data:', data.hex(), \
                  'expected data:', case['data'].hex())

        #print 'length:', case['value'], len(json.dumps(case['value']))-len(data)


def test_pack(cls, case):
    schema, data = cls().pack(case['value'])
    if schema != case['schema']:
        print('Error pack schema', \
              'value:',  case['value'], \
              'got schema:', schema.hex(), \
              'expected schema:', case['schema'].hex())

    if data != case['data']:
        print('Error pack data', \
              'value', case['value'], \
              'got data:', data.hex(), \
              'expected data', case['data'].hex())


def test_unpack(cls, case):
    additional_data = b'\xff'
    value, schema_tail, data_tail = cls().unpack(
        schema=case['schema']+additional_data,
        data=case['data']+additional_data
    )
    if value != case['value']:
        print('Error unpack value', \
              'expected value:',  case['value'], \
              'got value:', value)
    if schema_tail != additional_data:
        print('Error unpack wrong schema_tail', \
              'value', case['value'], \
              'got schema_tail:', schema_tail.hex(), \
              'expected schema_tail:', additional_data.hex())
    if data_tail != additional_data:
        print('Error unpack wrong schema_tail', \
              'value', case['value'], \
              'got data_tail:', data_tail.hex(), \
              'expected data_tail:', additional_data.hex())


def test_cases(cls, cases):
    for case in cases:
        test_pack(cls, case)
        test_unpack(cls, case)


def tests():
    print('test start')
    test_string()
    test_integer()
    test_boolean()
    test_float()
    test_list()
    test_dict()
    test_obj()
    print('-' * 10)
    print('test end')


if __name__ == '__main__':
    tests()
