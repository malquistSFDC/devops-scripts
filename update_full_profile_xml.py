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
print("Pseudocode only")