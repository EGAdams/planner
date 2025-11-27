#!/usr/bin/env python3
"""
Helper script to programmatically update Smart Menu configurations
Can add items, search for items, and modify existing items
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

class MenuUpdater:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> List[Dict]:
        """Load menu configuration."""
        if not self.config_path.exists():
            return []
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def save(self):
        """Save configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
        print(f"✅ Saved to {self.config_path}")
    
    def find_item(self, title: str, items: Optional[List[Dict]] = None) -> Optional[Dict]:
        """Find menu item by title (recursive search)."""
        if items is None:
            items = self.config
        
        for item in items:
            if item.get('title') == title:
                return item
            if 'submenu' in item:
                found = self.find_item(title, item['submenu'])
                if found:
                    return found
        return None
    
    def add_item(self, item: Dict, parent_title: Optional[str] = None):
        """Add menu item. If parent_title specified, adds to that submenu."""
        if parent_title:
            parent = self.find_item(parent_title)
            if not parent:
                print(f"❌ Parent '{parent_title}' not found")
                return False
            if 'submenu' not in parent:
                parent['submenu'] = []
            parent['submenu'].append(item)
        else:
            self.config.append(item)
        return True
    
    def remove_item(self, title: str, items: Optional[List[Dict]] = None) -> bool:
        """Remove menu item by title."""
        if items is None:
            items = self.config
        
        for i, item in enumerate(items):
            if item.get('title') == title:
                items.pop(i)
                return True
            if 'submenu' in item:
                if self.remove_item(title, item['submenu']):
                    return True
        return False
    
    def list_items(self, items: Optional[List[Dict]] = None, indent: int = 0):
        """List all menu items in tree format."""
        if items is None:
            items = self.config
        
        for item in items:
            prefix = "  " * indent
            title = item.get('title', 'Unknown')
            item_type = "submenu" if 'submenu' in item else "action"
            print(f"{prefix}- {title} ({item_type})")
            
            if 'submenu' in item:
                self.list_items(item['submenu'], indent + 1)


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python update_menu.py <config.json> list")
        print("  python update_menu.py <config.json> add '<title>' '<action>' [parent_title]")
        print("  python update_menu.py <config.json> remove '<title>'")
        sys.exit(1)
    
    config_path = sys.argv[1]
    command = sys.argv[2]
    
    updater = MenuUpdater(config_path)
    
    if command == "list":
        print(f"Menu structure in {config_path}:\n")
        updater.list_items()
    
    elif command == "add":
        if len(sys.argv) < 5:
            print("Usage: add '<title>' '<action>' [parent_title]")
            sys.exit(1)
        
        title = sys.argv[3]
        action = sys.argv[4]
        parent = sys.argv[5] if len(sys.argv) > 5 else None
        
        new_item = {
            "title": title,
            "action": action,
            "working_directory": "/home/adamsl/planner/smart_menu"
        }
        
        if updater.add_item(new_item, parent):
            updater.save()
            print(f"✅ Added '{title}'")
    
    elif command == "remove":
        if len(sys.argv) < 4:
            print("Usage: remove '<title>'")
            sys.exit(1)
        
        title = sys.argv[3]
        if updater.remove_item(title):
            updater.save()
            print(f"✅ Removed '{title}'")
        else:
            print(f"❌ Item '{title}' not found")

if __name__ == "__main__":
    main()
