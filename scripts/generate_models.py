#!/usr/bin/env python3
"""
Script to fetch OpenAPI spec, fix broken discriminators, and generate Pydantic models.

Usage:
    python scripts/generate_models.py
"""

import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


# Configuration
OPENAPI_URL = "http://astrox.cn:8765/openapi/v1.json"
OUTPUT_FILE = Path(__file__).parent.parent / "astrox" / "_models.py"

SUFFIX_WHITELIST = {'J2', 'SGP4', 'TLE4'}


def fetch_openapi_spec(url: str) -> dict[str, Any]:
    """Fetch OpenAPI spec from remote URL."""
    print(f"Fetching OpenAPI spec from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        spec = response.json()
        print(f"✓ Successfully fetched spec (version: {spec.get('info', {}).get('version', 'unknown')})")
        return spec
    except Exception as e:
        print(f"✗ Failed to fetch spec: {e}", file=sys.stderr)
        sys.exit(1)


def find_discriminators(obj: Any, path: str = "") -> list[tuple[str, dict]]:
    """Recursively find all discriminators in the spec."""
    results = []
    if isinstance(obj, dict):
        if 'discriminator' in obj:
            results.append((path, obj['discriminator']))
        for key, value in obj.items():
            results.extend(find_discriminators(value, f"{path}.{key}" if path else key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(find_discriminators(item, f"{path}[{i}]"))
    return results


def find_broken_discriminators(spec: dict[str, Any]) -> list[dict[str, str]]:
    """Find all broken discriminator mappings that reference non-existent schemas."""
    schemas = spec.get('components', {}).get('schemas', {})
    discriminators = find_discriminators(spec)

    broken = []
    for path, disc in discriminators:
        mapping = disc.get('mapping', {})
        if not mapping:
            continue

        for key, ref in mapping.items():
            # Extract schema name from $ref
            match = re.search(r'#/components/schemas/(.+)', ref)
            if match:
                schema_name = match.group(1)
                if schema_name not in schemas:
                    broken.append({
                        'path': path,
                        'discriminator_key': key,
                        'ref': ref,
                        'missing_schema': schema_name
                    })

    return broken


def normalize_schema(schema: dict[str, Any]) -> str:
    """
    Normalize a schema to a comparable string representation.
    Two schemas with identical structure will have the same normalized form.
    """
    # Create a deep copy and remove metadata that doesn't affect structure
    normalized = {}

    # Copy properties in sorted order
    if 'properties' in schema:
        normalized['properties'] = {
            k: {
                'type': v.get('type'),
                'description': v.get('description'),
                'enum': v.get('enum'),
                'format': v.get('format'),
                '$ref': v.get('$ref'),
                'items': v.get('items'),
                'allOf': v.get('allOf'),
                'oneOf': v.get('oneOf'),
                'anyOf': v.get('anyOf'),
            }
            for k, v in sorted(schema['properties'].items())
        }

    if 'required' in schema:
        normalized['required'] = sorted(schema['required'])

    if 'type' in schema:
        normalized['type'] = schema['type']

    if 'enum' in schema:
        normalized['enum'] = schema['enum']

    if 'allOf' in schema:
        normalized['allOf'] = schema['allOf']

    if 'oneOf' in schema:
        normalized['oneOf'] = schema['oneOf']

    if 'anyOf' in schema:
        normalized['anyOf'] = schema['anyOf']

    # Convert to JSON string for comparison
    return json.dumps(normalized, sort_keys=True)


def find_duplicate_schemas(spec: dict[str, Any]) -> dict[str, list[str]]:
    """
    Find duplicate schemas that have identical structure.
    Only considers numbered variants (Name, Name2, Name3) as duplicates.
    Returns a dict mapping canonical name -> list of duplicate names.
    """
    schemas = spec.get('components', {}).get('schemas', {})

    # Group schemas by their normalized form
    by_structure: dict[str, list[str]] = {}
    for name, schema in schemas.items():
        normalized = normalize_schema(schema)
        if normalized not in by_structure:
            by_structure[normalized] = []
        by_structure[normalized].append(name)

    # Filter to only keep numbered variant groups
    duplicates: dict[str, list[str]] = {}
    for names in by_structure.values():
        if len(names) <= 1:
            continue

        # Check if this group consists of numbered variants (Name, Name2, Name3, etc.)
        # Find potential base names by stripping trailing digits
        base_names: dict[str, list[str]] = {}  # base_name -> [Name, Name2, Name3, ...]

        for name in names:
            # Extract base name by removing trailing digit
            match = re.match(r'^(.+?)(\d+)?$', name)
            if match:
                base = match.group(1)
                if base not in base_names:
                    base_names[base] = []
                base_names[base].append(name)

        # Only process groups where all names share the same base
        if len(base_names) == 1:
            base, variants = list(base_names.items())[0]

            # Check if we have the unnumbered base name
            if base in variants:
                # Keep base, remove numbered variants
                canonical = base
                dups = [v for v in variants if v != base]
            else:
                # No base name exists, keep shortest numbered variant
                sorted_variants = sorted(variants, key=lambda x: (len(x), x))
                canonical = sorted_variants[0]
                dups = sorted_variants[1:]

            if dups:
                duplicates[canonical] = dups
        # else: names have different bases (like OrientationLVLH vs OrientationVNC), keep all

    return duplicates


def rename_numbered_schemas(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """
    Rename all numbered schemas (e.g., AccessInput2) to base name if base doesn't exist.
    Also updates discriminator mappings to use new names.

    Important: Preserves schemas with whitelisted suffixes (J2, SGP4, etc.) and
    only renames if all numbered variants are identical.

    Returns (updated_spec, renames_dict).
    """

    schemas = spec['components']['schemas']
    renames: dict[str, str] = {}
    ref_mapping: dict[str, str] = {}

    # Group schemas by base name
    by_base: dict[str, list[str]] = {}  # base -> [Name2, Name3, ...]

    for name in list(schemas.keys()):
        match = re.match(r'^(.+?)(\d+)$', name)
        if match:
            base = match.group(1)

            # Skip whitelisted suffixes (e.g., J2, SGP4)
            # Check if the name ends with a whitelisted suffix
            if any(name.endswith(wl) for wl in SUFFIX_WHITELIST):
                continue

            if base not in schemas:  # Base doesn't exist
                if base not in by_base:
                    by_base[base] = []
                by_base[base].append(name)

    # For each base, check if all numbered variants are identical
    to_rename = []
    for base, variants in by_base.items():
        if len(variants) == 1:
            # Only one variant, safe to rename
            to_rename.append((variants[0], base))
        else:
            # Multiple variants, check if they're all identical
            normalized_forms = [normalize_schema(schemas[v]) for v in variants]
            if len(set(normalized_forms)) == 1:
                # All identical, rename shortest to base
                sorted_variants = sorted(variants, key=lambda x: (len(x), x))
                to_rename.append((sorted_variants[0], base))
                print(f"  Note: {len(variants)} identical numbered variants found for '{base}', will rename '{sorted_variants[0]}' to '{base}'")
            else:
                # They're different, keep all as-is
                print(f"  Note: Multiple different numbered variants for '{base}' found, keeping all: {', '.join(sorted(variants))}")

    if to_rename:
        print(f"\nRenaming {len(to_rename)} numbered schema(s) to base names...")
        for old_name, new_name in to_rename:
            schemas[new_name] = schemas[old_name]
            del schemas[old_name]
            renames[old_name] = new_name
            ref_mapping[old_name] = new_name
            print(f"  ✓ Renamed '{old_name}' -> '{new_name}'")

    # Update all $ref references AND discriminator mappings throughout the spec
    if ref_mapping:
        def update_refs(obj: Any) -> Any:
            if isinstance(obj, dict):
                # Update $ref
                if '$ref' in obj:
                    ref = obj['$ref']
                    match = re.search(r'#/components/schemas/(.+)', ref)
                    if match:
                        schema_name = match.group(1)
                        if schema_name in ref_mapping:
                            obj['$ref'] = f"#/components/schemas/{ref_mapping[schema_name]}"

                # Update discriminator mappings
                if 'discriminator' in obj and 'mapping' in obj['discriminator']:
                    mapping = obj['discriminator']['mapping']
                    for key, ref in list(mapping.items()):
                        match = re.search(r'#/components/schemas/(.+)', ref)
                        if match:
                            schema_name = match.group(1)
                            if schema_name in ref_mapping:
                                mapping[key] = f"#/components/schemas/{ref_mapping[schema_name]}"

                return {k: update_refs(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [update_refs(item) for item in obj]
            else:
                return obj

        spec = update_refs(spec)

    return spec, renames


def remove_discriminator_from_any(spec: dict[str, Any]) -> dict[str, Any]:
    """
    Remove discriminator from fields that are typed as 'Any' (no schema ref).
    Pydantic V2 forbids discriminator on 'Any' fields.
    """
    print("\nScanning for 'Any' fields with discriminators...")

    schemas = spec.get('components', {}).get('schemas', {})
    count = 0

    for name, schema in schemas.items():
        if 'properties' not in schema:
            continue

        for prop_name, prop in schema['properties'].items():
            # Check if it has a discriminator but no $ref or exact type that supports it
            if 'discriminator' in prop:
                # If it doesn't have a $ref, acts like Any/Object
                if '$ref' not in prop and 'oneOf' not in prop:
                    # Remove discriminator
                    del prop['discriminator']
                    count += 1
                    print(f"  ✓ Removed discriminator from {name}.{prop_name} (typed as Any)")

    print(f"Removed discriminators from {count} fields.")
    return spec


def make_discriminator_fields_required(spec: dict[str, Any]) -> dict[str, Any]:
    """
    Make all discriminator fields required (non-nullable) in union member schemas.
    Pydantic V2 requires discriminator fields to be Literal types, not Literal | None.

    This searches for schemas that have properties with 'enum' of length 1
    (which become Literal fields) and makes them required if they're referenced
    in discriminated unions.
    """
    print("\nMaking discriminator fields non-nullable and required...")

    schemas = spec.get('components', {}).get('schemas', {})
    count = 0

    # Strategy: Find all schemas with single-value enum properties (these become Literal fields)
    # and make them required + non-nullable
    for schema_name, schema in schemas.items():
        if 'properties' not in schema:
            continue

        for prop_name, prop in schema['properties'].items():
            # Look for properties that have a single-value enum (becomes Literal)
            # These are likely discriminator fields
            if 'enum' in prop and len(prop['enum']) == 1:
                # Make it required
                if 'required' not in schema:
                    schema['required'] = []
                if prop_name not in schema['required']:
                    schema['required'].append(prop_name)
                    count += 1
                    print(f"  ✓ Made '{prop_name}' required in {schema_name}")

                # Remove nullable/None from type if present
                if 'type' in prop:
                    if isinstance(prop['type'], list) and 'null' in prop['type']:
                        prop['type'] = [t for t in prop['type'] if t != 'null']
                        if len(prop['type']) == 1:
                            prop['type'] = prop['type'][0]
                    # Also check for ['string', 'null'] pattern
                    if isinstance(prop['type'], list) and 'null' in prop['type']:
                        prop['type'] = [t for t in prop['type'] if t != 'null']

                # Remove nullable flag completely
                if 'nullable' in prop:
                    del prop['nullable']

                # Remove default None if present
                if 'default' in prop and prop['default'] is None:
                    del prop['default']

    print(f"Made {count} discriminator field(s) required and non-nullable.")
    return spec


def remove_duplicate_schemas(
    spec: dict[str, Any],
    duplicates: dict[str, list[str]]
) -> tuple[dict[str, Any], dict[str, str]]:
    """
    Remove duplicate schemas from the spec and update all $ref references.
    Returns (updated_spec, renames_dict) where renames_dict maps old_name -> new_name.
    """
    if not duplicates:
        return spec, {}

    print(f"\nFound {sum(len(v) for v in duplicates.values())} duplicate schema(s), removing...")

    schemas = spec['components']['schemas']
    renames: dict[str, str] = {}  # Track renames for header
    ref_mapping: dict[str, str] = {}  # All redirects for $ref updates

    for canonical, dups in duplicates.items():
        # Map all duplicates to canonical
        for dup in dups:
            ref_mapping[dup] = canonical

        # Remove duplicate schemas
        for dup in dups:
            if dup in schemas:
                del schemas[dup]
                print(f"  ✓ Removed '{dup}' (duplicate of '{canonical}')")

    # Update all $ref references throughout the spec
    def update_refs(obj: Any) -> Any:
        if isinstance(obj, dict):
            if '$ref' in obj:
                ref = obj['$ref']
                match = re.search(r'#/components/schemas/(.+)', ref)
                if match:
                    schema_name = match.group(1)
                    if schema_name in ref_mapping:
                        obj['$ref'] = f"#/components/schemas/{ref_mapping[schema_name]}"
            return {k: update_refs(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [update_refs(item) for item in obj]
        else:
            return obj

    spec = update_refs(spec)

    return spec, renames


def fix_discriminators(spec: dict[str, Any], broken: list[dict[str, str]]) -> dict[str, Any]:
    """Remove broken discriminator mappings from the spec."""
    if not broken:
        return spec

    print(f"\nFound {len(broken)} broken discriminator mapping(s), fixing...")

    # Group by path for easier removal
    removals_by_path: dict[str, list[str]] = {}
    for item in broken:
        path = item['path']
        key = item['discriminator_key']
        if path not in removals_by_path:
            removals_by_path[path] = []
        removals_by_path[path].append(key)

    # Navigate and fix each path
    for path, keys_to_remove in removals_by_path.items():
        # Parse the path and navigate to the discriminator
        parts = re.findall(r'([^.\[]+)(?:\[(\d+)\])?', path)

        current = spec
        for i, (key, index) in enumerate(parts):
            if i == len(parts) - 1:
                # Last part - this should be where 'discriminator' is
                if isinstance(current, dict) and key in current:
                    if 'discriminator' in current[key]:
                        mapping = current[key]['discriminator'].get('mapping', {})
                        for key_to_remove in keys_to_remove:
                            if key_to_remove in mapping:
                                del mapping[key_to_remove]
                                print(f"  ✓ Removed '{key_to_remove}' from {path}")
            else:
                # Navigate deeper
                if index:
                    current = current[key][int(index)]
                else:
                    current = current[key]

    return spec


def generate_models(spec: dict[str, Any], output_path: Path) -> bool:
    """Generate Pydantic models using datamodel-codegen."""
    print(f"\nGenerating Pydantic models to {output_path}...")

    # Save spec to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(spec, tmp, indent=2)
        tmp_path = tmp.name

    try:
        # Run datamodel-codegen
        cmd = [
            'datamodel-codegen',
            '--input', tmp_path,
            '--output', str(output_path),
            '--input-file-type', 'openapi',
            '--output-model-type', 'pydantic_v2.BaseModel',
            '--enum-field-as-literal', 'one',
            '--allow-population-by-field-name',  # Allow using both field name and alias
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            print(f"✗ datamodel-codegen failed:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False

        if result.stderr and 'Warning' not in result.stderr:
            print(f"Warnings/Output:\n{result.stderr}")

        print(f"✓ Successfully generated models ({output_path.stat().st_size / 1024:.1f} KB)")
        return True

    except subprocess.TimeoutExpired:
        print("✗ datamodel-codegen timed out", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Failed to run datamodel-codegen: {e}", file=sys.stderr)
        return False
    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


def update_header(
    output_path: Path,
    url: str,
    spec_version: str,
    broken_items: list[dict[str, str]],
    duplicates: dict[str, list[str]],
    renames: dict[str, str]
) -> None:
    """Update the generated file header with detailed information."""
    print(f"\nUpdating header in {output_path}...")

    # Read the generated file
    content = output_path.read_text()

    # Find the old header (first comment block)
    old_header_match = re.match(r'(# generated by datamodel-codegen:.*?\n(?:#.*?\n)*)', content, re.MULTILINE)

    # Build new header
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    new_header = f"""# Generated by datamodel-codegen
# Source: {url}
# API Version: {spec_version}
# Generated at: {timestamp}
"""

    if broken_items:
        new_header += "#\n# Auto-fixed broken discriminators:\n"
        # Group by missing schema
        by_schema: dict[str, list[str]] = {}
        for item in broken_items:
            schema = item['missing_schema']
            key = item['discriminator_key']
            if schema not in by_schema:
                by_schema[schema] = []
            by_schema[schema].append(key)

        for schema, keys in sorted(by_schema.items()):
            new_header += f"#   - Removed references to '{schema}' (keys: {', '.join(sorted(set(keys)))})\n"
    else:
        new_header += "#\n# No discriminator fixes were needed.\n"

    if renames:
        new_header += f"#\n# Auto-renamed {len(renames)} numbered schema(s) to base names:\n"
        for old_name, new_name in sorted(renames.items()):
            new_header += f"#   - '{old_name}' -> '{new_name}'\n"
    else:
        new_header += "#\n# No schemas renamed.\n"

    if duplicates:
        total_removed = sum(len(dups) for dups in duplicates.values())
        new_header += f"#\n# Auto-removed {total_removed} duplicate schema(s):\n"
        for canonical, dups in sorted(duplicates.items()):
            dup_list = ', '.join(sorted(dups))
            new_header += f"#   - Kept '{canonical}', removed: {dup_list}\n"
    else:
        new_header += "#\n# No duplicate schemas found.\n"

    new_header += "\n"

    # Replace old header
    if old_header_match:
        content = content[old_header_match.end():]

    # Write back
    output_path.write_text(new_header + content)
    print("✓ Header updated")


def main() -> None:
    """Main execution function."""
    print("=" * 70)
    print("ASTROX OpenAPI Model Generator")
    print("=" * 70)

    # Step 1: Fetch spec
    spec = fetch_openapi_spec(OPENAPI_URL)
    spec_version = spec.get('info', {}).get('version', 'unknown')
    original_schema_count = len(spec.get('components', {}).get('schemas', {}))

    # Step 2: Find and remove duplicate schemas
    print("\nChecking for duplicate schemas...")
    duplicates = find_duplicate_schemas(spec)
    renames_from_duplicates = {}

    if duplicates:
        total_dups = sum(len(dups) for dups in duplicates.values())
        print(f"Found {total_dups} duplicate schema(s) in {len(duplicates)} group(s)")
        spec, renames_from_duplicates = remove_duplicate_schemas(spec, duplicates)
    else:
        print("✓ No duplicate schemas found!")

    # Step 3: Rename numbered schemas to base names
    spec, renames_from_numbers = rename_numbered_schemas(spec)

    # Combine all renames
    all_renames = {**renames_from_duplicates, **renames_from_numbers}

    # Step 4: Find broken discriminators
    print("\nChecking for broken discriminator mappings...")
    broken = find_broken_discriminators(spec)

    if broken:
        print(f"Found {len(broken)} broken discriminator mapping(s):")
        for item in broken:
            print(f"  - {item['discriminator_key']} -> {item['missing_schema']}")
    else:
        print("✓ No broken discriminators found!")

    # Step 5: Fix broken discriminators
    if broken:
        spec = fix_discriminators(spec, broken)

    # Step 5b: Fix Any with discriminator
    spec = remove_discriminator_from_any(spec)

    # Step 5c: Make discriminator fields required
    spec = make_discriminator_fields_required(spec)

    # Summary
    final_schema_count = len(spec.get('components', {}).get('schemas', {}))
    print(f"\nSchema count: {original_schema_count} → {final_schema_count} (-{original_schema_count - final_schema_count})")

    # Step 6: Generate models
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    success = generate_models(spec, OUTPUT_FILE)

    if not success:
        sys.exit(1)

    # Step 7: Update header
    update_header(OUTPUT_FILE, OPENAPI_URL, spec_version, broken, duplicates, all_renames)

    print("\n" + "=" * 70)
    print("✓ Model generation complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
