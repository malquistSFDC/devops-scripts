# TODO -
# - Manage Login IP Hours and Login IP Ranges
# - Manage permission removal
import xml.etree.ElementTree as ET
import shutil
import glob

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

            # Create list of elements from profile whose tags are listed in the tag list
            changed_profile_elements: list[ET.Element[str]] = []
            for tag in tag_list:
                element_with_tag = changed_metadata_root.findall(f"xmlns:{tag}", ns)
                if len(element_with_tag) > 0:
                    changed_profile_elements += element_with_tag

            # If no elements are found, throw an exception
            if len(changed_profile_elements) == 0:
                raise Exception(f"There are no elements to add to {full_metadata}")

            # For each element in the changed_profile_elements tree, check if the element is
            # in the full profile tree. If true, replace the element in the full tree with the
            # updated version of the element. Otherwise, add the element to the full tree.
            for element in changed_profile_elements:
                element_tag = element.tag.split('}')[1]

                # Set the element identifier. For layoutAssignments, the format will vary if
                # a record type is being assigned to the layout. Use the recordType tag as the
                # identifier if the layoutAssignment element contains a recordType tag. Otherwise,
                # use the layout tag.
                name_tag = tag_dict[element_tag]
                if metadata_type == 'profiles' and element_tag == 'layoutAssignments' and len(element) > 1:
                    name_tag = 'recordType'
                element_identifier = element.find(f"xmlns:{name_tag}", ns).text

                element_in_full_tree = full_metadata_root.find(f"./xmlns:{element_tag}/xmlns:{name_tag}[.='{element_identifier}']/..", ns)
                if element_in_full_tree is not None:
                    full_metadata_root.remove(element_in_full_tree)
                full_metadata_root.append(element)
            
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
