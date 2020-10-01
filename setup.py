import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="sql-based-etl",
    version="0.0.1",

    description="A CDK Python app for SQL-based ETL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    author="meloyang",

    package_dir={"": "source/.python"},
    packages=setuptools.find_packages(where="sql-based-etl"),

    install_requires=[
        "aws-cdk.core==1.62.0",
        "aws-cdk.aws_iam==1.62.0",
        "aws-cdk.aws_eks==1.62.0",
        "aws-cdk.aws_ec2==1.62.0",
        "aws-cdk.aws_s3==1.62.0",
        "aws-cdk.aws_ssm==1.62.0",
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)