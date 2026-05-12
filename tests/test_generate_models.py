from copy import deepcopy
import unittest

from scripts.generate_models import normalize_schema, rename_numbered_schemas


class GenerateModelsTests(unittest.TestCase):
    def test_normalize_schema_distinguishes_defaults(self) -> None:
        schema_a = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "default": 0}
            },
        }
        schema_b = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "default": 100}
            },
        }

        self.assertNotEqual(normalize_schema(schema_a), normalize_schema(schema_b))

    def test_normalize_schema_handles_nested_properties(self) -> None:
        schema_a = {
            "type": "object",
            "properties": {
                "payload": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "number", "default": 1.0}
                    },
                }
            },
        }
        schema_b = deepcopy(schema_a)
        schema_b["properties"]["payload"]["properties"]["value"]["default"] = 2.0

        self.assertNotEqual(normalize_schema(schema_a), normalize_schema(schema_b))

    def test_rename_numbered_schemas_skips_collisions(self) -> None:
        spec = {
            "components": {
                "schemas": {
                    "Thing1": {"type": "string", "description": "v1"},
                    "Thing2": {"type": "string", "description": "v2"},
                }
            }
        }

        updated, renames = rename_numbered_schemas(deepcopy(spec))

        self.assertEqual(renames, {})
        self.assertEqual(set(updated["components"]["schemas"].keys()), {"Thing1", "Thing2"})

    def test_rename_numbered_schemas_promotes_unique_variant(self) -> None:
        spec = {
            "components": {
                "schemas": {
                    "OrbitState2": {"type": "string"},
                }
            }
        }

        updated, renames = rename_numbered_schemas(deepcopy(spec))

        self.assertEqual(renames, {"OrbitState2": "OrbitState"})
        self.assertIn("OrbitState", updated["components"]["schemas"])
        self.assertNotIn("OrbitState2", updated["components"]["schemas"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
