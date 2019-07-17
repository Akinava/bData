#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import json
import os
import sys


test_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(test_dir, '../src')
sys.path.append(src_dir)
import bdata


def test_integer():
    print '-' * 10
    print 'Integer'
    additional_data = '\xff'
    cases = [
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
    test_cases(bdata.Integer, cases)


def test_boolean():
    print '-' * 10
    print 'Boolean'
    cases = [
        {'value': True, 'schema': '\x60', 'data': '\x01'},
        {'value': False, 'schema': '\x60', 'data': '\x00'},
        {'value': None, 'schema': '\x60', 'data': '\xff'},
    ]
    test_cases(bdata.Boolean, cases)


def test_string():
    print '-' * 10
    print 'String'
    additional_data = '\xff'
    cases = [
        {'value': 'abc', 'schema': '\x40\x03', 'data': 'abc'},
        {'value': '123', 'schema': '\x40\x03', 'data': '123'},
        {'value': 'Лис', 'schema': '\x40\x06', 'data': 'Лис'},
        {'value': '123qweйцу', 'schema': '\x40\x0c', 'data': '123qweйцу'},
        {'value': '0'*((1<<8)-1), 'schema': '\x40'+'\xff'*1, 'data': '0'*((1<<8)-1)},
        {'value': '0'*((1<<16)-1), 'schema': '\x48'+'\xff'*2, 'data': '0'*((1<<16)-1)},
        #{'value': '0'*((1<<32)-1), 'schema': '\x50'+'\xff'*4, 'data': '0'*((1<<32)-1)},
        #{'value': '0'*((1<<33)-1), 'schema': '\x70'+('\x00'*3)+'\x01'+('\xff'*4), 'data': '0'*((1<<33)-1)},
     ]

    # additional condition // [:10]
    for case in cases:
        schema, data = bdata.String().pack(case['value'])
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

    for case in cases:
        value, schema_tail, data_tail = bdata.String().unpack(
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
    cases = [
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
    for case in cases:
        schema, data = bdata.Float().pack(case['value'])
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

    for case in cases:
        value, schema_tail, data_tail = bdata.Float().unpack(
            schema=case['schema']+additional_data,
            data=case['data']+additional_data
        )
        # additional condition // str(value) != str(case['value'])
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


def test_list():
    print '-' * 10
    print 'List'
    cases = [
        {'value': [], 'schema': '\x80\x00', 'data': ''},
        {'value': [1, 1], 'schema': '\x81\x02\x00', 'data': '\x01\x01'},
        {'value': [1, None], 'schema': '\x80\x02\x00\x60', 'data': '\x01\xff'},
        {'value': ["Л", "и", "с"], 'schema': '\x81\x03\x40\x02', 'data': 'Лис'},
        {'value': ["Лис", 0xffff, None], 'schema': '\x80\x03\x40\x06\x10\x60', 'data': 'Лис\x00\x00\xff\xff\xff'},
        {'value': [], 'schema': '\x80\x00', 'data': ''},
        {'value': [1, [1]], 'schema': '\x80\x02\x00\x80\x01\x00', 'data': '\x01\x01'},
    ]
    test_cases(bdata.List, cases)


def test_dict():
    print '-' * 10
    print 'Dict'
    cases = [
        {'value': {}, 'schema': '\xa0\x00', 'data': ''},
        {'value': {0: 0}, 'schema': '\xa0\x01\x00\x00', 'data': '\x00\x00'},
        {'value': {0: 0, 1: 0, 2: 0}, 'schema': '\xa3\x03\x00\x00', 'data': '\x00\x00\x01\x00\x02\x00'},
        {'value': {0: 0, 1: None}, 'schema': '\xa1\x02\x00\x00\x60', 'data': '\x00\x00\x01\xff'},
        {'value': {0: 0, 1: "a"}, 'schema': '\xa1\x02\x00\x00\x40\x01', 'data': '\x00\x00\x01\x61'},
        {'value': {0: 0, "a": 0}, 'schema': '\xa2\x02\x00\x00\x40\x01', 'data': '\x00\x00\x61\x00'},
        {'value': {0: 0, "a": []}, 'schema': '\xa0\x02\x00\00\x40\x01\x80\x00', 'data': '\x00\x00\x61'},
        {'value': {0: 0, "a": [1, 1]}, 'schema': '\xa0\x02\x00\x00\x40\x01\x81\x02\x00', 'data': '\x00\x00\x61\x01\x01'},
        {'value': {1: [0, 1], 2: {1: 1}}, 'schema': '\xa1\x02\x00\x81\x02\x00\xa0\x01\x00\x00', 'data': '\x01\x00\x01\x02\x01\x01'},
    ]
    test_cases(bdata.Dictionary, cases)


def test_obj():
    print '-' * 10
    print 'Object'
    cases = [
        {'value': True,          'data': '\x01\x60\x01\x01'},                    #  0
        {'value': [1],           'data': '\x03\x80\x01\x00\x01\x01'},            # -3
        {'value': {},            'data': '\x02\xa0\x00\x00'},                    # -2
        {'value': [],            'data': '\x02\x80\x00\x00'},                    # -2
        {'value': [0, 1],        'data': '\x03\x81\x02\x00\x02\x00\x01'},        # -1
        {'value': {0: 0},        'data': '\x04\xa0\x01\x00\x00\x02\x00\x00'},    #  0
        {'value': {0: []},       'data': '\x05\xa0\x01\x00\x80\x00\x01\x00'},    #  1
        {'value': {0: 0, 1: 0},  'data': '\x04\xa3\x02\x00\x00\x04\x00\x00\x01\x00'},          #  6
        {'value': [1, 'a', 3.5], 'data': '\x06\x80\x03\x00\x40\x01\x20\x04\x01\x61\xff\x23'},  #  1
        {'value': [1, 20, 3],    'data': '\x03\x81\x03\x00\x03\x01\x14\x03' },                 #  2
        {'value': [1, 20, 3, -2],  'data': '\x03\x81\x04\x00\x04\x01\x14\x03\xfe'},            #  5
        {'value': [1, 20, 3, '1'], 'data': '07800400000040010401140331'.decode('hex')},        #  2
        {'value': [1, 20, 3, '1', '0232'], 'data': '09800500000040014004080114033130323332'.decode('hex')},                                                  #  4
        {'value': [1, 20, 3, '1', '0232', 2, 3, {1:1, 4: 'q'}], 'data': '118008000000400140040000a102000040010e0114033130323332020301010471'.decode('hex')}, # 16
        {'value': 'qwertyqwerty', 'data': '02400c0c717765727479717765727479'.decode('hex')},   # -2
        {'value': 0,              'data': '\x01\x00\x01\x00'},                                 # -3
        {'value': 1000,           'data': '\x01\x08\x02\x03\xe8'},                             # -1
        {'value': 0x7fffffff,     'data': '0110047fffffff'.decode('hex')},                     #  3
        {'value': 100000.0,       'data': '\x01\x20\x02\x05\x01'},                             #  3
        {'value': 11.01,          'data': '\x01\x28\x03\xfe\x04\x4d'},                         # -1
        {'value': [11.01],        'data': '0380012803fe044d'.decode('hex')},                   # -1
        {'value': [11.01, 5.03],  'data': '0381022806fe044dfe01f7'.decode('hex')},             # -2
        {'value': [11.01, 5.03, 80.99], 'data': '0381032809fe044dfe01f7fe1fa3'.decode('hex')}, #  6
    ]

    for case in cases:
        data = bdata.pack(case['value'])
        value = bdata.unpack(data)

        if case['value'] != value:
            print 'Error pack/unpack obj', \
                'got value:', case['value'], \
                'expected data:', value

        if data != case['data']:
            print 'Error pack obj', \
                'value:', case['value'], \
                'got data:', data.encode('hex'), \
                'expected data:', case['data'].encode('hex')

        #print 'length:', case['value'], len(json.dumps(case['value']))-len(data)


def test_pack(cls, case):
    schema, data = cls().pack(case['value'])
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


def test_unpack(cls, case):
    additional_data = '\xff'
    value, schema_tail, data_tail = cls().unpack(
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


def test_cases(cls, cases):
    for case in cases:
        test_pack(cls, case)
        test_unpack(cls, case)


def tests():
    print 'test start'
    test_string()
    test_integer()
    test_boolean()
    test_float()
    test_list()
    test_dict()
    test_obj()
    print '-' * 10
    print 'test end'


if __name__ == '__main__':
    tests()
