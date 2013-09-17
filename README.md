PyService
=========

Mass JSON API tester

### Features

Target specific services in groups 
Override values for single service testing


### Usage

```python
$ python service.py -g <group_name> -s <service_name> -t <temporary_variable> -o <key>=<value>,<key>=<value>
```

Example -

```python
$ python service.py -g Example1 -s login,tweets -t 1200
```

#### Mass Test services

```python
$ python service.py 
$ python service.py -g <group_name>,<group_name>
```

### Mutual SSL Support

```xml

<service name="Example3" ssl_key="<path_to_key>" ssl_cert="<path_to_cert>" ssl_ca="<path_to_ca>"> 

	...

</service>

```
