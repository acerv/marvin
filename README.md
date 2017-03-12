[![Build Status](https://travis-ci.org/acerv/marvin.svg?branch=master)](https://travis-ci.org/acerv/marvin)

# Introduction
Marvin is a framework made for remote testing. At the moment, the following
protocols are supported:
* ssh
* sftp
* serial

In the future, it will support other protocols such as:
* ftp
* git
* http/https

A test file is created using the 
[Yaml syntax](https://learnxinyminutes.com/docs/yaml/)
and it defines the following
stages:
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

# An example using SSH/SFTP protocol

    description: Transfer and execute a test script fetching its report file
    name       : test
    version    : '1.0'
    author     : Andrea Cervesato

    protocols:
        sftp:
            address : &ssh_addr localhost
            port    : &ssh_port 22
            user    : &ssh_user ""
            password: &ssh_pass ""
            timeout : &ssh_tout 5.0

        ssh:
            address : *ssh_addr
            port    : *ssh_port
            user    : *ssh_user
            password: *ssh_pass
            timeout : *ssh_tout

    deploy:
        protocol: sftp
        delete: true

        transfer:
            - source: ./test_files/
              dest  : /home/user/test
              type  : file

    execute:
        protocol: ssh

        commands:
            - script: "chmod +x /home/user/test/setup.sh; /home/user/test/setup.sh"
              passing: "0"
              failing: "1"

    collect:
        protocol: sftp

        transfer:
            - source: /home/user/test/results.log
              dest  : results.log

## Define the SSH protocol
The SSH protocol is set in the `protocols` section and it's defined as
following (all parameters are required):

    ssh:
        address : localhost
        port    : 22
        user    : ""
        password: ""
        timeout : 5.0

## Define the SFTP protocol
The SFTP protocol is set in the `protocols` section and it's defined as
following (all parameters are required):

    # as you can see, it's identical to ssh
    sftp:
        address : localhost
        port    : 22
        user    : ""
        password: ""
        timeout : 5.0

## Define the Serial protocol
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
* `port`: the serial port (ie `/dev/ttyUSB0`). `loop` is a special port that
    is echoing a string back to the sender
* `baudrate`: 50 up to 4000000
* `parity`: 'none', 'even', 'odd'
* `stop_bits`: 1, 1.5, 2
* `data_bits`: 5, 6, 7, 8
* `timeout`: 0.0 up to 120.0

## Define the deploy stage
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

Where paramters are:
* `source`: the path to transfer
* `dest`: the location of the path to transfer on target
* `type`: (optional) the source type (ie file, git, http etc.). Some of the
    protocols are not implemented yet

## Define the execute stage
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

## Define the collect stage
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

    pip install --no-cache-dir --egg pyenv

Follow the pyenv instructions to setup your environment, then run:

    pyenv install 3.5.3

# Install/uninstall the framework
Once the correct python version is installed, to install marvin run:

    make install

..to uninstall:

    make uninstall

# Running tests
Create your reports directory:

    mkdir reports

Use the `marvin` command to execute tests:

    marvin -r reports <your tests list>

# Launch framework unittests
The framework uses `py.test` to run unittests, which are located in 
`marvin/tests`:

    pip install pytest

To run unittests, simply run:

    pytest marvin/tests

# TODO
- [x] serial protocol
- [ ] ftp protocol support
- [ ] git protocol support
- [ ] http/https protocol support
- [ ] replace paramiko library with parallel-ssh

# Under evaluation
- [ ] explicit cleanup definition in the deploy stage
