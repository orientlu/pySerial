#!/usr/bin/env python
# coding=utf-8

def set_change(msg):
    msg[0] = msg[0] + 1	
    data = msg[2:]
    print data
    data[0] = data[0] + 1
    print data
    print msg

if __name__ == "__main__":

    print "1 --------------------------------------------" 
    list = [1, 2, 3, 4, 5, 6]
    print list
    set_change(list)
    print list

    print "2 --------------------------------------------" 
    str = "010203040506"
    print str
    strlist = []
    i = 0
    while i < len(str):
        strlist.append(int(str[i:i+2], 16))
        i += 2
    print strlist

    print "3 --------------------------------------------" 
    list2 = [1, 2, 3, 4, 5, 6]
    print list2
    list2.append(7)
    print list2
    del list2[0:3]
    print list2
    list2.append(8)
    print list2
    print "4 --------------------------------------------" 
