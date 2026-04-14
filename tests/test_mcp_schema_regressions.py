from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_tool_generator(module_path: Path):
    previous_modules = {
        name: sys.modules.get(name)
        for name in ("schema_resolver", "tool_generator", "http_executor", "config")
    }
    for name in previous_modules:
        sys.modules.pop(name, None)
    sys.path.insert(0, str(module_path))
    try:
        from tool_generator import generate_tools

        return generate_tools, previous_modules, str(module_path)
    except Exception:
        sys.path.remove(str(module_path))
        for name, module in previous_modules.items():
            sys.modules.pop(name, None)
            if module is not None:
                sys.modules[name] = module
        raise


def _restore_modules(module_path: str, previous_modules: dict[str, object | None]) -> None:
    sys.path.remove(module_path)
    for name, module in previous_modules.items():
        sys.modules.pop(name, None)
        if module is not None:
            sys.modules[name] = module


class McpSchemaRegressionTest(unittest.TestCase):
    def test_tmf622_create_product_order_uses_direct_body_and_resolves_nested_refs(self) -> None:
        spec = {
            "swagger": "2.0",
            "paths": {
                "/productOrder": {
                    "post": {
                        "operationId": "createProductOrder",
                        "parameters": [
                            {
                                "name": "productOrder",
                                "in": "body",
                                "required": True,
                                "schema": {"$ref": "#/definitions/ProductOrder_Create"},
                            }
                        ],
                    }
                }
            },
            "definitions": {
                "ProductOrder_Create": {
                    "type": "object",
                    "required": ["productOrderItem"],
                    "properties": {
                        "productOrderItem": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/ProductOrderItem"},
                        }
                    },
                },
                "ProductOrderItem": {
                    "type": "object",
                    "properties": {
                        "productOffering": {"$ref": "#/definitions/ProductOfferingRef"}
                    },
                },
                "ProductOfferingRef": {
                    "allOf": [
                        {"$ref": "#/definitions/EntityRef"},
                        {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "@type": {"type": "string"},
                            },
                        },
                    ]
                },
                "EntityRef": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "href": {"type": "string"},
                    },
                },
            },
        }
        module_path = REPO_ROOT / "TMF622/source/ProductOrderCaptureValidation/MCPServerMicroservice"
        generate_tools, previous_modules, path_entry = _load_tool_generator(module_path)
        try:
            from http_executor import _split_arguments

            schema = generate_tools(spec)["create_product_order"]["tool"].inputSchema
            _, _, wrapped_body = _split_arguments(
                "/productOrder",
                spec["paths"]["/productOrder"]["post"]["parameters"],
                {"productOrder": {"productOrderItem": [{"id": "1"}]}},
            )
        finally:
            _restore_modules(path_entry, previous_modules)

        encoded = json.dumps(schema)
        self.assertNotIn("productOrder", schema["properties"])
        self.assertEqual(schema["required"], ["productOrderItem"])
        self.assertNotIn('"$ref"', encoded)
        self.assertNotIn("Schema depth limit reached", encoded)
        offering_schema = schema["properties"]["productOrderItem"]["items"]["properties"]["productOffering"]
        self.assertEqual(offering_schema["properties"]["name"]["type"], "string")
        self.assertEqual(wrapped_body, {"productOrderItem": [{"id": "1"}]})

    def test_tmf620_product_offering_price_discriminator_refs_are_resolved(self) -> None:
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/productOffering": {
                    "post": {
                        "operationId": "createProductOffering",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ProductOffering_FVO"}
                                }
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "ProductOffering_FVO": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "productOfferingPrice": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/ProductOfferingPriceRefOrValue_FVO"
                                },
                            },
                        },
                    },
                    "ProductOfferingPriceRefOrValue_FVO": {
                        "type": "object",
                        "oneOf": [
                            {"$ref": "#/components/schemas/ProductOfferingPrice_FVO"},
                            {"$ref": "#/components/schemas/ProductOfferingPriceRef_FVO"},
                        ],
                        "discriminator": {
                            "propertyName": "@type",
                            "mapping": {
                                "ProductOfferingPrice": "#/components/schemas/ProductOfferingPrice_FVO",
                                "ProductOfferingPriceRef": "#/components/schemas/ProductOfferingPriceRef_FVO",
                            },
                        },
                    },
                    "ProductOfferingPrice_FVO": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "priceType": {"type": "string"},
                            "@type": {"type": "string"},
                        },
                    },
                    "ProductOfferingPriceRef_FVO": {
                        "type": "object",
                        "required": ["id"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "@type": {"type": "string"},
                        },
                    },
                }
            },
        }
        module_path = REPO_ROOT / "TMF620/source/ProductCatalogManagement/MCPServerMicroservice"
        generate_tools, previous_modules, path_entry = _load_tool_generator(module_path)
        try:
            schema = generate_tools(spec)["create_product_offering"]["tool"].inputSchema
        finally:
            _restore_modules(path_entry, previous_modules)

        price_schema = schema["properties"]["productOfferingPrice"]["items"]
        encoded = json.dumps(price_schema)
        self.assertNotIn('"$ref"', encoded)
        self.assertNotIn("#/components/schemas", encoded)
        self.assertNotIn("Schema depth limit reached", encoded)
        self.assertEqual(len(price_schema["oneOf"]), 2)
        self.assertEqual(price_schema["oneOf"][1]["properties"]["id"]["type"], "string")
        self.assertEqual(price_schema["discriminator"], {"propertyName": "@type"})


if __name__ == "__main__":
    unittest.main()
