import xml.etree.ElementTree as ET
path = "../test_dir/WP3895_89784.gpml"
tree = ET.parse(path)
root = tree.getroot()
for child in root:
    print child.tag, child.attrib
    for grandchild in child:
        print grandchild.tag, grandchild.attrib