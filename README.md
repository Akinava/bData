# bData
- intention  
This is a library which helps to encode [JSON](https://en.wikipedia.org/wiki/JSON) object to binary data and decode it back.

- required  
python2.7


- usage
```python
>>> import bData
>>> data = bData.pack({})
>>> data
'\x02\xa0\x00\x00'
>>> obj = bData.unpack(data)
>>> print obj
{}
```

- how does it work  
please read [specification](/doc/specification.md)

- offtopic  
![new standart](http://imgs.xkcd.com/comics/standards.png)
