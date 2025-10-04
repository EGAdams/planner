#!/usr/bin/env python3
"""
Generate categories.json for category-picker component from category structure
"""
import json

# New category structure
CATEGORIES = [
    {"id": 1, "name": "Church", "parent_id": None},
    {"id": 2, "name": "Housing", "parent_id": None},

    # CHURCH categories
    {"id": 100, "name": "Facility Payment", "parent_id": 1},

    {"id": 110, "name": "Facility Upkeep", "parent_id": 1},
    {"id": 111, "name": "Trash", "parent_id": 110},
    {"id": 112, "name": "Furnishings", "parent_id": 110},
    {"id": 113, "name": "Tools", "parent_id": 110},
    {"id": 114, "name": "Cleaning", "parent_id": 110},
    {"id": 115, "name": "Other", "parent_id": 110},

    {"id": 120, "name": "Utilities", "parent_id": 1},
    {"id": 121, "name": "Church Gas Bill", "parent_id": 120},
    {"id": 122, "name": "Church Water Bill", "parent_id": 120},
    {"id": 123, "name": "Church Electric Bill", "parent_id": 120},
    {"id": 124, "name": "Church Phone/Internet Bill", "parent_id": 120},
    {"id": 125, "name": "Other", "parent_id": 120},

    {"id": 130, "name": "Food & Supplies", "parent_id": 1},
    {"id": 131, "name": "Family Fare", "parent_id": 130},
    {"id": 132, "name": "Meijer", "parent_id": 130},
    {"id": 133, "name": "Restaurants (members/guests)", "parent_id": 130},
    {"id": 134, "name": "Other", "parent_id": 130},

    {"id": 140, "name": "Office", "parent_id": 1},
    {"id": 141, "name": "Supplies", "parent_id": 140},
    {"id": 142, "name": "Apple", "parent_id": 140},
    {"id": 143, "name": "Amazon", "parent_id": 140},
    {"id": 144, "name": "Postage", "parent_id": 140},
    {"id": 145, "name": "Furnishings", "parent_id": 140},
    {"id": 146, "name": "Other", "parent_id": 140},

    {"id": 150, "name": "Education / Music / TV", "parent_id": 1},
    {"id": 151, "name": "CDs", "parent_id": 150},
    {"id": 152, "name": "DVDs", "parent_id": 150},
    {"id": 153, "name": "Books", "parent_id": 150},
    {"id": 154, "name": "Amazon", "parent_id": 150},
    {"id": 155, "name": "Other", "parent_id": 150},

    {"id": 160, "name": "Travel & Transportation", "parent_id": 1},
    {"id": 161, "name": "Fuel", "parent_id": 160},
    {"id": 162, "name": "RJ gas", "parent_id": 161},
    {"id": 163, "name": "RM gas", "parent_id": 161},
    {"id": 164, "name": "Vehicle Maintenance", "parent_id": 160},
    {"id": 165, "name": "RJ wash/oil", "parent_id": 164},
    {"id": 166, "name": "RM wash/oil", "parent_id": 164},
    {"id": 167, "name": "Car repair (RJ)", "parent_id": 164},
    {"id": 168, "name": "Car repair (RM)", "parent_id": 164},
    {"id": 169, "name": "Vehicle Ownership", "parent_id": 160},
    {"id": 170, "name": "Car payment (general)", "parent_id": 169},
    {"id": 171, "name": "RJ Car Payment", "parent_id": 169},
    {"id": 172, "name": "RM Car Payment", "parent_id": 169},
    {"id": 173, "name": "License Tags", "parent_id": 169},
    {"id": 174, "name": "RJ", "parent_id": 173},
    {"id": 175, "name": "RM", "parent_id": 173},
    {"id": 176, "name": "Other", "parent_id": 173},
    {"id": 177, "name": "Trips", "parent_id": 160},
    {"id": 178, "name": "Airfare", "parent_id": 177},
    {"id": 179, "name": "Tolls", "parent_id": 177},
    {"id": 180, "name": "AAA", "parent_id": 177},
    {"id": 181, "name": "Hotels", "parent_id": 177},
    {"id": 182, "name": "Ministry-related travel", "parent_id": 177},
    {"id": 183, "name": "Other", "parent_id": 160},

    {"id": 190, "name": "Gifts & Love Offerings", "parent_id": 1},
    {"id": 191, "name": "EG Adams (work for River of Life)", "parent_id": 190},
    {"id": 192, "name": "Individuals", "parent_id": 190},
    {"id": 193, "name": "C Baker", "parent_id": 192},
    {"id": 194, "name": "A Baker", "parent_id": 192},
    {"id": 195, "name": "K Cook", "parent_id": 192},
    {"id": 196, "name": "R Menninga", "parent_id": 192},
    {"id": 197, "name": "J Menninga", "parent_id": 192},
    {"id": 198, "name": "K Roark", "parent_id": 192},
    {"id": 199, "name": "H Schneider", "parent_id": 192},
    {"id": 200, "name": "R Exposito", "parent_id": 192},
    {"id": 201, "name": "K Vander Vliet", "parent_id": 192},
    {"id": 202, "name": "J McKay", "parent_id": 192},
    {"id": 203, "name": "Sound (R Slawson)", "parent_id": 192},
    {"id": 204, "name": "Guest Speakers", "parent_id": 192},
    {"id": 205, "name": "Special occasions (name/occasion)", "parent_id": 192},
    {"id": 210, "name": "Ministries & Organizations", "parent_id": 190},
    {"id": 211, "name": "Chosen People", "parent_id": 210},
    {"id": 212, "name": "Columbia Orphanage", "parent_id": 210},
    {"id": 213, "name": "Segals in Israel", "parent_id": 210},
    {"id": 214, "name": "Intercessors for America", "parent_id": 210},
    {"id": 215, "name": "Samaritans Purse", "parent_id": 210},
    {"id": 216, "name": "Mel Trotter", "parent_id": 210},
    {"id": 217, "name": "Guiding Light", "parent_id": 210},
    {"id": 218, "name": "Right to Life", "parent_id": 210},
    {"id": 219, "name": "Johnsons in Dominican Republic", "parent_id": 210},
    {"id": 220, "name": "Jews for Jesus", "parent_id": 210},
    {"id": 221, "name": "Jewish Voice", "parent_id": 210},
    {"id": 222, "name": "Salvation Army", "parent_id": 210},
    {"id": 223, "name": "Other", "parent_id": 210},

    {"id": 230, "name": "Insurance", "parent_id": 1},
    {"id": 231, "name": "Building", "parent_id": 230},
    {"id": 232, "name": "Boiler", "parent_id": 230},
    {"id": 233, "name": "Vehicles", "parent_id": 230},

    {"id": 240, "name": "Staff & Benefits", "parent_id": 1},
    {"id": 241, "name": "Senior Pastors", "parent_id": 240},
    {"id": 242, "name": "RJ — Priority Health (medical expenses)", "parent_id": 241},
    {"id": 243, "name": "RM — Priority Health (medical expenses)", "parent_id": 241},

    {"id": 250, "name": "Misc.", "parent_id": 1},

    # HOUSING categories
    {"id": 300, "name": "Housing Payment", "parent_id": 2},
    {"id": 301, "name": "House Payment", "parent_id": 300},

    {"id": 310, "name": "Utilities", "parent_id": 2},
    {"id": 311, "name": "Housing Gas Bill", "parent_id": 310},
    {"id": 312, "name": "Housing Water Bill", "parent_id": 310},
    {"id": 313, "name": "Housing Trash Bill", "parent_id": 310},
    {"id": 314, "name": "Housing Electric Bill", "parent_id": 310},

    {"id": 320, "name": "Taxes & Insurance", "parent_id": 2},
    {"id": 321, "name": "House Taxes", "parent_id": 320},
    {"id": 322, "name": "House Insurance", "parent_id": 320},

    {"id": 330, "name": "Services", "parent_id": 2},
    {"id": 331, "name": "Service Professor", "parent_id": 330},

    {"id": 340, "name": "Upkeep", "parent_id": 2},
    {"id": 341, "name": "Décor / Furnishings", "parent_id": 340},
    {"id": 342, "name": "Tools", "parent_id": 340},
    {"id": 343, "name": "Repair", "parent_id": 340},
    {"id": 344, "name": "Outdoor & Lawn Care", "parent_id": 340},
    {"id": 345, "name": "Other", "parent_id": 340},

    {"id": 350, "name": "Misc.", "parent_id": 2},
]


def build_tree(categories):
    """Build hierarchical tree from flat category list"""
    # Create a map of id -> category node
    nodes = {}
    for cat in categories:
        nodes[cat['id']] = {
            'id': str(cat['id']),
            'label': cat['name'],
            'children': []
        }

    # Build tree structure
    roots = []
    for cat in categories:
        node = nodes[cat['id']]
        if cat['parent_id'] is None:
            roots.append(node)
        else:
            parent = nodes.get(cat['parent_id'])
            if parent:
                parent['children'].append(node)

    # Remove empty children arrays from leaf nodes
    def clean_tree(node):
        if not node['children']:
            del node['children']
        else:
            for child in node['children']:
                clean_tree(child)

    for root in roots:
        clean_tree(root)

    return roots


def main():
    from pathlib import Path
    tree = build_tree(CATEGORIES)

    # Write to categories.json
    script_dir = Path(__file__).parent
    output_path = script_dir / '../../category-picker/public/categories.json'
    output_path = output_path.resolve()

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {output_path}")
    print(f"   Top-level categories: {len(tree)}")
    print(f"   Total categories: {len(CATEGORIES)}")


if __name__ == "__main__":
    main()
