
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
import copy
import time

class OrgDate:
    """Functions for date management"""

    format = 0
    TIMED = 1
    DATED = 2
    WEEKDAYED = 4
    ACTIVE = 8
    INACTIVE = 16

    def __init__(self,value=None):
        """
        Initialisation of an OrgDate element.
        """
        if value != None:
            self.set_value(value)

    def set_value(self,value):
        """
        Setting the value of this element (automatic recognition of format)
        """
        # Checking whether it is an active date-time or not
        if value[0]=="<":
            self.format = self.format | self.ACTIVE
            value = re.findall("(?:<)(.*)(?:>)",value)[0]
        elif value[0]=="[":
            self.format = self.format | self.INACTIVE
            value = re.findall("(?:\[)(.*)(?:\])",value)[0]
        # Checking if it is a date, a date+time or only a time
        value_splitted = value.split()

        timed = re.compile(".*?:.*?")
        dated = re.compile(".*?-.*?-.*?")

        if timed.findall(value):
            self.format = self.format | self.TIMED
        if dated.findall(value):
            self.format = self.format | self.DATED

        if len(value_splitted) == 3 :
            # We have a three parts date so it's dated, timed and weekdayed
            self.format = self.format | self.WEEKDAYED
            self.value = time.strptime(value_splitted[0]+" "+value_splitted[2],"%Y-%m-%d %H:%M")
        elif len(value_splitted) == 2 and (self.format & self.DATED) and not (self.format & self.TIMED):
            # We have a two elements date that is dated and not timed. So we must have a dated weekdayed item
            self.format = self.format | self.WEEKDAYED
            self.value = time.strptime(value_splitted[0],"%Y-%m-%d")
        elif self.format & self.TIMED:
            # We have only a time
            self.value = time.strptime(value,"%H:%M")
        elif self.format & self.DATED:
            self.value = time.strptime(value,"%Y-%m-%d")            

    def get_value(self):
        """
        Get the timestamp as a text according to the format
        """
        if self.format & self.ACTIVE:
            pre = "<"
            post = ">"
        elif self.format & self.INACTIVE:
            pre = "["
            post = "]"
        else:
            pre = ""
            post = ""

        if self.format & self.DATED:
            # We have a dated event
            dateformat = "%Y-%m-%d"
            if self.format & self.WEEKDAYED:
                # We have a weekday
                dateformat = dateformat + " %a"
            if self.format & self.TIMED:
                # We have a time also
                dateformat = dateformat + " %H:%M"

            return pre+time.strftime(dateformat,self.value)+post

        elif self.format & self.TIMED:
            # We have a time only
            timestr = time.strftime("%H:%M",self.value)
            if timestr[0] == '0':
                return timestr[1:]
            return pre+timestr+post

class OrgPlugin:
    """
    Generic class for all plugins
    """
    def __init__(self):
        """ Generic initialization """
        self.treated = True
        self.keepindent = True # By default, the plugin system stores the indentation before the treatment
        self.keepindent_value = ""

    def treat(self,current,line):
        """ This is a wrapper function for _treat. Asks the plugin if he can manage this kind of line. Returns True if it can """
        self.treated = True
        if self.keepindent :
            self.keepindent_value = line[0:len(line)-len(line.lstrip(" \t"))] # Keep a trace of the indentation
            return self._treat(current,line.lstrip(" \t"))
        else:
            return self._treat(current,line)

    def _treat(self,current,line):
        """ This is the function used by the plugin for the management of the line. """
        self.treated = False
        return current

    def _append(self,current,element):
        """ Internal function that adds to current. """
        if self.keepindent and hasattr(element,"set_indent"):
            element.set_indent(self.keepindent_value)
        return current.append(element)

    def close(self,current):
        """ A wrapper function for closing the module. """
        self.treated = False
        return self._close(current)
    def _close(self,current):
        """ This is the function used by the plugin to close everything that have been opened. """
        self.treated = False
        return current

class OrgElement:
    """
    Generic class for all Elements excepted text and unrecognized ones
    """ 
    def __init__(self):
        self.content=[]
        self.parent=None
        self.level=0
        self.indent = ""

    def append(self,element):
        # TODO Check validity
        self.content.append(element)
        # Check if the element got a parent attribute
        # If so, we can have childrens into this element
        if hasattr(element,"parent"):
            element.parent = self
        return element

    def set_indent(self,indent):
        """ Transfer the indentation from plugin to element. """
        self.indent = indent

    def output(self):
        """ Wrapper for the text output. """
        return self.indent+self._output()
    def _output(self):
        """ This is the function really used by the plugin. """
        return ""

    def __str__(self):
        """ Used to return a text when called. """
        return self.output()

class OrgClock(OrgPlugin):
    """Plugin for Clock elements"""
    def __init__(self):
        OrgPlugin.__init__(self)
        self.regexp = re.compile("(?:\s*)CLOCK:(?:\s*)((?:<|\[).*(?:>||\]))--((?:<|\[).*(?:>||\])).*=>\s*(.*)")
    def _treat(self,current,line):
        clocked = self.regexp.findall(line)
        if clocked:
            self._append(current,self.Element(clocked[0][0], clocked[0][1], clocked[0][2]))
        else:
            self.treated = False
        return current
   
    class Element(OrgElement):
        """Clock is an element taking into account CLOCK elements"""
        TYPE = "CLOCK_ELEMENT"
        def __init__(self,start="",stop="",duration=""):
            OrgElement.__init__(self)
            self.start = OrgDate(start)
            self.stop = OrgDate(stop)
            self.duration = OrgDate(duration)
        def _output(self):
            """Outputs the Clock element in text format (e.g CLOCK: [2010-11-20 Sun 19:42]--[2010-11-20 Sun 20:14] =>  0:32)"""
            return "CLOCK: " + self.start.get_value() + "--"+ self.stop.get_value() + " =>  "+self.duration.get_value()+"\n"

class OrgSchedule(OrgPlugin):
    """Plugin for Schedule elements"""
    # TODO: Need to find a better way to do this
    def __init__(self):
        OrgPlugin.__init__(self)

        self.regexp_scheduled = re.compile("SCHEDULED: ((<|\[).*?(>|\]))")
        self.regexp_deadline = re.compile("DEADLINE: ((<|\[).*?(>|\]))")
        self.regexp_closed = re.compile("CLOSED: ((<|\[).*?(>|\]))")
    def _treat(self,current,line):
        scheduled = self.regexp_scheduled.findall(line)
        deadline = self.regexp_deadline.findall(line)
        closed = self.regexp_closed.findall(line)
  
        if scheduled != []:
            scheduled = scheduled[0][0]
        if closed != []:
            closed = closed[0][0]
        if deadline != []:
            deadline = deadline[0][0]

        if scheduled or deadline or closed:
            self._append(current,self.Element(scheduled, deadline,closed))
        else:
            self.treated = False
        return current

    class Element(OrgElement):
        """Schedule is an element taking into account DEADLINE, SCHEDULED and CLOSED parameters of elements"""
        DEADLINE = 1
        SCHEDULED = 2
        CLOSED = 4
        TYPE = "SCHEDULE_ELEMENT"
        def __init__(self,scheduled=[],deadline=[],closed=[]):
            OrgElement.__init__(self)
            self.type = 0
  
            if scheduled != []:
                self.type = self.type | self.SCHEDULED
                self.scheduled = OrgDate(scheduled)
            if deadline != []:
                self.type = self.type | self.DEADLINE
                self.deadline = OrgDate(deadline)
            if closed  != []:
                self.type = self.type | self.CLOSED
                self.closed = OrgDate(closed)
  
        def _output(self):
            """Outputs the Schedule element in text format (e.g SCHEDULED: <2010-10-10 10:10>)"""
            output = ""
            if self.type & self.SCHEDULED:
                output = output + "SCHEDULED: "+self.scheduled.get_value()+" "
            if self.type & self.DEADLINE:
                output = output + "DEADLINE: "+self.deadline.get_value()+" "
            if self.type & self.CLOSED:
                output = output + "CLOSED: "+self.closed.get_value()+" "
            if output != "":
                output = output.rstrip() + "\n"
            return output

class OrgDrawer(OrgPlugin):
    """A Plugin for drawers"""
    def __init__(self):
        OrgPlugin.__init__(self)
        self.regexp = re.compile("^(?:\s*?)(?::)(\S.*?)(?::)\s*(.*?)$")
    def _treat(self,current,line):
        drawer = self.regexp.search(line)
        if isinstance(current, OrgDrawer.Element): # We are in a drawer
            if drawer:
                if drawer.group(1) == "END": # Ending drawer
                    current = current.parent
                elif drawer.group(2): # Adding a property
                    self._append(current,self.Property(drawer.group(1),drawer.group(2)))
            else: # Adding text in drawer
                self._append(current,line.rstrip("\n"))
        elif drawer: # Creating a drawer
            current = self._append(current,OrgDrawer.Element(drawer.group(1)))
        else:
            self.treated = False
            return current
        return current # It is a drawer, change the current also (even if not modified)
    
    class Element(OrgElement):
        """A Drawer object, containing properties and text"""
        TYPE = "DRAWER_ELEMENT"
        def __init__(self,name=""):
            OrgElement.__init__(self)
            self.name = name
        def _output(self):
            output = ":" + self.name + ":\n"
            for element in self.content:
                output = output + str(element) + "\n"
            output = output + self.indent + ":END:\n"
            return output
    class Property(OrgElement):
        """A Property object, used in drawers."""
        def __init__(self,name="",value=""):
            OrgElement.__init__(self)
            self.name = name
            self.value = value
        def _output(self):
            """Outputs the property in text format (e.g. :name: value)"""
            return ":" + self.name + ": " + self.value

class OrgTable(OrgPlugin):
    """A plugin for table managment"""
    def __init__(self):
        OrgPlugin.__init__(self)
        self.regexp = re.compile("^\s*\|")
    def _treat(self,current,line):
        table = self.regexp.match(line)
        if table:
            if not isinstance(current,self.Element):
                current = current.append(self.Element())
            current.append(line.rstrip().strip("|").split("|"))
        else:
            if isinstance(current,self.Element):
                current = current.parent
            self.treated = False
        return current

    class Element(OrgElement):
        """
        A Table object
        """
        TYPE = "TABLE_ELEMENT"
        def __init__(self):
            OrgElement.__init__(self)
        def _output(self):
            output = ""
            for element in self.content:
                output = output + "|"
                for cell in element:
                    output = output + str(cell) + "|"
                output = output + "\n"
            return output

class OrgNode(OrgPlugin):
    def __init__(self):
        OrgPlugin.__init__(self)
        self.regexp = re.compile("^(\*+)\s*(\[.*\])?\s*(.*)$")
        self.keepindent = False # If the line starts by an indent, it is not a node
    def _treat(self,current,line):
        heading = self.regexp.findall(line)
        if heading: # We have a heading

            if current.parent :
                current.parent.append(current)
  
                  # Is that a new level ?
            if (len(heading[0][0]) > current.level): # Yes
                parent = current # Parent is now the current node
            else:
                parent = current.parent # If not, the parent of the current node is the parent
                # If we are going back one or more levels, walk through parents
                while len(heading[0][0]) < current.level:
                    current = current.parent
                    parent = current.parent
            # Creating a new node and assigning parameters
            current = OrgNode.Element() 
            current.level = len(heading[0][0])
            current.heading = re.sub(":([\w]+):","",heading[0][2]) # Remove tags
            current.priority = heading[0][1]
            current.parent = parent
                  
                  # Looking for tags
            heading_without_links = re.sub(" \[(.+)\]","",heading[0][2])
            current.tags = re.findall(":([\w]+):",heading_without_links)
        else:
            self.treated = False
        return current
    def _close(self,current):
        # Add the last node
        if current.level>0:
            current.parent.append(current)

    class Element(OrgElement):
        # Defines an OrgMode Node in a structure
        # The ID is auto-generated using uuid.
        # The level 0 is the document itself
        TYPE = "NODE_ELEMENT"    
        def __init__(self):
            OrgElement.__init__(self)
            self.content = []       
            self.level = 0
            self.heading = ""
            self.priority = ""
            self.tags = []
          # TODO  Scheduling structure
  
        def _output(self):
            output = ""
            
            if hasattr(self,"level"):
                output = output + "*"*self.level
  
            if self.parent is not None:
                output = output + " "
                if self.priority:
                    output = output + self.priority + " "
                output = output + self.heading
  
                for tag in self.tags:
                    output= output + ":" + tag + ":"
  
                output = output + "\n"
    
            for element in self.content:
                output = output + element.__str__()
  
            return output
        def append_clean(self,element):
            if isinstance(element,list):
                self.content.extend(element)
            else:
                self.content.append(element)
            self.reparent_cleanlevels(self)
        def reparent_cleanlevels(self,element=None,level=None):
            """
            Reparent the childs elements of 'element' and make levels simpler.
            Useful after moving one tree to another place or another file.
            """
            if element == None:
                element = self.root
            if hasattr(element,"level"):
                if level == None:
                    level = element.level
                else:
                    element.level = level

            if hasattr(element,"content"):
                for child in element.content:
                    if hasattr(child,"parent"):
                        child.parent = element
                        self.reparent_cleanlevels(child,level+1)

class OrgDataStructure(OrgElement):
    """
    Data structure containing all the nodes
    The root property contains a reference to the level 0 node
    """
    root = None
    TYPE = "DATASTRUCTURE_ELEMENT"
    def __init__(self):
        OrgElement.__init__(self)
        self.plugins = []
        self.load_plugins(OrgTable(),OrgDrawer(),OrgNode(),OrgSchedule(),OrgClock())
        # Add a root element
        # The root node is a special node (no parent) used as a container for the file
        self.root = OrgNode.Element()
        self.root.parent = None
        self.level = 0

    def load_plugins(self,*arguments,**keywords):
        """
        Used to load plugins inside this DataStructure
        """
        for plugin in arguments:
            self.plugins.append(plugin)
    def load_from_file(self,name):
        """
        Used to load an org-file inside this DataStructure
        """
        current = self.root
        file = open(name,'r')

        for line in file:
            
            for plugin in self.plugins:
                current = plugin.treat(current,line)
                if plugin.treated: # Plugin found something
                    treated = True
                    break;
                else:
                    treated = False
            if not treated and line is not None: # Nothing special, just content
                current.append(line)

        for plugin in self.plugins:
            current = plugin.close(current)
        file.close()

    def save_to_file(self,name,node=None):
        """
        Used to save an org-file corresponding to this DataStructure
        """
        output = open(name,'w')
        if node == None:
            node = self.root
        output.write(str(node))
        output.close()
