from setuptools import setup, find_packages

setup(
    name='ticket_processor',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'apache-beam[gcp]',
        'google-genai',
        'google-cloud-bigquery',
        'google-cloud-aiplatform'
    ]
)
