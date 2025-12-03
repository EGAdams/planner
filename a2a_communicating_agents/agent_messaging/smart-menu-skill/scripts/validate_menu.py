#!/usr/bin/env python3
"""
Validate Smart Menu Configuration
Checks JSON syntax, structure, and paths
"""

import json
import sys
from pathlib import Path

def validate_menu_config(config_path):
    """Validate menu configuration file."""
    errors = []
    warnings = []
    
    # Check file exists
    if not Path(config_path).exists():
        errors.append(f"Config file not found: {config_path}")
        return errors, warnings
    
    # Load and validate JSON
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return errors, warnings
    
    # Validate structure
    if not isinstance(config, list):
        errors.append("Config must be a JSON array")
        return errors, warnings
    
    # Validate each menu item
    def validate_item(item, path="root"):
        if not isinstance(item, dict):
            errors.append(f"{path}: Menu item must be an object")
            return
        
        # Check required fields
        if 'title' not in item:
            errors.append(f"{path}: Missing 'title' field")
        
        # Check for action or submenu
        has_action = 'action' in item
        has_submenu = 'submenu' in item
        
        if not has_action and not has_submenu:
            warnings.append(f"{path}: Item '{item.get('title', 'unknown')}' has no action or submenu")
        
        if has_action and has_submenu:
            errors.append(f"{path}: Item '{item.get('title', 'unknown')}' cannot have both action and submenu")
        
        # Validate working_directory paths
        if 'working_directory' in item:
            wd = item['working_directory']
            if wd.startswith('C:\\') or '\\' in wd:
                warnings.append(f"{path}: Windows path detected: '{wd}'. Use Linux paths for WSL.")
        
        # Recursively validate submenus
        if has_submenu:
            if not isinstance(item['submenu'], list):
                errors.append(f"{path}: 'submenu' must be an array")
            else:
                for i, sub_item in enumerate(item['submenu']):
                    validate_item(sub_item, f"{path} > {item.get('title', 'unknown')}[{i}]")
    
    for i, item in enumerate(config):
        validate_item(item, f"item[{i}]")
    
    return errors, warnings

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_menu.py <config.json>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    errors, warnings = validate_menu_config(config_path)
    
    print(f"Validating: {config_path}\n")
    
    if errors:
        print("ERRORS:")
        for err in errors:
            print(f"  - {err}")
        print()
    
    if warnings:
        print("WARNINGS:")
        for warn in warnings:
            print(f"  - {warn}")
        print()
    
    if not errors and not warnings:
        print("✅ Configuration is valid!")
        sys.exit(0)
    elif errors:
        print("❌ Validation failed with errors")
        sys.exit(1)
    else:
        print("⚠️  Validation passed with warnings")
        sys.exit(0)

if __name__ == "__main__":
    main()
