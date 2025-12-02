# How to Install Locally Built Package with `uv`

When developing Python packages, you may find yourself needing to install a package that you've built locally. This can be particularly useful for testing changes before publishing to a package index like PyPI. In this micro-tutorial, we'll explore how to install a locally built package using `uv` (a hypothetical package for demonstration purposes) and address common pitfalls you might encounter along the way.

## Why This Happens

Installing a locally built package is essential for testing and development. It allows you to verify that your package works as expected before sharing it with others. However, the installation process can sometimes be confusing, especially if you are not familiar with the package structure or the tools available.

## Step-by-Step Solution

### Step 1: Build Your Package

Before you can install your package, you need to build it. Ensure your package has a proper structure, including a `setup.py` file. Here’s a simple example of a `setup.py`:

```python
from setuptools import setup, find_packages

setup(
    name='uv',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # List your package dependencies here
    ],
)
```

To build your package, navigate to the directory containing `setup.py` and run:

```bash
python setup.py sdist bdist_wheel
```

This command generates distribution archives in the `dist` directory.

### Step 2: Install the Package Locally

Once your package is built, you can install it using `pip`. Use the following command, replacing `path/to/dist/uv-0.1-py3-none-any.whl` with the actual path to your built wheel file:

```bash
pip install path/to/dist/uv-0.1-py3-none-any.whl
```

Alternatively, if you want to install it in "editable" mode (which allows you to make changes to the code without reinstalling), use:

```bash
pip install -e .
```

Make sure to run this command in the directory where your `setup.py` file is located.

### Step 3: Verify the Installation

To verify that your package has been installed correctly, you can run the following command:

```bash
pip show uv
```

This command will display information about the installed package, confirming that it is available for use.

## Example Variation

Suppose you have a package named `myapp` with the following structure:

```
myapp/
├── myapp/
│   ├── __init__.py
│   └── main.py
└── setup.py
```

Your `setup.py` might look like this:

```python
from setuptools import setup, find_packages

setup(
    name='myapp',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',  # Example dependency
    ],
)
```

To build and install `myapp`, follow the same steps as outlined above. After building, you would run:

```bash
pip install path/to/dist/myapp-0.1-py3-none-any.whl
```

## Common Errors & Fixes

### Error: "No module named 'uv'"

This error usually indicates that the package was not installed correctly. Ensure that:

- You are in the correct directory when running the installation command.
- The package name in `setup.py` matches what you are trying to import.

### Error: "Could not find a version that satisfies the requirement"

This error may occur if you are trying to install a package that does not exist in the specified path. Check that the path to the wheel file is correct and that the file was generated successfully.

### Error: "Permission denied"

If you encounter permission issues, try running the installation command with elevated privileges:

```bash
sudo pip install path/to/dist/uv-0.1-py3-none-any.whl
```

Alternatively, consider using a virtual environment to avoid permission issues.

## Cheat Sheet Summary

- **Build the package**: 
  ```bash
  python setup.py sdist bdist_wheel
  ```
- **Install the package**: 
  ```bash
  pip install path/to/dist/uv-0.1-py3-none-any.whl
  ```
- **Install in editable mode**: 
  ```bash
  pip install -e .
  ```
- **Verify installation**: 
  ```bash
  pip show uv
  ```

By following this guide, you should be able to successfully build and install your locally developed Python package using `uv`. Happy coding!