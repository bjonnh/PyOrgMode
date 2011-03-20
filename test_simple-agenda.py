
import PyOrgMode
import copy
def Get_Scheduled_Elements(element, data=[]):
    """
    Grab the data from all scheduled elements for all the tree defined by 'element' recursively.
    Returns all the elements as an array.
    """
    if hasattr(element,"content"):
        for child in element.content:
            if hasattr(child,"TYPE"):
                if child.TYPE == "SCHEDULE_ELEMENT":
                    # This element is scheduled, we are creating a copy of it
                    data.append(copy.deepcopy(child.parent))
            Get_Scheduled_Elements(child,data)
    return data

# Creating the input and output files data structures
input_file = PyOrgMode.DataStructure()
output_file = PyOrgMode.DataStructure()

# Loading from agenda.org file
input_file.load_from_file("agenda.org")

# Get the scheduled elements (those with SCHEDULE, DEADLINE in them, not in the node name)
scheduled_elements = Get_Scheduled_Elements(input_file.root)

# Assign these element to the root (reparent each elements recursively, relevel them cleanly)
output_file.root.append_clean(scheduled_elements)

output_file.save_to_file("test_scheduled_output.org")
