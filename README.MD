<h1 align="center">
  <a href="https://github.com/orangebeard-io/python-client">
    <img src="https://raw.githubusercontent.com/orangebeard-io/python-client/master/.github/logo.svg" alt="Orangebeard.io Python Client" height="200">
  </a>
  <br>Orangebeard.io Python Client<br>
</h1>

<h4 align="center">Orangebeard Python client for Python based Orangebeard Listeners.</h4>



<div align="center">
  <h4>
    <a href="https://orangebeard.io">Orangebeard</a> |
    <a href="#installation">Installation</a>
  </h4>
</div>

## Installation

### Install the pip package

Note: this client should be used as a dependency in listener projects

`pip install orangebeard-client`

## CLI
The python client comes with a simple command line utility `orangebeard-cli`. This utility can be used
to start and finish test runs outside a listener's lifecycle. Mainly useful to report parrallel executions
to the same Orangebeard test run. 

Usage:
```commandline
usage: Orangebeard CommandLine Utility [-h] [-e ENDPOINT] [-t ACCESSTOKEN] [-p PROJECT] -x {start,finish} [-s TESTSET] [-d DESCRIPTION] [-id TESTRUNUUID]

CLI to start or finish a test run

options:
  -h, --help            show this help message and exit
  -e ENDPOINT, --endpoint ENDPOINT
                        Your Orangebeard endpoint
  -t ACCESSTOKEN, --accessToken ACCESSTOKEN
                        Your Orangebeard Access Token
  -p PROJECT, --project PROJECT
                        Orangebeard Project Name
  -x {start,finish}, --cmd {start,finish}
                        Command to execute
  -s TESTSET, --testset TESTSET
                        The testset name, required for start command
  -d DESCRIPTION, --description DESCRIPTION
                        The test run description (optional)
  -id TESTRUNUUID, --testRunUuid TESTRUNUUID
                        The UUID of the test run to finish, required for finish
```

Example (Robotframework using pabot):
```shell
#!/bin/bash
testrunUuid=$(orangebeard-cli -x start)
pabot --listener orangebeard_robotframework.listener  --variable orangebeard_testrun:"$testrunUuid" --console verbose .
orangebeard-cli -x finish -id $testrunUuid
```
