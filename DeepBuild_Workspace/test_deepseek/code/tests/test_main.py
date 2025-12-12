import pytest
from click.testing import CliRunner
from main import cli


def test_add():
    runner = CliRunner()
    result = runner.invoke(cli, ['add', '--task=Test Task'])
    assert 'Added task \'Test Task\'' in result.output

# Add more tests for view and other commands