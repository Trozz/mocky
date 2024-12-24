# Mocky

Mocky is a simple OpenAPI Mock Server to simulate API responses based on OpenAPI specifications. It is built using Flask and supports OpenTelemetry for metrics collection.

## Features

- Load OpenAPI 3.0 specifications in JSON or YAML format.
- Automatically generate routes based on the OpenAPI specification.
- Support for dynamic and fixed routes.
- OpenTelemetry integration for metrics collection.

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/trozz/mocky.git
    cd mocky
    ```

2. Install the package:

    ```sh
    pip install .
    ```

## Usage

1. Run the Mocky server:

    ```sh
    mocky --file openapi.yaml --port 8080 --host 127.0.0.1
    ```

    You can specify the path to the OpenAPI specification file using the `--file` argument. The server will listen on the specified host and port. The `--debug` flag is optional and enables debug mode, which provides more detailed logging for troubleshooting.

2. Access the server:

    - Root endpoint: `http://127.0.0.1:8080/`
    - Info endpoint: `http://127.0.0.1:8080/mocky/info`
    - Health endpoint: `http://127.0.0.1:8080/mocky/health`
    - Routes endpoint: `http://127.0.0.1:8080/mocky/routes`

## OpenTelemetry Integration

To enable OpenTelemetry metrics collection, use the `--otel` flag when running the server:

```sh
mocky --file openapi.yaml --port 8080 --host 127.0.0.1 --debug --otel
```

## Testing

To run the tests, use pytest:

    ```sh
    pytest
    ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

### Acknowledgements

- Flask
- OpenTelemetry
- Swagger
