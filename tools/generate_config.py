#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generate configuration files from templates for local development.

This script creates settings.local.toml and .secrets.toml files with placeholder values
to help users get started quickly without having to figure out the correct format.
"""

import argparse
import os
import shutil
from pathlib import Path


def create_config_files(config_dir, force=False):
    """Create configuration files from templates."""
    config_path = Path(config_dir)
    template_path = config_path / "templates"

    # Check if template directory exists
    if not template_path.exists():
        print(f"❌ Error: Template directory not found: {template_path}")
        print("Make sure the config/templates directory exists with template files.")
        return [], []

    files = [
        "settings.local.toml",
        ".secrets.toml",
    ]

    created_files = []
    skipped_files = []

    for filename in files:
        template_file_path = template_path / filename
        target_file_path = config_path / filename

        # Check if template file exists
        if not template_file_path.exists():
            print(f"❌ Error: Template file not found: {template_file_path}")
            continue

        # Skip if target file exists and force is False
        if target_file_path.exists() and not force:
            print(f"❗️ Skipping existing file: {target_file_path}")
            skipped_files.append(target_file_path)
            continue

        # Copy the template file to the target file
        shutil.copy2(template_file_path, target_file_path)
        created_files.append(target_file_path)
        print(f"✅ Created: {target_file_path}")

    if created_files:
        print("\n🎉 Configuration files created successfully!")
        print("❗️ Please update the placeholder values with your own settings.")
    elif not skipped_files:
        print("\n❗️ No configuration files were created.")

    return created_files, skipped_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate configuration files from templates."
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument(
        "--config-dir",
        "-d",
        default="config",
        help="Directory where configuration files will be created (default: config)",
    )

    args = parser.parse_args()

    create_config_files(args.config_dir, args.force)


if __name__ == "__main__":
    main()
