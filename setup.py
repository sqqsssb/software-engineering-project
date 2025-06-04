 from setuptools import setup, find_packages

setup(
    name="chatdev",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-socketio',
        'requests',
        'openai',
        'mysql-connector-python'
    ],
)