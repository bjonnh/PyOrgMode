
# -*- encoding: utf-8 -*-
##############################################################################
#
#    PyOrgMode, a python module for treating with orgfiles
#    Copyright (C) 2010 Jonathan BISSON (bissonjonathan on the google thing).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""
The PyOrgMode class is able to read,modify and create orgfiles. The internal
representation of the file allows the use of orgfiles easily in your projects.
"""

import re
import string

class OrgElement:
    """
    Generic class for all Elements excepted text and unrecognized ones
    """
    def __init__(self):
        self.content=[]
        self.parent=None
    def append(self,element):
        # TODO Check validity
        self.content.append(element)
        # Check if the element got a parent attribute
        # If so, we can have childrens into this element
        if hasattr(element,"parent"):
            element.parent = self
        return element

class Property(OrgElement):
    """
    A Property object, used in drawers.
    """
    def __init__(self,name="",value=""):
        OrgElement.__init__(self)
        self.name = name
        self.value = value
    def __str__(self):
        """
        Outputs the property in text format (e.g. :name: value)
        """
        return ":" + self.name + ": " + self.value

class Schedule(OrgElement):
    """
    Schedule is an element taking into account DEADLINE and SCHEDULED elements
    """
    DEADLINE = 1
    SCHEDULED = 2
    def __init__(self,type="",date=""):
        OrgElement.__init__(self)
        self.date = date
        self.type = 0
        if type == "DEADLINE":
            self.type = self.DEADLINE
        elif type == "SCHEDULED":
            self.type = self.SCHEDULED

    def __str__(self):
        """
        Outputs the Schedule element in text format (e.g SCHEDULED: <2010-10-10 10:10>)
        """
        if self.type == self.DEADLINE:
            output = "DEADLINE:"
        elif self.type == self.SCHEDULED:
            output = "SCHEDULED:"
        return output + " " + self.date + "\n"

class Drawer(OrgElement):
    """
    A Drawer object, containing properties and text
    """
    # TODO has_property, get_property
    def __init__(self,name=""):
        OrgElement.__init__(self)
        self.name = name
    def __str__(self):
        output = ":" + self.name + ":\n"
        for element in self.content:
            output = output + str(element) + "\n"
        output = output + ":END:\n"
        return output

class Node(OrgElement):
    # Defines an OrgMode Node in a structure
    # The ID is auto-generated using uuid.
    # The level 0 is the document itself

    def __init__(self):
        OrgElement.__init__(self)
        self.content = []       
        self.level = 0
        self.heading = ""
        self.priority = ""
        self.tags = []
        # TODO  Scheduling structure

    def __str__(self):
        output = ""

        if hasattr(self,"level"):
            output = output + "*"*self.level

        if self.parent is not None:
            output = output + " "
            if self.priority :
                output = output + self.priority + " "
            output = output + self.heading

            for tag in self.tags:
                output= output + ":" + tag + ":"

            output = output + "\n"
  
        for element in self.content:
            output = output + element.__str__()

        return output

class DataStructure:
    """
    Data structure containing all the nodes
    The root property contains a reference to the level 0 node
    """

    root = None

    def append(self,node):
        if node.parent is None: # Node has no parent (so it is the level 0 node)
            self.root = node # So parent is the first added node
        else:
            node.parent.append(node)

    def load_from_file(self,name):
        current = Node()
        parent = None
        file = open(name,'r')

        re_drawer = re.compile("^(?:\s*?)(?::)(\S.*?)(?::)\s*(.*?)$")
        re_heading = re.compile("^(\*+)\s*(\[.*\])?\s*(.*)$")

        re_scheduled = re.compile("(?:\s*)(SCHEDULED|DEADLINE)(?::\s*)(<.*?>)(?:\s.*|$)")

        current_drawer = None
        for line in file:
            heading = re_heading.findall(line)

            drawer = re_drawer.search(line)
            scheduled = re_scheduled.findall(line)

            if isinstance(current, Drawer):
                if drawer:
                    if drawer.group(1) == "END":
                        current = current.parent
                    elif drawer.group(2):
                        current.append(Property(drawer.group(1),drawer.group(2)))
                else:
                    current.append(line.rstrip("\n"))
            elif drawer:
                current = current.append(Drawer(drawer.group(1)))

            elif heading: # We have a heading
                self.append(current) # We append the current node as it is done

                # Is that a new level ?
                if (len(heading[0][0]) > current.level): # Yes
                    parent = current # Parent is now the current node

                # If we are going back one or more levels, walk through parents
                while len(heading[0][0]) < current.level:
                    current = current.parent

                # Creating a new node and assigning parameters
                current = Node() 
                current.level = len(heading[0][0])
                current.heading = re.sub(":([\w]+):","",heading[0][2]) # Remove tags
                current.priority = heading[0][1]
                current.parent = parent
                
                # Looking for tags
                heading_without_links = re.sub(" \[(.+)\]","",heading[0][2])
                current.tags = re.findall(":([\w]+):",heading_without_links)

            elif scheduled:
                current.append(Schedule(scheduled[0][0], scheduled[0][1]))
            else: # Nothing special, just content
                if line is not None:
                    current.append(line)

        # Add the last node
        if current.level>0:
            self.append(current)

        file.close()

    def save_to_file(self,name):
        output = open(name,'w')
        output.write(str(self.root))
        output.close()
