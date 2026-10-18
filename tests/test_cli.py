from jsa import cli


def test_list_on_empty_db(capsys):
    cli.main(["list"])
    assert capsys.readouterr().out.strip() == "No applications yet."
