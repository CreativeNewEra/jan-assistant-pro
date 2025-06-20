"""
Setup configuration for Jan Assistant Pro
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="jan-assistant-pro",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A powerful, local-first AI assistant with tools that work with Jan.ai",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/jan-assistant-pro",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "bandit>=1.7.0",
            "black>=23.0.0",
            "build>=0.10.0",
            "flake8>=6.0.0",
            "ipdb>=0.13.0",
            "isort>=5.12.0",
            "memory-profiler>=0.60.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "py-spy>=0.3.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-watch>=4.2.0",
            "pytest>=7.0.0",
            "rich>=13.0.0",  # For better console output
            "safety>=2.3.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx>=6.0.0",
            "twine>=4.0.0",
        ],
        "system": [
            "psutil>=5.8.0",  # For system monitoring
        ],
    },
    entry_points={
        "console_scripts": [
            "jan-assistant-pro=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md", "*.txt"],
    },
)
