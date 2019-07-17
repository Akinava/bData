# SPECIFICATION
- usage  
```python
>>> import bdata
>>> data = bdata.pack(42)
>>> print data.encode('hex')
'0101002a'
```

- parts  
'\x01\x01\x00\x2a' has two parts: schema and data
'\x01' '\x01' '\x00\x2a'
part '\x01' == 1 it is length of schema '\x00'
part '\x01' == 1 it is length of data '\x2a'

# schema
- data type  
the type of data is located in bit 7,6,5

```python
>>> bdata.pack(0).encode('hex')
'01010000'
```
'01 'schema length 1 byte
'01 'data length 1 byte
'00' type byte is int
'00' data is 0

```python
>>> bdata.pack(True).encode('hex')
'01016001'
```
'01' schema length
'01' data length
'60' type byte = bool/none
'01' data True

- sign of size
the sign of data size located in bit 4,3
00 = 1 byte -128 / 127
01 = 2 bytes
10 = 4 bytes
11 = 8 bytes

for Integer bytes sign int
for Float this is mantisa bytes size
for String this is length of size in bytes
for List this is length of items size
for Dictionary this is length of objects size

```python
>>> bdata.pack(1).encode('hex')
'01010001'
```
'01' schema length                                                              
'01' data length                                                                
'00' type byte 0b00000000, int, sign of size = 0 -> 1 byte                                                      
'01' data is 1

```python
>>> bdata.pack(0x7fff).encode('hex')
'0102087fff'
```
'01' schema length                                                              
'02' data length                                                                
'08' type byte 0b00001000, int, sign of size = 1 -> 2 byte                                                      
'7fff' data is 0x7fff

```python
>>> bdata.pack([1, '2', 3, '4', 5, '6']).encode('hex')
'0b068006004001004001004001013203340536'
```
'0b' schema length 11 byte
'06' data length 6 byte
'80' type byte 0b10000000, List, sign of size = 0 -> 1 byte of length
'06' length of List 6 items
'00' type of items 1 0b00000000 this is int, sign of size = 0 -> 1 byte
'40' type of items 2 0b01000000 this is string, sign of size = 0 -> 1 byte for length
'01' length of string is 1
'00' type of items 3 0b00000000 this is int, sign of size = 0 -> 1 byte
'40' type of items 4 0b01000000 this is string, sign of size = 0 -> 1 byte for length
'01' length of string is 1
'00' type of items 5 0b00000000 this is int, sign of size = 0 -> 1 byte
'40' type of items 6 0b01000000 this is string, sign of size = 0 -> 1 byte for length
'01' length of string is 1
'01' int data 1 is 1
'32' string data 2 is '2'
'03' int data 3 is 3
'34' string data 4 is '4'
'05' int data 5 is 5
'36' string data 6 is '6'

```python
>>> bdata.pack({1: 2, '3': '4'}).encode('hex')
'0804a00200004001400101023334'
```
'08' schema length 8 byte
'04' data length 4 byte
'a0' type byte 0b10100000, Dictionary, sign of size = 0 -> 1 byte of length
'02' ength of Dictionary objects
'00' type of key obj 1 0b00000000 this is int, sign of size = 0 -> 1 byte
'00' type of value obj 1 0b00000000 this is int, sign of size = 0 -> 1 byte
'40' type of key obj 2 0b01000000 this is string, sign of size = 0 -> 1 byte for length
'01' length of string is 1
'40' type of value obj 2 0b01000000 this is string, sign of size = 0 -> 1 byte for length
'01' length of string is 1
'01' data obj 1 key is 1
'02' data obj 1 value is 2
'33' data obj 2 key is '3'
'34' data obj 2 value is '4'

- compress items schema  
schema could be compressed on List if items in List has the same type
or Dictionary if keys or/and value has the same type

if items in List are the same is schema in type byte bit 0 set as 1
if keys in Dictionary are the same is schema in type byte bit 0 set as 1
if value in Dictionary are the same is schema in type byte bit 1 set as 1

```python
>>> bdata.pack([0, 1]).encode('hex')
'03028102000001'
```
'03' schema length 3 byte
'02' data length 2 byte
'81' type byte 0b10000001, List, sign of size = 0 -> 1 byte of length, bit 0 is 1 it means types of items are compressed
'02' length of List 2 items
'00' type of all items is int, sign of size = 0 -> 1 byte
'00' int data 1 is 0
'01' int data 2 is 1

```python
>>> bdata.pack({'a': 100, 'b': 101}).encode('hex')
'0504a30240010061646265'
```
'05' schema length 5 byte
'04' data length 4 byte
'a3' type byte 0b10100011, Dictionary, sign of size = 0 -> 1 byte of length, bit 0 is 1 it means types of key are compressed, bit 1 is 1 it means types of values are compressed
'02' length of Dictionary objects
'40' type of key all objects is 0b01000000 this is string, sign of size = 0 -> 1 byte for length
'01' length of string is 1
'00' type of value all objects 0b00000000 this is int, sign of size = 0 -> 1 byte
'61' data obj 1 key is 'a'
'64' data obj 1 value is 0x64 = 100
'62' data obj 2 key is 'b'
'65' data obj 2 value is 101
