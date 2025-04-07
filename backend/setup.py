from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f.readlines() if not line.startswith("#")]

# Read long description from README if it exists
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r") as f:
        long_description = f.read()

setup(
    name="book_translator",
    version="0.1.0",
    description="Book Translation API for translating books and PDFs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rafael Ribeiro",
    author_email="your-email@example.com",
    url="https://github.com/your-username/tradutor_livro",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "book-translator=app.main:start_server",
        ],
    },
) 