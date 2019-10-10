# -*- coding: utf-8 -*-
import re, os

class StringFormatting(object):
    """ The goal here is to have one formatting string that can cope with any
        type of release.  We don't want different strings for Various Artists,
        or multidisc releases, where each disc has a separate title.

        One string to rule them all.

        Some string formatting functions. Loosely based on:
        http://wiki.hydrogenaud.io/index.php?title=Foobar2000:Title_Formatting_Reference

        Limitations:
            don't leave empty conditions (or potentiall empty), blank
            placeholders.

            $if1($strcmp('%artist%','%albumartist%'),'','%artist% - ') -- good
            $if1($strcmp(%artist%,%albumartist%),,%artist% - ) -- bad

        Example:
        stringFormatting = StringFormatting()
        stringFormatting.test()

        string = "%albumartist%/[%year%] %album%/$num(%track%,2) $if1($strcmp('%artist%','%albumartist%'),'','%artist% - ')%title%%fileext%"
        new_string = stringFormatting.parseString(string)

        See tests for more examples
    """

    def __init__(self):
        self.functions = {
            '$num': 2,
            '$strcmp': 2,
            '$if1': 3,  # cannot use $if
            '$ifequal': 4,
            '$ifgreater': 4,
        }

    def ifgreater(self, int1,int2,met,unmet):
        # for convenience if int1 or int2 are None make 0
        int1 = 0 if int1 is None or int1 == '' else int1
        int2 = 0 if int2 is None or int2 == '' else int2
        result = met if int(int1) > int(int2) else unmet
        return result


    def ifequal(self, int1,int2,met,unmet):
        result = met if int(int1) == int(int2) else unmet
        return result


    def num(self, num, places):
        string = '{:0>%%}'
        string = re.sub(r'\%\%', str(places), string)
        string = string.format(str(num))
        return string

    def strcmp(self, string1, string2):
        result = str(string1) == str(string2)
        return result

    def if1(self, cond, string1, string2=''):
        result = string1 if cond == True else string2
        return result

    def parseString(self, string):
        """ Walk through the input string, collecting functions along the way.

            string = 'some text $functionname(arg1,arg2, ...)'

            There is probably a clever way to do this with regex, but doing
            it this way to properly manage nested functions
        """
        output = ''

        print('parseString, input: {}'.format(string))

        # TODO: substitutions will happen later on when script embedded
        # subs = set(re.findall(r'(%.*?%)', string))
        #
        # for sub in subs:
        #     if sub in data:
        #         string = re.sub(sub, data[sub], string)
        #     else:
        #         string = re.sub(sub, '', string)

        command = ''
        """hierarchy used to track & collect nested functions
        """
        hierarchy = 0
        lastchar = ''
        for c in string:
            # print(command)
            if c == '$':
                hierarchy = hierarchy + 1
                command += c
            elif re.search(r'\(', c) and lastchar != '\\':
                command += c
            elif re.search(r'\)', c) and lastchar != '\\':
                hierarchy = hierarchy -1
                command += c
                if hierarchy == 0:
                    result = self.execute(command)
                    output += result
                    command = ''
            elif hierarchy > 0:
                command += c
            else:
                output += c
            lastchar = c

        print('parseString, output: {}'.format(output))

        return output

    def execute(self, string):
        """ Unpick the command, validate the function name and arguments
            Returns a string
        """
        output = ''

#TODO:  regex to capture empty & unquoted parameters

        functNameMatch = re.findall(r'(\$[a-z0-9_]+)\(', string)
        for match in functNameMatch:
            if match not in self.functions:
                 return 'unknown command'
        string = re.sub(r'\$', 'self.', string)
        result = eval(string)

        return result

    def test(self):
        track = {

            'formatted_string': "%albumartist%/[%year%] %album%$if1($strcmp('%totaldiscs%',''),'',$ifgreater('%totaldiscs%', 1,'/CD %discnumber%',''))$if1($strcmp('%disctitle%',''),'',', %disctitle%')/$num('%track%','2') $if1($strcmp('%artist%','%albumartist%'),'','%artist% - ')%title%%fileext%",
            'test': 'Advance/[2014] Deus Ex Machina/09 When we return.flac',
            '%artist%': 'Advance',
            '%albumartist%': 'Advance',
            '%year%': '2014',
            '%album%': 'Deus Ex Machina',
            '%title%': 'When we return',
            '%track%': '9',
            '%fileext%': '.flac',
        }

        multidisctrack = {
            'formatted_string': "%albumartist%/[%year%] %album%$if1($strcmp('%totaldiscs%',''),'',$ifgreater('%totaldiscs%', 1,'/CD %discnumber%',''))$if1($strcmp('%disctitle%',''),'',', %disctitle%')/$num('%track%','2') $if1($strcmp('%artist%','%albumartist%'),'','%artist% - ')%title%%fileext%",
            'test': 'Advance/[2014] Deus Ex Machina/CD 2, Bonus tracks/09 When we return.flac',
            '%artist%': 'Advance',
            '%albumartist%': 'Advance',
            '%year%': '2014',
            '%album%': 'Deus Ex Machina',
            '%discnumber%': '2',
            '%totaldiscs%': '2',
            '%disctitle%': 'Bonus tracks',
            '%title%': 'When we return',
            '%track%': '9',
            '%fileext%': '.flac',
        }

        various = {
            'formatted_string': "%albumartist%/[%year%] %album% \(%catnumber%\)$if1($strcmp('%totaldiscs%',''),'',$ifgreater('%totaldiscs%', 1,'/CD %discnumber%',''))$if1($strcmp('%disctitle%',''),'',', %disctitle%')/$num('%track%','2') $if1($strcmp('%artist%','%albumartist%'),'','%artist% - ')%title%%fileext%",
            'test': 'Various Artists/[2016] Modern EBM/05 Advance - Dead technology.flac',
            '%artist%': 'Advance',
            '%albumartist%': 'Various Artists',
            '%year%': '2016',
            '%album%': 'Modern EBM',
            '%title%': 'Dead technology',
            '%track%': '5',
            '%fileext%': '.flac',
        }

        passMessage = 'Pass'
        failMessage = 'Fail'

        """Test 1: directly calling function"""
        result = self.num(8,4)
        test = '0008'
        output = 'Output should read: "{}": {}'.format(test, failMessage if result != test else passMessage)
        print(output)

        """Test 2: track from a single artist album"""
        result = stringFormatting.parseString(track['formatted_string'], track)
        output = 'Output should read "{}": {}'.format(track['test'], failMessage if result != track['test'] else passMessage)
        print(output)

        """Test 3: track from a various artist album"""
        result = stringFormatting.parseString(various['formatted_string'], various)
        output = 'Output should read "{}": {}'.format(various['test'], failMessage if result != various['test'] else passMessage)
        print(output)

        """Test 4: track from a multidisc album"""
        result = stringFormatting.parseString(multidisctrack['formatted_string'], multidisctrack)
        output = 'Output should read "{}": {}'.format(multidisctrack['test'], failMessage if result != multidisctrack['test'] else passMessage)
        print(output)

# stringFormatting = StringFormatting()
# stringFormatting.test()
