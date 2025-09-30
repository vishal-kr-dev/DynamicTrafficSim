import xml.etree.ElementTree as ET
import sys

def find_trip(route_file, vehicle_id):
    """Finds and prints the details of a specific trip in a route file."""
    try:
        tree = ET.parse(route_file)
        root = tree.getroot()

        # Use an XPath search to find the trip element with the matching id
        trip = root.find(f".//trip[@id='{vehicle_id}']")

        if trip is not None:
            from_edge = trip.get('from')
            to_edge = trip.get('to')
            print("="*30)
            print(f"Found Trip Details for Vehicle '{vehicle_id}':")
            print(f"  - From Edge: {from_edge}")
            print(f"  - To Edge:   {to_edge}")
            print("="*30)
        else:
            print(f"Error: Could not find a trip with id='{vehicle_id}' in {route_file}.")

    except FileNotFoundError:
        print(f"Error: The file '{route_file}' was not found.")
    except ET.ParseError:
        print(f"Error: Could not parse the XML file '{route_file}'.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python inspect_trip.py <path_to_route_file> <vehicle_id>")
        sys.exit(1)

    find_trip(sys.argv[1], sys.argv[2])