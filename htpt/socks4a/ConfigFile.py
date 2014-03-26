"""ConfigFile.py

Copyright (C) 2001  Xavier Lagraula
See COPYRIGHT.txt and GPL.txt for copyrights information.

This module defines a crude function used to read a configuration file and
fill an options dictionary, according to an option definitions dictionary.
See decode_configfile documentation for more information.
"""

def decode_configfile(filename, definitions, defaults = {}, separator = ':'):
    """decode_configfile(filename, definitions, defaults = {}, separator = ':')
Reads a configuration file, decodes it and store the result in a dictionary.

See functions read_configfile() and evaluate() in the same module for more
details.

Parameters:
- filename: name of the file to be read.
- definitions: dictionary describing the avilable options and how to decode
    them from the configuration file.
- defaults: a dictionary containing defaults values for the options

Return value:
- a dictionary, eventually empty, containing the options extracted from
    the file."""
    # This will store values read in the file as strings.
    string_values = read_configfile(filename, separator)

    # Now we convert these values into the expected data types.
    # Note that defaults values are handled by evaluate() because if it wasn't
    # I would have to make a loop to copy "values" content into a copy of
    # "defaults". 
    values = evaluate(definitions, string_values, defaults)

    return values

def evaluate(definitions, values, defaults = {}):
    """evaluate(definitions, values, defaults = {})
Evaluates a dictionary of "values" according to the "definitions" of type.

For each key in "values", "definitions" is searched for the corresponding type.
If no type definition is found, 'string' is assumed. Then the value is
converted and stored in the result. Values are expected to be strings
before conversion.

The types can be one of the following:
- 'string': no conversion is made
- '<name of a builtin Python conversion function>': the function is applied
    to the value string. Examples are 'tuple', 'list', 'int', 'long', 'float'.
- '': the value is evaluated as a Python expression "as is" using the eval()
    function.

Notes:
- Because of the use of the eval() function for known and unknown types
    conversion, many complex possibilities are left open.
- To keep results predictable and debugging easy (and to avoid being taken too
    far away from the topic of this module), eval() is always used with empty
    dictionaries."""

    # I am quite happy of having isolated this code in a function, because it
    # proved very useful in the command line analysis too.

    result = defaults.copy()

    for item in values.keys():
        if item in definitions.keys():
            item_type = definitions[item]
        else:
            item_type = 'string'

        if not item_type:
            result[item] = eval(values[item], {})
        elif item_type == 'string':
            result[item] = values[item]
        else:
            result[item] = eval(item_type + '(' + values[item] + ')', {})

    return result

def read_configfile(filename, separator = ':'):
    """read_configfile(filename, separator = ':')
This function reads a configuration file, extracting <keyword>, <value> pairs
to a dictionary.

Parameters:
- filename: name of the file to be read
- separator: character used to separate the <keyword> from the <value>

Return value:
- a dictionary containing the <keyword>, <value> pairs.

Notes about the configuration file format:
- A <keyword>, <value> pair must fit on one line.
- A line, a keyword, or a value may start with as many blank characters as fit,
    those will be ignored and won't appear in the result.
- Comments start with a "#".
- One can not mix values and comment on a line."""
    # This will store values read in the file as strings.
    result = {}

    # Opening the file for reading    
    file = open(filename, 'r')

    # try/finally block to ensure the file is ALWAYS correctly closed.    
    try:

        # Reading the file line by line.
        while 1:
            # Reading a line. A line may start/end with blanks that we wish
            # to ignore.
            line_with_blanks = file.readline()

            # If nothing is read, the end of line has been reached, we get out
            # of the loop.
            if not line_with_blanks: break
            
            # Stripping the leading/trailing blanks.
            line = line_with_blanks.strip()

            # if the line was only made of blanks, or starts with a "#", it is
            # of no interest.
            if not line or (line[0] == '#'): continue

            # Seperating the <keyword> from the <value>.
            split_line = line.split(separator, 1)

            # Stripping leading/trailing blanks from the keyword and the
            # value. Storing the value as a string in "values".
            keyword = split_line[0].strip()
            result[keyword] = split_line[1].strip()

    # The file is now useless. We close it.
    finally:
        file.close()

    return result
