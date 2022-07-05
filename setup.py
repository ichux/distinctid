import uniqueid
import setuptools

setuptools.setup(
    name="uniqueid",
    version=uniqueid.version,
    description="Generate distinct/unique IDs",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="unique id uuid sort",
    url=uniqueid.URL,
    author=uniqueid.__author__,
    author_email="theichux@gmail.com",
    license="MIT",
    python_requires=">=3.10",
    packages=["uniqueid"],
)
