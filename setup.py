from setuptools import setup, find_packages

setup(
    name='medium_to_markdown_py',
    version='1.1.8',
    description='medium-to-medium_to_markdown_py-py is a Python package that converts Medium articles to Markdown format.',
    author='knowslog',
    author_email='scshin88@gmail.com',
    url='https://github.com/tourbut/medium-to-markdown_python',
    install_requires=['beautifulsoup4', 'requests'],
    packages=find_packages(exclude=[]),
    keywords=['medium', 'knowslog', 'markdown', 'medium to markdown'],
    python_requires='>=3.6',
    package_data={},
    zip_safe=False,
    classifiers=[],
)