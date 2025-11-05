# This script maintains a clean version of the CustomLabels metadata file called FullCustomLabels.labels-meta.xml.
# The intent is to reduce merge conflicts with CustomLabels.labels-meta.xml in the force-app directory and
# source track all custom labels in the Salesforce org.
# When an incoming merge contains CustomLabels.labels-meta.xml, this script uses the ElementTree library to
# parse CustomLabels.labels-meta.xml and merge it into FullCustomLabels.labels-meta.xml.
# This script ensures that there are no duplicate labels.
#
# If duplicate labels have different values for the <value> tag, the script will always use
# the incoming version. The other option would be to fail the job and notify the owner of
# the commit of the potential conflicts (not in the scope of this script).
#
# Ideally, this script should be triggered by a GitLab job on the develop branch immediately after an MR
# that contains updates to CustomLabels.labels-meta.xml is merged.
 
# TODO List:
# - Exception handling if FullCustomLabels.labels-meta.xml does not exist
# - Remove deleted labels from FullCustomLabels

import xml.etree.ElementTree as ET 

xmlns = "http://soap.sforce.com/2006/04/metadata"
incoming_label_md_path = 'force-app/main/default/labels/CustomLabels.labels-meta.xml'
full_label_md_path = 'full-metadata/labels/FullCustomLabels.labels-meta.xml'
ns = {'xmlns': xmlns}

try:
    ET.register_namespace('', xmlns)

    new_label_tree = ET.parse(incoming_label_md_path)
    new_label_root = new_label_tree.getroot()

    full_tree = ET.parse(full_label_md_path)
    full_tree_root = full_tree.getroot()

    # For each Custom Label in CustomLabels, find a matching label name in FullCustomLabels.
    # If the label exists in FullCustomLabels, replace it with the new version of the label.
    # Add the value of <fullName> as an attribute to <labels>, then add the label block
    # to the FullCustomLabel tree.

    for new_label in new_label_root:
        full_name = new_label.find('xmlns:fullName', ns).text
        existing_child = full_tree_root.find(f"./xmlns:labels/fullName[.='{full_name}']/..", ns)
        if existing_child is not None:
            full_tree_root.remove(existing_child)
        full_tree_root.append(new_label)

    # Format and sort the FullCustomLabel tree.
    ET.indent(full_tree_root, space='    ')
    full_tree_root[:] = sorted(full_tree_root, key = lambda child: child.find("./xmlns:fullName", ns).text)

    # Write the modified FullCustomLabel tree to its xml file.
    full_tree_xml_string = ET.tostring(full_tree_root, encoding="unicode", xml_declaration=True)
    full_tree_xml_string_double_quotes = full_tree_xml_string.replace("'", "\"", 4)
    full_tree_xml_string_unescape = full_tree_xml_string_double_quotes.replace("'", "&apos;")
    with open(full_label_md_path, "w") as file:
        file.write(full_tree_xml_string_unescape)
    print(f"Successfully wrote to {full_label_md_path}")
except ET.ParseError as pe:
    print(f"Could not parse the modified label tree: {pe}")
except Exception as e:
    print(f"Caught {type(e)}: {e}")