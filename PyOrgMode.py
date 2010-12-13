import uuid
import re
import string

# TODO Error/Warning managment
# TODO Document every function correctly (docstrings)
# TODO Put things in a module
# TODO Check for other OS compatibility
# TODO Do a validator (input file MUST be output file, and check every function)
# TODO TODO tags (and others)
# TODO Priority
# TODO Git it
# TODO Add more types of data (currently: Drawer=DONE)
# BUG The drawers lost indentation and added spaces/tabs in properties :NON-BLOCKING::NO-DATA-LOSS: 

class Property():
    def __init__(self,name,value):
        self.name = name
        self.value = value
    def text_output(self):
        return ":" + self.name + ": " + self.value

class Drawer():
    # TODO has_property, get_property
    def __init__(self):
        self.id = uuid.uuid4()
        self.content = []
        self.name = ""
    def add_content(self,content):
        # TODO Check validity
        self.content.append(content)
    def text_output(self):
        output = ":" + self.name + ":\n"
        for element in self.content:
            # TODO Should use the "print" property to ease things up
            if type(element) == type(""):
                output = output + element + "\n"
            else:
                output = output + element.text_output() + "\n"
        output = output + ":END:\n"
        return output

class Node():
    # Defines an OrgMode Node in a structure
    # The ID is auto-generated using uuid.
    # The level 0 is the document itself

    def __init__(self):
        self.drawers = {}
        self.content = []       
        self.level = 0
        self.heading = ""
        self.tags = []
        # TODO  Scheduling structure
        self.parent = None
        self.childs = []
        self.id = uuid.uuid4() # Generate an random ID

    def set_id(self,id):
        self.id = id
    def get_id(self):
        return self.id

    def add_drawer(self,name):
        drawer = Drawer()
        id = drawer.id
        drawer.name = name
        self.drawers[id] = drawer
        self.content.append(drawer)
        return id
    def add_to_drawer(self,id,content):
        if id in self.drawers.keys():
            self.drawers[id].add_content(content)
    
    def set_heading(self,heading):
        self.heading = heading
    def get_heading(self):
        return self.heading

    def set_parent(self,parent):
        self.parent = parent
    def get_parent(self):
        return self.parent

    def has_tag(self,tag):
        return(tag in self.tags)
    def add_tag(self,tag):
        # TODO Check validity
        if not tag in self.tags:
            self.tags.append(tag)
    def remove_tag(self,tag):
        if tag in self.tags:
            self.tags.remove(tag)
    def set_tags_array(self,tags):
        self.tags = tags

    def append_content(self,content):
        self.content.append(content)
    def set_content(self,content):
        self.content = content
    def get_content(self):
        return self.content

    def append_child(self,child=None):
        self.childs.append(child)

    def private_text_output(self):
        output = ""
        if self.parent != None:
            
            output = " " + self.heading

            for tag in self.tags:
                output= output + ":" + tag + ":"
            output = output + "\n"
  
        if self.content:
            for element in self.content:
                if type(element) == type(""):
                    output = output + element + "\n"
                else:
                    output = output + element.text_output()
        return output

    def text_output(self,level=0,starting_level=0):
        output = ""
        for stars in range(0,level-starting_level):
            output = output + "*"
        output = output + self.private_text_output()
        if self.childs: # Has this node childs ?
            for child in self.childs: # So walk through each child
                output = output + child.text_output(child.level,starting_level)
        return output


class Datastructure:
    # Data structure containing all the nodes
    # The root property contains a reference to the level 0 node
    # TODO Move or delete nodes

    root = None

    def append(self,node):
        if (node.parent == None): # Node has no parent (so it is the level 0 node)
            if (self.root != None): # Level 0 node already defined ?
                print("Warning : Redefining the level 0 node !")
            self.root = node # So parent is the first added node
        else:
            node.parent.append_child(node)

    def load_from_file(self,name):
        current = Node()
        parent = None
        file = open(name,'r')

        re_heading_stars = re.compile("^(\*+)\s(.*?)\s*$")
        re_drawer = re.compile("^(?:\s*?)(?::)(\S.*?)(?::)\s*(.*?)$")
        re_heading = re.compile("(?:\*+)\s((.*?)(?:\s*.*?)\s*\s)((:\S(.*?)\S:$)|$)")
        # The (?!.*?\]) protects against links containing tags being considered as tags
        re_tags = re.compile("(?:::|\s:)(\S.*?\S)(?=:)(?!.*?\])")

        current_drawer = None
        for line in file:
            heading_stars = re_heading_stars.search(line)
            drawer = re_drawer.search(line)
       
            if drawer:
                if drawer.group(1) == "END":
                    if current_drawer != None: # If :END:, close drawer
                        current_drawer = None
                    else:
                        print("ERROR: :END: Before beginning of drawer")
                elif current_drawer != None and drawer.group(2):
                    current.add_to_drawer(current_drawer,
                                          Property(drawer.group(1),drawer.group(2)))
                elif drawer.group(1) and not drawer.group(2) and current_drawer == None:
                    current_drawer = current.add_drawer(drawer.group(1))
            elif current_drawer != None: # If a Drawer is open, add content to it
                current.add_to_drawer(current_drawer,line.rstrip("\n"))
            elif heading_stars: # We have a heading
                self.append(current) # We append the current node as it is done

                # Is that a new level ?
                if (len(heading_stars.group(1)) > current.level): # Yes
                    parent = current # Parent is now the current node

                # If we are going back one or more levels, walk through parents
                while len(heading_stars.group(1)) < current.level:
                    current = current.parent

                # Creating a new node and assigning parameters
                current = Node() 
                current.level = len(heading_stars.group(1))
                current.set_heading(re_heading.findall(line)[0][0].rstrip("\n"))
                current.set_parent(parent)
                
                # Looking for tags
                current.set_tags_array(re_tags.findall(line))
            else: # Nothing special, just content
                if line != None:
                    current.append_content(line.rstrip("\n"))

        # Add the last node
        if current.level>0:
            self.append(current)

        file.close()

    def save_to_file(self,name):
        output = open(name,'w')
        output.write(self.text_output())
        output.close()

    def text_output(self,node=None,level=0):
        if (node == None):
            node = self.root

        output = node.text_output()

        return output
