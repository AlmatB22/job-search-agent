import sys

import pytest

from jsa import cli


def test_list_command_parses(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jsa", "list"])
    with pytest.raises(SystemExit, match="not implemented"):
        cli.main()
