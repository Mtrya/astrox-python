#!/usr/bin/env python3
"""Analyze if one-layer flattening is sufficient for all Input/Output models.

This script checks if all fields in Input/Output models are either:
1. Native types (str, int, float, bool, None)
2. Pydantic models
3. Lists/Unions of the above

Problem: If any field is a bare dict/Dict[str, Any], that means we need deeper flattening.
"""

import re
import yaml
from pathlib import Path
from typing import Set, Dict, List, Tuple
from collections import defaultdict


def load_openapi_spec(spec_path: Path) -> dict:
    """Load the OpenAPI spec."""
    with open(spec_path) as f:
        return yaml.safe_load(f)


def get_schema_ref_name(ref: str) -> str:
    """Extract schema name from $ref."""
    # '#/components/schemas/AccessInput2' -> 'AccessInput2'
    return ref.split('/')[-1]


def resolve_type(schema: dict, spec: dict, visited: Set[str] = None, is_ref: bool = False) -> str:
    """Resolve the actual type of a schema, following $refs.

    Returns a string representation of the type for analysis.

    Args:
        schema: The schema to analyze
        spec: The full OpenAPI spec
        visited: Set of schema names we've already visited (for circular ref detection)
        is_ref: True if this schema was reached via a $ref (means it's a named model)
    """
    if visited is None:
        visited = set()

    # Handle $ref - these are named schemas, treat as models
    if '$ref' in schema:
        ref_name = get_schema_ref_name(schema['$ref'])
        # Always treat $refs as models - don't recursively analyze them
        return f'Model({ref_name})'

    # Handle discriminated unions (oneOf/anyOf/allOf)
    if 'oneOf' in schema or 'anyOf' in schema or 'allOf' in schema:
        variants = schema.get('oneOf') or schema.get('anyOf') or schema.get('allOf')
        if variants and len(variants) > 0:
            # Check if all variants are $refs (typical discriminated union)
            if all('$ref' in v for v in variants):
                variant_names = [get_schema_ref_name(v['$ref']) for v in variants]
                return f'Union[{", ".join(variant_names)}]'
        return 'Union[...]'

    # Handle arrays
    if schema.get('type') == 'array':
        if 'items' in schema:
            item_type = resolve_type(schema['items'], spec, visited)
            return f'List[{item_type}]'
        return 'List[Any]'

    # Handle objects
    if schema.get('type') == 'object':
        # Check if it has properties (structured object -> should be a model)
        if 'properties' in schema:
            return 'InlineObject'  # Should be extracted as a model
        # Check if it has additionalProperties (dictionary)
        if 'additionalProperties' in schema:
            value_type = resolve_type(schema['additionalProperties'], spec, visited)
            return f'Dict[str, {value_type}]'
        # Plain object without properties -> dict
        return 'Dict[str, Any]'

    # Native types
    type_map = {
        'string': 'str',
        'integer': 'int',
        'number': 'float',
        'boolean': 'bool',
        'null': 'None',
    }

    schema_type = schema.get('type')

    # Handle type as list (e.g., ["string", "null"])
    if isinstance(schema_type, list):
        types = [type_map.get(t, t) for t in schema_type if t in type_map]
        if types:
            if len(types) == 1:
                return types[0]
            return f'Union[{", ".join(types)}]'
        return 'Any'

    if schema_type in type_map:
        return type_map[schema_type]

    # No type specified - could be Any
    return 'Any'


def analyze_model(model_name: str, model_schema: dict, spec: dict) -> Dict[str, str]:
    """Analyze a single model and return its field types.

    Returns: {field_name: type_string}
    """
    field_types = {}

    if 'properties' not in model_schema:
        return field_types

    for field_name, field_schema in model_schema['properties'].items():
        field_type = resolve_type(field_schema, spec)
        field_types[field_name] = field_type

    return field_types


def is_problematic_type(type_str: str) -> bool:
    """Check if a type is problematic (bare dict without model typing)."""
    problematic_patterns = [
        'Dict[str, Any]',
        'InlineObject',
        'Any',
    ]
    return any(pattern in type_str for pattern in problematic_patterns)


def main():
    spec_path = Path(__file__).parent.parent / 'docs' / 'internal' / 'astrox-web-api-260118-fixed.yaml'

    print(f"Loading OpenAPI spec from {spec_path}...")
    spec = load_openapi_spec(spec_path)

    schemas = spec['components']['schemas']

    # Filter for Input/Output models
    input_output_models = {
        name: schema
        for name, schema in schemas.items()
        if name.endswith('Input') or name.endswith('Output') or
           'Input' in name or 'Output' in name
    }

    print(f"\nFound {len(input_output_models)} Input/Output models\n")

    # Analyze each model
    problematic_models = defaultdict(list)
    all_results = {}

    for model_name, model_schema in input_output_models.items():
        field_types = analyze_model(model_name, model_schema, spec)
        all_results[model_name] = field_types

        # Check for problematic types
        for field_name, field_type in field_types.items():
            if is_problematic_type(field_type):
                problematic_models[model_name].append((field_name, field_type))

    # Report problematic models
    if problematic_models:
        print("=" * 80)
        print("PROBLEMATIC MODELS (have untyped dicts or inline objects):")
        print("=" * 80)

        for model_name in sorted(problematic_models.keys()):
            print(f"\n{model_name}:")
            for field_name, field_type in problematic_models[model_name]:
                print(f"  - {field_name}: {field_type}")
    else:
        print("✓ No problematic models found! One-layer flattening should be sufficient.")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Total Input/Output models analyzed: {len(input_output_models)}")
    print(f"Models with problematic fields: {len(problematic_models)}")

    # Count field types
    type_counts = defaultdict(int)
    for field_types in all_results.values():
        for field_type in field_types.values():
            # Normalize type for counting
            if field_type.startswith('Model('):
                type_counts['Pydantic Model'] += 1
            elif field_type.startswith('List['):
                type_counts['List'] += 1
            elif field_type.startswith('Union['):
                type_counts['Union'] += 1
            elif field_type.startswith('Dict['):
                type_counts['Dict'] += 1
            elif field_type in ['str', 'int', 'float', 'bool', 'None']:
                type_counts['Native Type'] += 1
            else:
                type_counts[field_type] += 1

    print("\nField type distribution:")
    for type_name, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {type_name}: {count}")

    # Save detailed report
    report_path = Path(__file__).parent.parent / 'docs' / 'model_depth_analysis.md'
    with open(report_path, 'w') as f:
        f.write("# Model Depth Analysis\n\n")
        f.write("Analysis of whether one-layer flattening is sufficient for all Input/Output models.\n\n")

        if problematic_models:
            f.write("## Problematic Models\n\n")
            f.write("These models have fields that are untyped dicts or inline objects:\n\n")

            for model_name in sorted(problematic_models.keys()):
                f.write(f"### {model_name}\n\n")
                for field_name, field_type in problematic_models[model_name]:
                    f.write(f"- `{field_name}`: `{field_type}`\n")
                f.write("\n")
        else:
            f.write("## Result\n\n")
            f.write("✓ **No problematic models found!** One-layer flattening should be sufficient.\n\n")

        f.write("## All Models\n\n")
        for model_name in sorted(all_results.keys()):
            f.write(f"### {model_name}\n\n")
            field_types = all_results[model_name]
            if field_types:
                for field_name, field_type in sorted(field_types.items()):
                    f.write(f"- `{field_name}`: `{field_type}`\n")
            else:
                f.write("*(no fields)*\n")
            f.write("\n")

    print(f"\nDetailed report saved to: {report_path}")


if __name__ == '__main__':
    main()
