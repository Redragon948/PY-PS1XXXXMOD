from setuptools import setup, find_packages
import os


# Read the long description from README.md
def read_long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        return f.read()


setup(
    name="PY-PS1XXXXMOD",
    version="0.1.0",
    description="Python library to interface with PS1-CO-1000-MOD and other PS1-*.*-MOD gas sensors.",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    author="Redragon948",
    author_email="redragon948@gmail.com",
    url="https://github.com/Redragon948/PY-PS1XXXXMOD",
    license="Apache 2.0",
    packages=find_packages(exclude=["tests", "docs"]),
    install_requires=[
        "pyserial>=3.6",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache 2.0 License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Hardware",
    ],
    keywords="sensor serial communication gas concentration temperature humidity",
    python_requires=">=3.6",
    project_urls={
        "Bug Reports": "https://github.com/Redragon948/PY-PS1XXXXMOD/issues",
        "Source": "https://github.com/Redragon948/PY-PS1XXXXMOD",
        "Documentation": "https://github.com/Redragon948/PY-PS1XXXXMOD#readme",
    },
    include_package_data=True,  # Include non-Python files specified in MANIFEST.in
    zip_safe=False,  # Recommended to be False for packages that include data files
)
