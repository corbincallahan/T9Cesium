import datetime
import json


def unix_to_iso_string(unix_seconds):
    """Take seconds from unix epoch and turn into ISO string"""
    return f"{datetime.datetime.utcfromtimestamp(unix_seconds).isoformat()}Z"


def get_strptime(time):
    """Get unix time from an ISO string"""
    try:
        return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")


def create_doc_packet_from_czmls(czmls):
    """
    Create Document Packet from a list of CZML objects that defines interval based on min/max times of provided packets
    This assumes that each packet has a position property
    You may need to do some filtering if your CZMLs do not match this!

    Tip: You can also define a position in the document packet to define a place for the camera to zoom to on load
    """
    position_types = ["cartesian", "cartographicDegrees", "cartographicRadians"]

    min_time = min(
        [
            packet["position"][list(packet["position"].keys())[0]][0]
            for packet in czmls
            if "position" in packet.keys()
            and list(packet["position"].keys())[0] in position_types
        ]
    )
    max_time = max(
        [
            packet["position"][list(packet["position"].keys())[0]][-4]
            for packet in czmls
            if "position" in packet.keys()
            and list(packet["position"].keys())[0] in position_types
        ]
    )

    return {
        "id": "document",
        "version": "1.0",
        "clock": {
            "interval": f"{min_time}/{max_time}",
            "multiplier": 1.0,
            "currentTime": f"{min_time}",
            "range": "CLAMPED",
        },
    }


# Convert a csv file with a series of timestamps and positions into czml
# Using line.split here for simplicity, could use pandas dataframes instead
# For this function to work:
# There should be no header row
# Each row should be in the format of timestamp,x,y,z (e.g. 1676502926,10000000,10000000,10000000)
# There should be a newline at the end of the file (a single blank line at the end)
def csv_to_czml(filepath, entity_name="Test Entity", position_type="cartesian"):
    """
    Convert a csv file with a series of timestamps and positions into czml
    Using line.split here for simplicity, could use pandas dataframes instead
    For this function to work:
        There should be no header row
        Each row should be in the format of timestamp,x,y,z (e.g. 1676502926,10000000,10000000,10000000)
        There should be a newline at the end of the file (a single blank line at the end)

    filepath -- Path to the csv file to read
    entity_name -- ID to use for the resulting entity
    position_type -- The coordinate frame to expect the data in. "cartesian", "cartographicDegrees", or "cartographicRadians"
    """
    if position_type not in ["cartesian", "cartographicDegrees", "cartographicRadians"]:
        raise Exception(
            "Position type must be cartesian, cartographicDegrees, or cartographicRadians"
        )

    positions = []
    color = {"rgba": [0, 199, 203, 255]}
    with open(filepath) as in_file:
        for line in in_file:
            t, x, y, z = line[:-1].split(",")[:4]
            positions.extend(
                [unix_to_iso_string(float(t)), float(x), float(y), float(z)]
            )
    return {
        "id": entity_name,
        "position": {position_type: positions},
        "point": {"pixelSize": 10.0, "color": color},
        "path": {
            "leadTime": 30000,
            "trailTime": 30000,
            "resolution": 45.0,
            "material": {"solidColor": {"color": color}},
        },
    }


def create_entity_with_polyline(endpoint1, endpoint2):
    """Create an entity with a polyline that will use the entities with the given IDs as endpoints"""
    color = {"rgba": [162, 0, 193, 255]}
    return {
        "id": f"polyline-{endpoint1}-{endpoint2}",
        "polyline": {
            "positions": {
                "references": [f"{endpoint1}#position", f"{endpoint2}#position"]
            },
            "material": {"solidColor": {"color": color}},
        },
    }


# Pass a list of strings with IDs of entities that you would like to use as vertices
# i.e. create_entity_with_polygon(["poly_vertex_1", "poly_vertex_2", "poly_vertex_3"])
# https://cesium.com/learn/cesiumjs/ref-doc/PolygonGraphics.html
def create_entity_with_polygon(vertices):
    """Create an entity with a polygon that will use the entities with the given IDs as vertices"""
    return {
        "id": "Polygon Entity",
        "polygon": {
            "positions": {"references": [f"{vertex}#position" for vertex in vertices]},
            "fill": True,
            "material": {"solidColor": {"color": {"rgba": [255, 255, 0, 50]}}},
            "outline": True,
            "outlineColor": {"rgba": [0, 0, 0, 100]},
            "perPositionHeight": True,  # Change this to false if you would like the polygon to stay on the Earth's surface or at another fixed altitude
        },
    }


# https://cesium.com/learn/cesiumjs/ref-doc/Ellipsoid.html
def create_entity_with_ellipsoid():
    """Create an entity with an ellipsoid surrounding it"""
    return {
        "id": "Ellipsoid Entity",
        "position": {
            "cartesian": [unix_to_iso_string(0), 10000000, 10000000, 10000000]
        },
        "ellipsoid": {
            "radii": {"cartesian": [500, 500, 500]},
            "material": {"solidColor": {"color": {"rgba": [0, 199, 203, 64]}}},
            "outline": True,
            "outlineColor": {"rgbaf": [0.0, 1.0, 0.5, 1.0]},
        },
    }


# https://cesium.com/learn/cesiumjs/ref-doc/Billboard.html
def create_entity_with_billboard():
    """Create an entity at the given positions with an ellipsoid surrounding it"""
    return {
        "id": "Billboard Entity",
        "position": {
            "cartesian": [unix_to_iso_string(0), 10000000, 10000000, 10000000]
        },
        "billboard": {
            "image": "https://t9hacks.org/images/logos/T9Hacks2022Logo.png",
            "scale": 0.2,
        },
    }


def write_to_file(czml, filename="sample.czml"):
    """Write a CZML dict to file"""
    json_string = json.dumps(czml)
    with open(filename, "w") as out_file:
        out_file.write(json_string)


def main():
    # czml = csv_to_czml("positions.csv", "first_id", "cartesian")
    # czml1 = csv_to_czml("positions1.csv", "second_id", "cartesian")
    # czml2 = csv_to_czml("positions2.csv", "third_id", "cartesian")
    # poly = create_entity_with_polygon(["first_id", "second_id", "third_id"])

    # all_entities = [czml, czml1, czml2, poly]

    czml = csv_to_czml("positions_lla.csv", position_type="cartographicDegrees")
    all_entities = [czml]

    doc_packet = create_doc_packet_from_czmls(all_entities)
    write_to_file([doc_packet, *all_entities])


if __name__ == "__main__":
    main()
