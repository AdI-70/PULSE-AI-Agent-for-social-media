from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements-cli.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pulse-cli",
    version="1.0.0",
    author="Pulse Team",
    author_email="pulse@example.com",
    description="CLI tool for Pulse - Enterprise News-to-X Automated Pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AdI-70/AdI-70-PULSE-AI-Agent-for-social-media",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pulse=pulse_cli:cli",
        ],
    },
)