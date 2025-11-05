"""
This script maintains all full copies of the org's profiles. The script accepts a list
of profile paths as an argument. Each profile in the list is parsed to an ElementTree
and compared to its corresponding full profile (located outside of the force-app directory).
The full version of the profile is updated with new or modified permissions.

Pseudocode:
For each modified profile:
    Parse the profile and full profile into ElementTrees.
    Find all of the following permission blocks:
        Application Visibility
        Apex Class Access
        Field-Level Security
        Object-Level Security
        Layout Assignments
        Record Type Visibility
        Tab Visibility
    For each permission block type:
        Compare list of permission blocks with the full profile's list
        Add new permissions and replace existing permissions
    Write modified full profile tree to full profile xml file.
"""
import xml.etree.ElementTree as ET
import glob

xmlns = "http://soap.sforce.com/2006/04/metadata"
full_profiles_dir = "full-metadata/profiles"
changed_profiles_dir = "force-app/main/default/profiles" # temporary path
ns = {'xmlns': xmlns}
tag_dict = {
    'applicationVisibilities': 'application',
    'classAccesses': 'apexClass',
    'fieldPermissions': 'field',
    'flowAccesses': 'flow',
    'layoutAssignments': 'layout',
    'objectPermissions': 'object',
    'pageAccesses': 'apexPage',
    'recordTypeVisibilities': 'recordType',
    'tabVisibilities': 'tab'
}
tag_list = tag_dict.keys()

ET.register_namespace("", xmlns)

changed_profiles = glob.glob("*.profile-meta.xml", root_dir=changed_profiles_dir)

for profile in changed_profiles:
    full_profile = f"{full_profiles_dir}/{profile}"
    changed_profile = f"{changed_profiles_dir}/{profile}"

    try:
        full_profile_tree = ET.parse(full_profile)
        full_profile_root = full_profile_tree.getroot()

        changed_profile_tree = ET.parse(changed_profile)
        changed_profile_root = changed_profile_tree.getroot()

        changed_profile_elements: list[ET.Element[str]] = []
        for tag in tag_list:
            element_with_tag = changed_profile_root.findall(f"xmlns:{tag}", ns)
            if len(element_with_tag) > 0:
                changed_profile_elements += element_with_tag
        
        if len(changed_profile_elements) == 0:
            raise Exception(f"There are elements to add to {full_profile}")

        for element in changed_profile_elements:
            element_tag = element.tag.split('}')[1]
            name_tag = tag_dict[element_tag]
            element_identifier = element.find(f"xmlns:{name_tag}", ns).text

            element_in_full_tree = full_profile_root.find(f"./xmlns:{element_tag}/xmlns:{name_tag}[.='{element_identifier}']/..", ns)
            if element_in_full_tree is not None:
                full_profile_root.remove(element_in_full_tree)
            full_profile_root.append(element)
        
        # Format and sort the full profile tree.
        full_profile_root[:] = sorted(full_profile_root, key = lambda child: child.tag)
        ET.indent(full_profile_root, space='    ')

        # Write the modified profile tree to its xml file.
        full_tree_xml_string = ET.tostring(full_profile_root, encoding="unicode", xml_declaration=True)
        full_tree_xml_string_double_quotes = full_tree_xml_string.replace("'", "\"", 4)
        with open(full_profile, "w") as file:
            file.write(full_tree_xml_string_double_quotes)
        print(f"Successfully wrote to {full_profile}")
    except ET.ParseError as pe:
        print(f"Could not parse the modified label tree: {pe}")
    except Exception as e:
        print(e)
