from flask import Flask, jsonify, request, make_response
import yaml
import json
from typing import Any, Dict
import argparse
import random
import string
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)


class MockyApp:
    """MockyApp is a simple OpenAPI Mock Server to simulate API responses based on OpenAPI specifications.


    Methods:
        __init__():
            Initialize the MockyApp class, set up argument parsing, initialize Flask app,
            instrument with OpenTelemetry, and register routes.
        load_and_register_routes():
        generate_default_response(status: int, media_type: str = "application/json") -> Any:
        convert_path(openapi_path: str) -> str:
            Convert an OpenAPI path template to a format suitable for URL routing.
        create_handler(operation: Dict[str, Any], example: Any, method: str):
        register_routes(openapi_spec: Dict[str, Any]):
        root():
            Handle the root endpoint of the application.
        info():
            Return application information as a JSON response.
        health():
        routes():
            Generate a list of routes defined in the application.
        run():
            Run the application server."""

    def __init__(self):
        """
        Initialize the MockyApp class.
        This method sets up argument parsing for the command-line interface, initializes the Flask application,
        instruments the Flask app with OpenTelemetry for metrics, and registers both dynamic and fixed routes.
        Args:
            None
        Attributes:
            args (Namespace): Parsed command-line arguments.
            app (Flask): The Flask application instance.
            meter (Meter): The OpenTelemetry meter for metrics collection.
            dynamic_routes_counter (Counter): A counter for tracking dynamic routes.
        Raises:
            RuntimeError: If the OpenTelemetry meter initialization fails.
        """
        # Argument parsing
        parser = argparse.ArgumentParser(
            description="Mocky - A simple OpenAPI Mock Server to simulate API responses based on OpenAPI specifications"
        )
        parser.add_argument(
            "--file",
            type=str,
            help="Path to the OpenAPI specification file (YAML or JSON format)",
            default="openapi.yaml",
        )
        parser.add_argument(
            "--port",
            type=int,
            help="Port number on which the server will listen",
            default=8080,
        )
        parser.add_argument(
            "--host",
            type=str,
            help="Hostname or IP address to bind the server to",
            default="127.0.0.1",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode for more detailed logging and error messages",
        )
        parser.add_argument(
            "--otel",
            action="store_true",
            help="Enable OpenTelemetry metrics",
            default=False,
        )
        self.args = parser.parse_args()

        # Initialize Flask app
        self.app = Flask(__name__)

        # Instrument Flask app with OpenTelemetry
        if self.args.otel:
            FlaskInstrumentor().instrument_app(self.app)
            metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
            provider = MeterProvider(metric_readers=[metric_reader])
            metrics.set_meter_provider(provider)
            self.meter = metrics.get_meter("mocky")
            if self.meter:
                self.dynamic_routes_counter = self.meter.create_counter(
                    "dynamic_routes.counter",
                    description="Counter for dynamic routes",
                    unit="1",
                )
            else:
                self.app.logger.error("Failed to initialize meter")
                raise RuntimeError("Failed to initialize meter")
        else:
            self.meter = None

        # Load, parse OpenAPI, and register routes
        self.load_and_register_routes()

        # Register fixed routes
        self.app.add_url_rule("/", view_func=self.root)
        self.app.add_url_rule("/mocky/info", view_func=self.info)
        self.app.add_url_rule("/mocky/health", view_func=self.health)
        self.app.add_url_rule("/mocky/routes", view_func=self.routes)

    def load_and_register_routes(self):
        """
        Load OpenAPI file and register routes based on the specification.
        This method attempts to load an OpenAPI file specified by the user, parse it,
        and register the routes defined in the specification. It supports both YAML
        and JSON file formats.
        Raises:
            ValueError: If the file format is unsupported or if parsing the OpenAPI file fails.
            Exception: If there is an error while loading the OpenAPI file or registering routes.
        """
        try:
            openapi_spec = self._parse_openapi(self.args.file)
            self.register_routes(openapi_spec)
        except Exception as e:
            self.app.logger.error(f"Failed to load OpenAPI file: {e}")
            raise e

        try:
            with open(self.args.file, "r") as file:
                if self.args.file.endswith(".yaml") or self.args.file.endswith(".yml"):
                    return yaml.safe_load(file)
                elif self.args.file.endswith(".json"):
                    return json.load(file)
                else:
                    raise ValueError("Unsupported file format. Use JSON or YAML.")
        except Exception as e:
            raise ValueError(f"Failed to parse OpenAPI file: {e}")

    def _parse_openapi(self, file_path: str) -> Dict[str, Any]:
        """
        Parse the OpenAPI file and return the specification as a dictionary.

        Args:
            file_path (str): The path to the OpenAPI file.

        Returns:
            Dict[str, Any]: The parsed OpenAPI specification.

        Raises:
            ValueError: If the file format is unsupported or if parsing the OpenAPI file fails.
        """
        try:
            with open(file_path, "r") as file:
                if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                    return yaml.safe_load(file)
                elif file_path.endswith(".json"):
                    return json.load(file)
                else:
                    raise ValueError("Unsupported file format. Use JSON or YAML.")
        except Exception as e:
            raise ValueError(f"Failed to parse OpenAPI file: {e}")

    def generate_default_response(
        self, status: int, media_type: str = "application/json"
    ) -> Any:
        """
        Generate a default response based on the status code and media type.

        Args:
            status (int): The HTTP status code for the response.
            media_type (str): The media type of the response. Defaults to "application/json".

        Returns:
            Any: The default response content.
        """
        if media_type == "application/json":
            return {"status": status, "message": "Default response"}
        return f"Default response with status {status}"

    def convert_path(self, openapi_path: str) -> str:
        """
        Converts an OpenAPI path template to a format suitable for URL routing.

        This method replaces curly braces `{}` used in OpenAPI path templates with
        angle brackets `<>` which are commonly used in URL routing frameworks.

        Args:
            openapi_path (str): The OpenAPI path template to convert.

        Returns:
            str: The converted path with angle brackets.
        """
        return openapi_path.replace("{", "<").replace("}", ">")

    def create_handler(self, operation: Dict[str, Any], example: Any, method: str):
        """
        Create a request handler for the given operation.

        Args:
            operation (Dict[str, Any]): The operation details, including parameters.
            example (Any): An example response to be used as a base for the response.
            method (str): The HTTP method for the request (e.g., 'GET', 'POST', 'PUT', 'DELETE').

        Returns:
            function: A request handler function that processes the request based on the given operation and method.
        """

        def handler():
            """Request handler function"""
            query_params = {}
            for param in operation.get("parameters", []):
                if param.get("in") == "query":
                    param_name = param["name"]
                    query_params[param_name] = request.args.get(param_name)

            if method.upper() == "POST":
                try:
                    if request.content_type == "application/json":
                        data = request.json
                        if isinstance(data, dict) and isinstance(example, dict):
                            return jsonify({**example, **data})
                    else:
                        return jsonify({"error": "Unsupported Media Type"}), 415
                except Exception:
                    return jsonify({"error": "Invalid request body"}), 400
            elif method.upper() == "GET":
                if query_params:
                    return jsonify({**example, "query_params": query_params})
                return jsonify(example)
            elif method.upper() == "PUT":
                try:
                    data = request.json
                    if isinstance(data, dict) and isinstance(example, dict):
                        return jsonify({**example, **data})
                except Exception:
                    return jsonify({"error": "Invalid request body"}), 400
            elif method.upper() == "DELETE":
                return jsonify({"message": "Resource deleted"}), 204
            else:
                return make_response(jsonify({"error": "Method not supported"}), 405)

            return jsonify(example)

        return handler

    def register_routes(self, openapi_spec: Dict[str, Any]):
        """
        Register routes based on the OpenAPI specification.

        Args:
            openapi_spec (Dict[str, Any]): The OpenAPI specification containing paths and methods.

        This method iterates over the paths defined in the OpenAPI specification and registers
        corresponding routes in the Flask application. For each path and method, it generates
        a handler function and adds a URL rule to the Flask app. If a response example is provided
        in the OpenAPI spec, it uses that example; otherwise, it generates a default response.

        The method also logs the registration process and increments a dynamic routes counter if
        metering is enabled.
        """
        paths = openapi_spec.get("paths", {})
        for openapi_path, methods in paths.items():
            self.app.logger.debug(f"Registering path: {openapi_path}")
            flask_path = self.convert_path(openapi_path)
            for method, operation in methods.items():
                self.app.logger.debug(f"Registering method: {method}")
                responses = operation.get("responses", {})
                default_resp = self.generate_default_response(200)
                if "200" in responses and "content" in responses["200"]:
                    content = responses["200"]["content"]
                    example = content.get("application/json", {}).get(
                        "example", default_resp
                    )
                else:
                    example = default_resp

                handler = self.create_handler(operation, example, method)
                if self.meter:
                    self.dynamic_routes_counter.add(1)
                self.app.add_url_rule(
                    flask_path,
                    endpoint=f"{flask_path}_{method}",
                    view_func=handler,
                    methods=[method.upper()],
                )

    def root(self):
        """
        Handles the root endpoint of the application.

        Returns:
            Response: A JSON response with a message indicating the user might be in the wrong place.
        """
        return jsonify({"message": "Are you meant to be here?"})

    def info(self):
        """
        Provides information about the Mocky application.

        Returns:
            Response: A JSON response containing the application's name, version, description, author, company, and repository URL.
        """
        application_name = "Mocky"
        application_version = "0.0.1"
        application_description = "Mocky is a HTTP mock service, it can read OpenAPI 3.1 specification and return example data."
        application_author = "Michael Leer"
        application_company = "Gremlin LTD"
        application_repository = "https://github.com/trozz/mocky"

        application_info_as_dict = {
            "name": application_name,
            "version": application_version,
            "description": application_description,
            "author": application_author,
            "company": application_company,
            "repository": application_repository,
        }
        return jsonify(application_info_as_dict)

    def health(self):
        """
        Health check endpoint that returns the status of the service.

        Returns:
            Response: A JSON response with the status of the service.
        """
        return jsonify({"status": "ok"})

    def routes(self):
        """
        Generates a list of routes defined in the application.

        Iterates over the URL map rules of the application and constructs a list of
        dictionaries, each containing the path and allowed methods (excluding "HEAD")
        for each route.

        Returns:
            Response: A JSON response containing the list of routes.
        """
        route_list = []
        for rule in self.app.url_map.iter_rules():
            route_list.append(
                {
                    "path": rule.rule,
                    "methods": [m for m in rule.methods if m != "HEAD"],
                }
            )
        return jsonify(route_list)

    def run(self):
        """
        Runs the application server.

        This method starts the application server using the host, port, and debug
        settings specified in the command-line arguments.

        Args:
            None

        Returns:
            None
        """
        self.app.run(host=self.args.host, port=self.args.port, debug=self.args.debug)


def main():
    """
    Entry point for the Mocky application.

    This function initializes the MockyApp instance and starts the application.
    """
    mocky_app = MockyApp()
    mocky_app.run()


if __name__ == "__main__":
    main()
