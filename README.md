[![Build Status](https://travis-ci.org/acerv/marvin.svg?branch=master)](https://travis-ci.org/acerv/marvin)

# Introduction
Marvin is a framework made for remote testing. At the moment, the following
protocols are supported:
* ssh
* sftp

In the future, it will support other protocols such as:
* serial
* ftp
* git
* http/https

A test is created using the Yaml syntax, for example:

    description: Execute a script remotely and it fetch the script report
    name       : test
    version    : '1.0'
    author     : Andrea Cervesato

    protocols:
        sftp:
            address : &ssh_addr localhost
            port    : &ssh_port 22
            user    : &ssh_user sshtest
            password: &ssh_pass test
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
            - source: setup.sh
              dest  : /home/sshtest/setup.sh
              type  : file

    execute:
        protocol: ssh

        commands:
            - script  : chmod +x /home/sshtest/setup.sh
            - script  : /home/sshtest/setup.sh

    collect:
        protocol: sftp

        transfer:
            - source: /home/sshtest/results.log
              dest  : results.log

Each part of the test file has some sections, which defines the following
informations:
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
* serial protocol support
* ftp protocol support
* git protocol support
* http/https protocol support

# Under evaluation
* explicit cleanup definition in the deploy stage
