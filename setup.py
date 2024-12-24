from setuptools import setup, find_packages

setup(
    name="mocky",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask==3.1.0",
        "opentelemetry-api==1.29.0",
        "opentelemetry-instrumentation",
        "opentelemetry-instrumentation-flask",
        "opentelemetry-sdk==1.29.0",
        "PyYAML==6.0.2",
    ],
    entry_points={
        "console_scripts": [
            "mocky=mocky.main:main",
        ],
    },
    author="Michael Leer",
    author_email="your-email@example.com",
    description="Mocky is a simple OpenAPI Mock Server to simulate API responses based on OpenAPI specifications.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/trozz/mocky",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
