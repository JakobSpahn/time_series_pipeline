import csv 
import re

def get_header(location):
    start = 0
    units = None
    with open(location, 'r') as f:
        while True:

            line = f.readline()
            
            sniffer = csv.Sniffer()
            Dialect = sniffer.sniff(line)
            delimiter = Dialect.delimiter
            
            groups = re.findall(r'(?:{0}{1})'.format(delimiter, delimiter),line)
            
            if(not groups):
                line = f.readline()
                numbers = sum(c.isdigit() for c in line)
                if(numbers < len(line)/2): #If line consists of less than 50% numbers, it is unit row
                    units = start+1
                break

            if(not line):
                break
            
            start += 1

    return start, units