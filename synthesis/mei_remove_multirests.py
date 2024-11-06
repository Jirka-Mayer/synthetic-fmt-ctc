import xml.etree.ElementTree as ET


# NOTE: tutorial on rests in MEI:
# https://music-encoding.org/tutorials/104-rests.html
#
# Find all of these:
# <multiRest num="123"/>
#
# And replace them with:
# <mRest/>


MEI_XMLNS = "http://www.music-encoding.org/ns/mei"
MULTIREST_TAG = "{http://www.music-encoding.org/ns/mei}multiRest"
MEASURE_REST_TAG = "{http://www.music-encoding.org/ns/mei}mRest"


def mei_remove_multirests(original_mei: str) -> str:
    """Finds all multi-measure rests and replaces
    them with whole-measure rests."""

    # parse incomming MEI
    root = ET.fromstring(original_mei)

    # find all multirests and replace them
    for rest in root.findall(".//" + MULTIREST_TAG):
        rest.tag = MEASURE_REST_TAG # change the tag
        rest.attrib.clear() # clear attributes

    # serialize modified XML tree
    ET.register_namespace(
        prefix="",
        uri=MEI_XMLNS
    )
    patched_mei = str(ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True
    ), "utf-8")
    return patched_mei
