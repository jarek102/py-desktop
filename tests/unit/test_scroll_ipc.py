import json

from services.scroll_ipc import parse_outputs, parse_workspaces


def test_parse_outputs_filters_invalid_entries():
    payload = json.dumps(
        [
            {"name": "eDP-1", "focused": True},
            {"focused": False},
            {"name": "HDMI-A-1"},
        ]
    )

    outputs = parse_outputs(payload)

    assert [output.name for output in outputs] == ["eDP-1", "HDMI-A-1"]
    assert outputs[0].focused is True
    assert outputs[1].focused is False


def test_parse_workspaces_reads_sway_like_json():
    payload = json.dumps(
        [
            {
                "num": 1,
                "name": "1:web",
                "focused": True,
                "visible": True,
                "output": "eDP-1",
            },
            {
                "num": 2,
                "name": "2:code",
                "focused": False,
                "visible": False,
                "output": "HDMI-A-1",
            },
        ]
    )

    workspaces = parse_workspaces(payload)

    assert len(workspaces) == 2
    assert workspaces[0].num == 1
    assert workspaces[0].name == "1:web"
    assert workspaces[0].output == "eDP-1"
    assert workspaces[0].focused is True
    assert workspaces[1].visible is False
