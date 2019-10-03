# -*- coding: utf-8 -*-
import re, os

class StringFormatting(object):
    """ Some string formatting functions. Loosely based on:
        http://wiki.hydrogenaud.io/index.php?title=Foobar2000:Title_Formatting_Reference
        Validate anything passed through.  Reject unknown functions and wrong number of paramString

        Example:
        stringFormatting = StringFormatting()
        stringFormatting.test()

    """

    def __init__(self):
        self.functions = {
            '$num': 2,
            '$strcmp': 2,
            '$if1': 3,  # cannot use $if
            '$ifequal': 4,
        }

    def test(self):

        track = {
            'formatted_string': '%albumartist%/[%year%] %album%/$num(%track%,2) $if1($strcmp("%artist%","%albumartist%"),"","%artist% - ")%title%%fileext%',
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
            'formatted_string': '%albumartist%/[%year%] %album%$if1($strcmp(%totaldiscs%,),,$ifequal(%totaldiscs%,1,YEP,/CD %discnumber%))/$num(%track%,2) $if1($strcmp(%artist%,%albumartist%),,%artist% - )%title%%fileext%',
            'test': 'Advance/[2014] Deus Ex Machina/CD 2/09 When we return.flac',
            '%artist%': 'Advance',
            '%albumartist%': 'Advance',
            '%year%': '2014',
            '%album%': 'Deus Ex Machina',
            # '%discnumber%': '2',
            '%totaldiscs%': '2',
            '%title%': 'When we return',
            '%track%': '9',
            '%fileext%': '.flac',
        }

        various = {
            'formatted_string': '$if1($strcmp(%albumartist%,Various Artists),Various Artists,%albumartist%)/[%year%] %album%/$num(%track%,2) $if1($strcmp(%artist%,%albumartist%),,%artist% - )%title%%fileext%',
            'test': 'Various Artists/[2016] Modern EBM/05 Advance - Dead technology.flac',
            '%artist%': 'Advance',
            '%albumartist%': 'Various Artists',
            '%year%': '2016',
            '%album%': 'Modern EBM',
            '%title%': 'Dead technology',
            '%track%': '5',
            '%fileext%': '.flac',
        }



        string = "Advance/[2014] Deus Ex Machina$if1($strcmp(2,),,$ifequal(2,1,YEP,/CD ))/$num(9,2) $if1($strcmp(Advance,Advance),,Advance - )When we return.flac"
        commands = 'self.if1(self.strcmp("Advance","Advance"),"smae","Advance - ")'

        # commands = "self.if1(self.strcmp('2','1'),'',self.ifequal('2','2','','/CD '))"
        result = eval(commands)
        print(result)
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

        # """Test 3: track from a various artist album"""
        # result = stringFormatting.parseString(various['formatted_string'], various)
        # output = 'Output should read "{}": {}'.format(various['test'], failMessage if result != various['test'] else passMessage)
        # print(output)
        #
        # """Test 4: track from a multidisc album"""
        # result = stringFormatting.parseString(multidisctrack['formatted_string'], multidisctrack)
        # print(result)
        # output = 'Output should read "{}": {}'.format(multidisctrack['test'], failMessage if result != multidisctrack['test'] else passMessage)
        # print(output)
        #


    def ifequal(self, int1,int2,yes,nope):
        print(int1)
        print(int2)
        print(yes)
        print(nope)
        result = yes if int(int1) == int(int2) else nope
        print(result)
        return result


    def num(self, num, places):
        string = '{:0>%%}'
        string = re.sub(r'\%\%', str(places), string)
        string = string.format(str(num))
        return string

    def strcmp(self, string1, string2):
        result = str(string1) == str(string2)
        print(result)
        return result

    def if1(self, cond, string1, string2=''):
        result = string1 if cond == True else string2
        return result

    def parseString(self, string, data):
        """ Walk through the input string, collecting functions along the way.

            string = 'some text $functionname(arg1,arg2, ...)'

            There is probably a clever way to do this with regex, but doing
            it this way to properly manage nested functions
        """
        print(string)
        output = ''

        # TODO: substitutions will happen later on when script embedded
        subs = set(re.findall(r'(%.*?%)', string))
        print(subs)
        for sub in subs:
            if sub in data:
                string = re.sub(sub, data[sub], string)
            else:
                string = re.sub(sub, '', string)

        print(string)

        command = ''
        """hierarchy used to track & collect nested functions
        """
        hierarchy = 0
        lastchar = ''
        for c in string:
            print(command)
            if c == '$':
                hierarchy = hierarchy + 1
                command += c
            elif re.search(r'[\\\/]', c) and lastchar != '\\':
                output += os.path.sep
            elif re.search(r'\(', c) and lastchar != '\\':
                command += c
            elif re.search(r'\)', c) and lastchar != '\\':
                hierarchy = hierarchy -1
                command += c
                if hierarchy == 0:
                    result = self.execute(command)
                    command = ''
            elif hierarchy > 0:
                command += c
            else:
                output += c
            lastchar = c

        return output

    def execute(self, string):
        """ Unpick the command, validate the function name and arguments
            Returns a string
        """
        output = ''

        print(string)

        # TODO: do this differently!!!
        # funtNameMatch = re.search(r'(\$[a-z0-9_]+)', string)
        # if funtNameMatch is None:
        #     return 'unknown command'
        # elif funtNameMatch.group(1) not in self.functions:
        #     return 'unknown command'
        # else:
        #     function = re.sub(r'\$', 'self.', funtNameMatch.group(1))
        #
        # paramString = re.search(r'\((.*)\)$', string)
        # if paramString is None:
        #     return 'cannot parse arguments'
        # else:
        #     parameters = re.split(r'(?<!\\)(?:\\\\)*,', paramString.group(1))
        #
        # """we will need to substitute placeholders before further processing"""
        # for param in parameters:
        #     # TODO hand over to function that handles placeholder substitution
        #     print(param)
        #
        # # if len(parameters) != self.functions[funtNameMatch.group(1)]:
        # #     return 'wrong number of arguments'

        result = eval(function + str(tuple(parameters)))

        return result


stringFormatting = StringFormatting()
stringFormatting.test()
