from scoreboard import main


def test_main_prints_greeting(capsys):
    main()
    assert "retrieval-scoreboard" in capsys.readouterr().out
