import re

def split_string(string, seperator=None, maxsplit=-1):
    try:
        return string.split(seperator, maxsplit)
    except:
        return list(string)

def split_regex(string, seperator_pattern):
    try:
        return re.split(seperator_pattern, string)
    except:
        return list(string)

class FilterModule(object):
    ''' A filter to split a string into a list. '''
    def filters(self):
        return {
            'split' : split_string,
            'split_regex' : split_regex,
        }

