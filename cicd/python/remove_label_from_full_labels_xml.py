# Removes labels listed in destructiveChanges.xml from FullCustomLabels.labels-meta.xml.

import xml.etree.ElementTree as ET 

xmlns = "http://soap.sforce.com/2006/04/metadata"
destructive_changes_path = 'manifest/destructiveChanges/destructiveChanges.xml'
full_label_md_path = 'full-metadata/labels/FullCustomLabels.labels-meta.xml'
ns = {'xmlns': xmlns}

ET.register_namespace('', xmlns)

destructive_changes_tree = ET.parse(destructive_changes_path)
destructive_changes_root = destructive_changes_tree.getroot()

full_tree = ET.parse(full_label_md_path)
full_tree_root = full_tree.getroot()

label_type_block = destructive_changes_root.find("./xmlns:types/xmlns:name[.='CustomLabel']/..", ns)
label_removal_list = label_type_block.findall("xmlns:members", ns)

for member in label_removal_list:
    label_name = member.text
    label_to_remove = full_tree_root.find(f"./xmlns:labels/xmlns:fullName[.='{label_name}']/..", ns)
    if label_to_remove is not None:
        full_tree_root.remove(label_to_remove)
    else:
        print(f"Label {label_name} is not in the full CustomLabel tree.")

# Format the FullCustomLabel tree.
ET.indent(full_tree_root, space='    ')

# Write the modified FullCustomLabel tree to its xml file.
full_tree_xml_string = ET.tostring(full_tree_root, encoding="UTF-8", xml_declaration=True)
with open(full_label_md_path, "wb") as file:
    file.write(full_tree_xml_string)
print(f"Successfully wrote to {full_label_md_path}")
