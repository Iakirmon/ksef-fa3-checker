"""Pokrycie punktów wejścia CLI / web (bez realnego serwera)."""

from __future__ import annotations

from unittest.mock import patch

import pytest


def test_cli_main_konczy_sie_komunikatem() -> None:
    from fa3check.__main__ import main

    with pytest.raises(SystemExit, match="CLI walidacji"):
        main()


def test_web_main_uruchamia_uvicorn() -> None:
    from fa3check.web.__main__ import main

    with patch("fa3check.web.__main__.uvicorn.run") as run:
        main()
    run.assert_called_once()
    assert run.call_args.args[0] == "fa3check.web.app:app"
