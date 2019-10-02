#!/usr/bin/python3
import re

data = {
    '%artist%': 'Advance',
    '%albumartist%': 'Advance',
    '%year%': '2010',
    '%album%': '100 years',
    '%title%': 'Intro',
    '%track%': '1',
}


formatted_string = "%albumartist%\%album%\$num(%track%,2) %title%$if($strcmp(%artist%,%albumartist%),, - %artist%)"

class StringFormatting(object):

    def __init__(self, string):
        self.string = string
        self.functions = (
            'num',
            'strcmp'
        )

    def parseString(self, string, data):
        print(string)
        output = ''
        subs = set(re.findall(r'(%.*?%)', string))
        for sub in subs:
            string = re.sub(sub, data[sub], string)

        command = {}
        hierarchy = 0
        open = 0
        lastchar = ''
        for c in string:
            if c == '$':
                hierarchy = hierarchy + 1
                command[hierarchy] = c
            elif re.search(r'\(', c) and lastchar != '\\':
                command[hierarchy] += c
                open = open + 1
            elif re.search(r'\)', c) and lastchar != '\\':
                command[hierarchy] += c
                output += self.execute(command[hierarchy])
                open = open - 1
                hierarchy = hierarchy - 1
                print(output)
            elif hierarchy > 0:
                command[hierarchy] += c
            else:
                output += c
            lastchar = c


        # print(commands)
        print(subs)
        print(string)
        print(output)

    def execute(self, command):
        command = re.sub(r'\$', 'self.', command)
        output = ''
        result = eval(command)

        print(command)
        print(result)
        return result

    def num(self, num, places):
        string = '{:0>%%}'
        string = re.sub(r'\%\%', str(places), string)
        string = string.format(str(places), str(num))
        print(string)
        return string



stringFormatting = StringFormatting(formatted_string)
stringFormatting.parseString(formatted_string, data)
