from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from .command_line import CliRunner

if __name__ == "__main__":
    cli = CliRunner()
    cli.run()
