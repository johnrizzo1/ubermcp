from setuptools import find_packages, setup

setup(
    name="uber-mcp-server",
    version="0.1.0",
    description="FastAPI-based MCP Server providing Kubernetes management tools",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/jrizzo/uber-mcp-server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
        "requests>=2.28.0",
        "httpx>=0.24.0",
        "kubernetes>=26.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-mock>=3.10.0",
            "pytest-watch>=4.2.0",
            "pylint>=2.17.0",
            "mypy>=1.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "ruff>=0.0.250",
            "types-requests>=2.28.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "uber-mcp-server=main:run_server",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
)
