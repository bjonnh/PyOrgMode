
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
    RANGED = 32

    # TODO: Timestamp with repeater interval
    DICT_RE = {'start': '[[<]',
               'end':   '[]>]',
               'date':  '([0-9]{4})-([0-9]{2})-([0-9]{2})(\s+([\w]+))?',
               'time':  '([0-9]{2}):([0-9]{2})'}

    def __init__(self,value=None):
        """
        Initialisation of an OrgDate element.
        """
        if value != None:
            self.set_value(value)

    def parse_datetime(self, s):
        """
        Parses an org-mode date time string.
        Returns (timed, weekdayed, time_struct).
        """
        search_re = '(?P<date>{date})(\s+(?P<time>{time}))?'.format(
            **self.DICT_RE)
        s = re.search(search_re, s)
        weekdayed = (len(s.group('date').split()) > 1)
        if s.group('time'):
            return (True,
                    weekdayed,
                    time.strptime(
                        s.group('date').split()[0] + ' ' + s.group('time'),
                        '%Y-%m-%d %H:%M'))
        else:
            return (False,
                    weekdayed,
                    time.strptime(s.group('date').split()[0], '%Y-%m-%d'))

    def set_value(self,value):
        """
        Setting the value of this element (automatic recognition of format)
        """
        # Checking whether it is an active date-time or not
        if value[0] == '<':
            self.format |= self.ACTIVE
        elif value[0] == '[':
            self.format |= self.INACTIVE

        # time range on a single day
        search_re = ('{start}(?P<date>{date})\s+(?P<time1>{time})'
                     '-(?P<time2>{time}){end}').format(**self.DICT_RE)
        match = re.search(search_re, value)
        if match:
            #timed, weekdayed, date = self.parse_datetime(match.group('date'))
            #self.value = time.strptime(match.group('time1').split()[0], '%H:%M')
            #self.value = time.struct_time(date[:3] + self.value[3:])
            timed, weekdayed, self.value = self.parse_datetime(
                match.group('date') + ' ' + match.group('time1'))
            if weekdayed:
                self.format |= self.WEEKDAYED
            timed, weekdayed, self.end = self.parse_datetime(
                match.group('date') + ' ' + match.group('time2'))
            #self.end = time.strptime(match.group('time2').split()[0], '%H:%M')
            #self.end = time.struct_time(date[:3] + self.end[3:])
            self.format |= self.TIMED | self.DATED | self.RANGED
            return
        # date range over several days
        search_re = ('{start}(?P<date1>{date}(\s+{time})?){end}--'
                     '{start}(?P<date2>{date}(\s+{time})?){end}').format(
            **self.DICT_RE)
        match = re.search(search_re, value)
        if match:
            timed, weekdayed, self.value = self.parse_datetime(
                match.group('date1'))
            if timed:
                self.format |= self.TIMED
            if weekdayed:
                self.format |= self.WEEKDAYED
            timed, weekdayed, self.end = self.parse_datetime(
                match.group('date2'))
            self.format |= self.DATED | self.RANGED
            return
        # single date with no range
        search_re = '{start}(?P<datetime>{date}(\s+{time})?){end}'.format(
            **self.DICT_RE)
        match = re.search(search_re, value)
        if match:
            timed, weekdayed, self.value = self.parse_datetime(
                match.group('datetime'))
            self.format |= self.DATED
            if timed:
                self.format |= self.TIMED
            if weekdayed:
                self.format |= self.WEEKDAYED
            self.end = None

    def get_value(self):
        """
        Get the timestamp as a text according to the format
        """
        fmt_dict = {'time': '%H:%M'}
        if self.format & self.ACTIVE:
            fmt_dict['start'], fmt_dict['end'] = '<', '>'
        else:
            fmt_dict['start'], fmt_dict['end'] = '[', ']'
        if self.format & self.WEEKDAYED:
            fmt_dict['date'] = '%Y-%m-%d %a'
        else:
            fmt_dict['date'] = '%Y-%m-%d'
        if self.format & self.RANGED:
            if self.value[:3] == self.end[:3]:
                # range is between two times on a single day
                assert self.format & self.TIMED
                return (time.strftime(
                    '{start}{date} {time}-'.format(**fmt_dict), self.value) +
                        time.strftime('{time}{end}'.format(**fmt_dict),
                                      self.end))
            else:
                # range is between two days
                if self.format & self.TIMED:
                    return (time.strftime(
                        '{start}{date} {time}{end}--'.format(**fmt_dict),
                        self.value) +
                            time.strftime(
                                '{start}{date} {time}{end}'.format(**fmt_dict),
                                self.end))
                else:
                    return (time.strftime(
                        '{start}{date}{end}--'.format(**fmt_dict), self.value) +
                            time.strftime(
                                '{start}{date}{end}'.format(**fmt_dict),
                                self.end))
        else:
            # non-ranged time
            if self.format & self.TIMED:
                return time.strftime(
                    '{start}{date} {time}{end}'.format(**fmt_dict), self.value)
            else:
                return time.strftime(
                    '{start}{date}{end}'.format(**fmt_dict), self.value)

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

        self.regexp_scheduled = re.compile("SCHEDULED: ((<|\[).*?(>|\])(--(<|\[).*?(>|\]))?)")
        self.regexp_deadline = re.compile("DEADLINE: ((<|\[).*?(>|\])(--(<|\[).*?(>|\]))?)")
        self.regexp_closed = re.compile("CLOSED: ((<|\[).*?(>|\])(--(<|\[).*?(>|\]))?)")
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
        self.todo_list = ['TODO', 'DONE']
        self.keepindent = False # If the line starts by an indent, it is not a node
    def _treat(self,current,line):
        heading = self.regexp.findall(line)
        if heading: # We have a heading
            # Build the regexp for finding TODO items
            if self.todo_list:
                separator = ""
                regexp_string = "^(\*+)\s*("
                for todo_keyword in self.todo_list:
                    regexp_string += separator
                    separator = "|"
                    regexp_string += todo_keyword
                regexp_string += ")\s*(\[.*\])?\s*(.*)$"
                self.regexp_todo = re.compile(regexp_string)
                todo = self.regexp_todo.findall(line)

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

            if todo: # This item has a todo associated with it
                current.todo = todo[0][1]
                  
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
    def set_todo_states(self,new_todo_states):
        """
        Used to override the default list of todo states for any 
        OrgNode plugins in this object's plugins list. Expects 
        a list[] of strings as its argument.
        Setting to an empty list will disable TODO checking.
        """
        for plugin in self.plugins:
            if plugin.__class__ == OrgNode:
                plugin.todo_list = new_todo_states
    def get_todo_states(self):
        """
        Returns a list of lists of todo states, one entry for each instance
        of OrgNode in this object's plugins list. An empty list means that
        instance of OrgNode has TODO checking disabled.
        """
        all_todo_states = []
        for plugin in self.plugins:
            if plugin.__class__ == OrgNode:
                all_todo_states.append(plugin.todo_list)
        return all_todo_states
    def add_todo_state(self, new_state):
        """
        Appends a todo state to the list of todo states of any OrgNode 
        plugins in this objects plugins list.
        Expects a string as its argument.
        """
        for plugin in self.plugins:
            if plugin.__class__ == OrgNode:
                plugin.todo_list.append(new_state)
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
