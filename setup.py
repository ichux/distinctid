import setuptools

import distinctid

setuptools.setup(
    name="distinctid",
    version=distinctid.version,
    description="Generate distinct/unique IDs",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="unique distinct id uuid sort",
    url=distinctid.URL,
    download_url="https://github.com/ichux/distinctid/archive/refs/tags/v1.0.1.tar.gz",
    author=distinctid.__author__,
    author_email="theichux@gmail.com",
    license="MIT",
    python_requires=">=3",
    packages=["distinctid"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
