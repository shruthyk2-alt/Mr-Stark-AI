"""Setup configuration for MR. STARK application."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mr-stark",
    version="1.0.0",
    author="Shruthy",
    description="MR. STARK - Personal AI Assistant with Voice Interaction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mr-stark",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: User Interfaces",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mr-stark=mr_stark:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["**/*"],
    },
    zip_safe=False,
    keywords="ai assistant voice interaction desktop pyside6",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/mr-stark/issues",
        "Source": "https://github.com/yourusername/mr-stark",
    },
)
