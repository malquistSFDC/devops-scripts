"""
This script maintains all full copies of the following metadata types:
- Profiles
- SharingRules
- CustomLabels
Each metadata file in 'changed_metadata_root_dir' that is one of the above types is parsed
to an ElementTree and compared to its corresponding full metadata file in 'full_metadata_root_dir', 
which is stored separately from the Salesforce project directory.
The full version of the metadata file is updated with new or modified elements.
"""

# TODO -
# - Manage Login IP Hours and Login IP Ranges
# - Manage element removal
import xml.etree.ElementTree as ET
import shutil
import glob

def create_element_map(element: ET.Element[str], tag_dict: dict[str, str]):
    element_tag = element.tag.split('}')[1]
    name_tag = tag_dict[element_tag]
    if element.tag == 'layoutAssignments' and len(element) > 1:
        name_tag = 'recordType'
    element_identifier = element.find(f"xmlns:{name_tag}", ns).text
    return (element_tag, element_identifier)

def create_tree_dict_with_keys(tag_dict, tag_list, element_tree):
    filtered_metadata_elements: list[ET.Element[str]] = \
                filter(lambda element: element.tag.split('}')[1] in tag_list, element_tree.findall("."))
    metadata_dict: dict[(str, str), ET.Element[str]] = \
                {create_element_map(element, tag_dict): element for element in filtered_metadata_elements}
    metadata_keys = set(metadata_dict.keys())
    return metadata_dict, metadata_keys

# --- VARIABLES ---
xmlns = "http://soap.sforce.com/2006/04/metadata"
full_metadata_root_dir = "full-metadata"
changed_metadata_root_dir = "force-app/main/default" # temporary path
ns = {'xmlns': xmlns}
metadata_dict = {
    'profiles': {
        'fileGlob': '*.profile-meta.xml',
        'tags': {
            'applicationVisibilities': 'application',
            'classAccesses': 'apexClass',
            'customMetadataTypeAccesses': 'name',
            'customPermissions': 'name',
            'customSettingAccesses': 'name',
            'externalDataSourceAccesses': 'externalDataSource',
            'fieldPermissions': 'field',
            'flowAccesses': 'flow',
            'layoutAssignments': 'layout',
            'objectPermissions': 'object',
            'pageAccesses': 'apexPage',
            'recordTypeVisibilities': 'recordType',
            'tabVisibilities': 'tab',
            'userPermissions': 'name'
        }
    },
    'labels': {
        'fileGlob': '*.labels-meta.xml',
        'tags': {
            'labels': 'fullName'
        }
    },
    'sharingRules': {
        'fileGlob': '*.sharingRules-meta.xml',
        'tags': {
            'sharingCriteriaRules': 'fullName'
        }
    }
}
metadata_list = metadata_dict.keys()

ET.register_namespace("", xmlns)

for metadata_type in metadata_list:
    changed_metadata_dir = f"{changed_metadata_root_dir}/{metadata_type}"
    full_metadata_dir = f"{full_metadata_root_dir}/{metadata_type}"
    changed_metadata_list = glob.glob(f"{metadata_dict[metadata_type]['fileGlob']}", root_dir=changed_metadata_dir)
    
    tag_dict: dict[str, any] = metadata_dict[metadata_type]['tags']
    tag_list = tag_dict.keys()

    # For each changed profile, add or replace the elements from the profile to its full copy in
    # the full profile directory. If there is no full copy version, copy the profile to the full
    # profile directory.
    for metadata in changed_metadata_list:
        full_metadata = f"{full_metadata_dir}/{metadata}"
        changed_metadata = f"{changed_metadata_dir}/{metadata}"

        try:
            full_metadata_tree = ET.parse(full_metadata)
            full_metadata_root = full_metadata_tree.getroot()

            changed_metadata_tree = ET.parse(changed_metadata)
            changed_metadata_root = changed_metadata_tree.getroot()

            # For both metadata trees, create a dictionary where the key is a tuple that contains the identifying tag
            # and the text in the identifying tag, and the value is the element. This strategy reduces the number of calls
            # to search the full metadata tree.
            full_metadata_dict, full_metadata_keys = create_tree_dict_with_keys(tag_dict, tag_list, full_metadata_root)
            changed_metadata_dict, changed_metadata_keys = create_tree_dict_with_keys(tag_dict, tag_list, changed_metadata_root)
            
            # Find elements that are in both metadata trees.
            elements_modified = full_metadata_keys.intersection(changed_metadata_keys)

            for element_tuple in changed_metadata_keys:
                if element_tuple in elements_modified:
                    full_metadata_root.remove(full_metadata_dict[element_tuple])
                full_metadata_root.append(changed_metadata_dict[element_tuple])
            
            # Format and sort the full profile tree.
            full_metadata_root[:] = sorted(full_metadata_root, key = lambda child: child.tag)
            ET.indent(full_metadata_root, space='    ')

            # Write the modified profile tree to its xml file.
            full_tree_xml_string = ET.tostring(full_metadata_root, encoding="unicode", xml_declaration=True)
            full_tree_xml_string_double_quotes = full_tree_xml_string.replace("'", "\"", 4)
            with open(full_metadata, "w") as file:
                file.write(full_tree_xml_string_double_quotes)
            print(f"Successfully wrote to {full_metadata}")
        except ET.ParseError as pe:
            print(f"Could not parse the modified label tree: {pe.with_traceback()}")
        except FileNotFoundError as fnfe:
            missing_filepath: str = fnfe.filename
            if missing_filepath.find(full_metadata_dir) >= 0:
                shutil.copyfile(changed_metadata, full_metadata)
                print(f"{missing_filepath} does not exist. Creating copy from force-app...")
            else:
                print(f"Could not find file {missing_filepath}: {fnfe.with_traceback()}")
        except Exception as e:
            print(f"Got error type {type(e)}: {e.with_traceback()}")
