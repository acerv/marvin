**Consider marvin 1.x as a prototype. I'm working on a version which is going to be modular and fully extensible.**

[![Build Status](https://travis-ci.org/acerv/marvin.svg?branch=master)](https://travis-ci.org/acerv/marvin)

# Table of contents
- [Introduction](#introduction)
- [A Marvin test example](#a-marvin-test-example)
- [Test file](#test-file)
- [Define protocols](#define-protocols)
    - [SSH protocol](#ssh-protocol)
    - [SFTP protocol](#sftp-protocol)
    - [Serial protocol](#serial-protocol)
- [Define stages](#define-stages)
    - [Deploy stage](#deploy-stage)
    - [Execute stage](#execute-stage)
    - [Collect stage](#collect-stage)
- [Python version](#python-version)
- [Install/uninstall framework](#installuninstall-framework)
- [Running tests](#running-tests)
- [Framework unittests](#framework-unittests)
- [TODO](#todo)
- [Rejected](#rejected)
- [Under evaluation](#under-evaluation)

# Introduction
The Marvin framework has been created with the idea of testing GNU/Linux
embedded systems in the IoT and automotive context, giving a programming
language agnostic system where it's possibile to build and merge different
tests suites.

# A Marvin test example

    description: Test my remote server
    name       : server_test
    version    : '1.0 beta2'
    author     : Andrea Cervesato

    protocols:
        # the following parameters must be defined in order to use protocols

        sftp:
            address : &ssh_addr "10.0.2.18"
            port    : &ssh_port 22
            user    : &ssh_user "www"
            password: &ssh_pass "www1234"
            timeout : &ssh_tout 5.0

        ssh:
            address : *ssh_addr
            port    : *ssh_port
            user    : *ssh_user
            password: *ssh_pass
            timeout : *ssh_tout

        serial:
            port     : /dev/ttyUSB0
            baudrate : 9600
            parity   : 'odd'
            stop_bits: 2
            data_bits: 7
            timeout  : 1.0

    deploy:
        protocol: sftp

        # if true, transferred data will be deleted after collect stage
        delete: true

        transfer:
            # marvin will download the following script on target's
            # /var/marvin/data/setup.sh path

            - source: http://mywebsite.com/setup.sh
              dest  : /var/marvin/data/setup.sh
              type  : http

            - source: http://mywebsite.com/tests.git
              dest  : /var/marvin/data/tests.git
              type  : git

    execute:
        protocol: ssh

        commands:
            # marvin will execute the downloaded scripts, checking if they
            # succeeded or failed

            - script : "sh -c /var/marvin/data/setup.sh"
              passing: "0"
              failing: "1"

            - script : "sh -c /var/marvin/data/tests.git/unit_tests.sh"
              passing: "0"
              failing: "1"
              
            - script : "sh -c /var/marvin/data/tests.git/functional_tests.sh"
              passing: "0"
              failing: "1"

            - script : "sh -c /var/marvin/data/tests.git/stress_tests.sh"
              passing: "0"
              failing: "1"

            - script : "sh -c /var/marvin/data/tests.git/hardware_tests.sh"
              passing: "0"
              failing: "1"

            - script  : "AT"
              passing : "OK"
              failing : ""
              protocol: serial
              
            - script : "ping -c 1 www.google.it"
              passing: "0"
              failing: "1"

    collect:
        protocol: sftp

        transfer:
            # marvin will fetch the setup results in the hosting machine

            - source: /var/marvin/data/setup_results.log
              dest  : results.log

# Test file
A test file is created using the 
[Yaml syntax](https://learnxinyminutes.com/docs/yaml/)
and it defines the following stages:
* `header`: description, name, version, author of the test file
* `protocols`: the protocols informations
* `deploy`: the deploy stage. It transfer data from local host to the target
* `execute`: the execute stage. It defines what commands must be executed on
    target
* `collect`: the collect stage. It defines what data must be fetched from the
    target, when the `deploy` and `execute` stage are completed

What happens when the Marvin framework reads a file is:
* file syntax is validated
* test definition is imported
* deploy stage is launched (if defined)
* execute stage is launched (if defined)
* collect stage is launched (if defined)
* target is cleaned by files which have been transferred (if deploy defines it)

Yes, eventually, you can write a file without stages (who wants to do that? 
:-)). During the stages, a report directory is created and populated with
informations about the running test.

At the moment, the following protocols are supported:
* ssh
* sftp
* serial
* git
* http/https

In the future, it will support other protocols such as:
* ftp
# Define protocols
The `protocols` section is __not optional__ and it defines the protocols
configurations.

## SSH protocol
The SSH protocol is set in the `protocols` section and it's defined as
following (all parameters are required):

    ssh:
        address : localhost
        port    : 22
        user    : ""
        password: ""
        timeout : 5.0

## SFTP protocol
The SFTP protocol is set in the `protocols` section and it's defined as
following (all parameters are required):

    # as you can see, it's identical to ssh
    sftp:
        address : localhost
        port    : 22
        user    : ""
        password: ""
        timeout : 5.0

## Serial protocol
The serial protocol is set in the `protocols` section and it's defined as
following (all parameters are required):

    serial:
        port     : /dev/ttyUSB0
        baudrate : 9600
        parity   : 'odd'
        stop_bits: 2
        data_bits: 7
        timeout  : 1.0

Where parameters are:
* `port`: the serial port (ie `/dev/ttyUSB0`). `loop` is a special port 
    echoing a string back to the sender
* `baudrate`: 50 up to 4000000
* `parity`: 'none', 'even', 'odd'
* `stop_bits`: 1, 1.5, 2
* `data_bits`: 5, 6, 7, 8
* `timeout`: 0.0 up to 120.0

# Define stages
The test stages are:
* `deploy`: (optional) deploy system, transferring data on target
* `execute`: (optional) execute scripts and commands on target
* `collect`: (optional) collect data from target after `execute`

## Deploy stage
The deploy stage can be defined as following:

    deploy:
        protocol: sftp
        delete  : true

Where parameters are:
* `protocol`: the transfer protocol. Supported protocol is `sftp`
* `delete`: (optional) if true, the transferred files are deleted after collect
    stage

Each file/directory path must be defined in the `transfer` section as following:

    transfer:
        - source: ./testfile0.txt
          dest  : testfile0.txt
          type  : file

Where parameters are:
* `source`: the path to transfer
* `dest`: the location of the path to transfer on target
* `type`: (optional) the source type. Possible values are: `file`, `git`, `http`

## Execute stage
The execute stage can be defined as following:

    execute:
        protocol: ssh

Where parameters are:
* `protocol`: the default execute protocol to use, if no protocol is defined for
    the single commands. Supported protocols are `serial` and `ssh`

Each command to execute must be defined in the `commands` section as following:

    commands:
        - script: "test -d /; ls /"
          passing: "0"
          failing: "1"
          protocol: ssh

Where parameters are:
* `script`: the command to execute on target
* `passing`: (optional) what the command returns if passing (always formatted as
    string)
* `failing`: (optional) what the command returns if failing (always formatted as
    string)
* `protocol`: (optional) the protocol to use for the single command. Supported
    protocols are `serial` and `ssh`

When a command doesn't return the `passing` or `failing` string, the framework
will mark the command result as `unknown`.

## Collect stage
The collect stage can be defined as following:

    collect:
        protocol: sftp

Where parameters are:
* `protocol`: the transfer protocol. Supported protocol is `sftp`

Each file/directory path must be defined in the `transfer` section as following:

    transfer:
        - source: results/
          dest  : results_cmd/

Where paramters are:
* `source`: the path to transfer
* `dest`: the location of the path to transfer on host

# Python version
The python version used by the framework is the 3.5.3. If your system does not
provide it, you can use the `pyenv` package:

    sudo apt-get install libssl-dev
    pip install --no-cache-dir pyenv

Follow the pyenv instructions to setup your environment, then run:

    pyenv install 3.5.3

# Install/uninstall framework
Once the correct python version is installed, to install marvin run:

    make install

..to uninstall:

    make uninstall

# Running tests
Create your reports directory:

    mkdir reports

Use the `marvin` command to execute tests:

    marvin -r reports <your tests list>

# Framework unittests
The framework uses `py.test` to run unittests, which are located in 
`marvin/tests`:

    pip install pytest

To run unittests, simply run:

    pytest marvin/tests

# TODO
- [x] serial protocol
- [x] git protocol support
- [x] http/https protocol support
- [x] JUnit reports
- [ ] a better stdout, stderr handling with paramiko
- [ ] send data to remote targets during collect stage
- [ ] ftp protocol support

# Rejected
- [ ] replace paramiko library with parallel-ssh

# Under evaluation
- [ ] explicit cleanup definition in the deploy stage
