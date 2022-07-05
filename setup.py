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
    author=distinctid.__author__,
    author_email="theichux@gmail.com",
    license="MIT",
    python_requires=">=3.10",
    packages=["distinctid"],
)
