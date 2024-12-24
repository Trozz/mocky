import unittest
from unittest.mock import patch, MagicMock
import argparse
from flask import Flask
from src.main import MockyApp


# Base class to hold common logic
class BaseMockyAppTest(unittest.TestCase):
    def setUp(self):
        self.mock_parse_args = patch("argparse.ArgumentParser.parse_args").start()
        self.addCleanup(patch.stopall)

    def initialize_app(self, file: str):
        self.mock_parse_args.return_value = argparse.Namespace(
            file=file, port=8080, host="127.0.0.1", debug=True, otel=False
        )
        self.mocky_app = MockyApp()
        self.mocky_app.args = self.mock_parse_args.return_value
        self.app = self.mocky_app.app
        self.client = self.app.test_client()

    def get_and_assert(self, endpoint: str, status_code: int = 200):
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status_code)
        return response


class TestMockyApp(BaseMockyAppTest):
    def test_root(self):
        for file in ["openapi.yaml"]:
            with self.subTest(file=file):
                self.initialize_app(file)
                response = self.get_and_assert("/")
                self.assertEqual(
                    response.json, {"message": "Are you meant to be here?"}
                )

    def test_health(self):
        for file in ["openapi.yaml"]:
            with self.subTest(file=file):
                self.initialize_app(file)
                response = self.get_and_assert("/mocky/health")
                self.assertEqual(response.json, {"status": "ok"})

    def test_routes(self):
        for file in ["openapi.yaml"]:
            with self.subTest(file=file):
                self.initialize_app(file)
                response = self.get_and_assert("/mocky/routes")
                self.assertIsInstance(response.json, list)
                self.assertTrue(
                    any(
                        route["path"] == "/items"
                        and set(route["methods"]) == {"GET", "OPTIONS"}
                        for route in response.json
                    )
                )
                self.assertTrue(
                    any(
                        route["path"] == "/items"
                        and set(route["methods"]) == {"POST", "OPTIONS"}
                        for route in response.json
                    )
                )

    def test_load_and_register_routes(self):
        for file in ["openapi.yaml"]:
            with self.subTest(file=file):
                self.initialize_app(file)
                with patch("src.main.MockyApp._parse_openapi") as mock_parse_openapi:
                    mock_parse_openapi.return_value = {
                        "paths": {
                            "/test": {
                                "get": {
                                    "responses": {
                                        "200": {
                                            "content": {
                                                "application/json": {
                                                    "example": {"message": "test"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    self.mocky_app.load_and_register_routes()
                    response = self.client.get("/test")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json, {"message": "test"})

    def test_generate_default_response(self):
        for file in ["openapi.yaml"]:
            with self.subTest(file=file):
                self.initialize_app(file)
                response = self.mocky_app.generate_default_response(200)
                self.assertEqual(
                    response, {"status": 200, "message": "Default response"}
                )

    def test_convert_path(self):
        for file in ["openapi.yaml"]:
            with self.subTest(file=file):
                self.initialize_app(file)
                openapi_path = "/users/{user_id}/posts/{post_id}"
                flask_path = self.mocky_app.convert_path(openapi_path)
                self.assertEqual(flask_path, "/users/<user_id>/posts/<post_id>")

    def test_create_handler_get(self):
        for file in ["openapi.yaml"]:
            with self.subTest(file=file):
                self.initialize_app(file)
                operation = {
                    "parameters": [{"name": "param1", "in": "query"}],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {"example": {"message": "test"}}
                            }
                        }
                    },
                }
                example = {"message": "test"}
                handler = self.mocky_app.create_handler(operation, example, "get")
                with self.app.test_request_context("/test?param1=value1"):
                    response = handler()
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(
                        response.json,
                        {"message": "test", "query_params": {"param1": "value1"}},
                    )

    def test_create_handler_post(self):
        for file in ["openapi.yaml"]:
            with self.subTest(file=file):
                self.initialize_app(file)
                operation = {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {"example": {"message": "test"}}
                            }
                        }
                    }
                }
                example = {"message": "test"}
                handler = self.mocky_app.create_handler(operation, example, "post")
                with self.app.test_request_context(
                    "/test", method="POST", json={"key": "value"}
                ):
                    response = handler()
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json, {"message": "test", "key": "value"})

    def test_create_handler_unsupported_method(self):
        for file in ["openapi.yaml"]:
            with self.subTest(file=file):
                self.initialize_app(file)
                operation = {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {"example": {"message": "test"}}
                            }
                        }
                    }
                }
                example = {"message": "test"}
                handler = self.mocky_app.create_handler(operation, example, "patch")
                with self.app.test_request_context("/item", method="PATCH"):
                    response = handler()
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(response.json, {"error": "Method not supported"})


if __name__ == "__main__":
    unittest.main()
