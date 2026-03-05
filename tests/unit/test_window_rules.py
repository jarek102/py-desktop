from services.window_rules import MatchCriterion, WindowRule, match_window


def _rule(app_id=None, title=None, workspace="test") -> WindowRule:
    return WindowRule(
        matches=[MatchCriterion(app_id=app_id, title=title)],
        workspace=workspace,
    )


def test_matches_by_app_id():
    rules = [_rule(app_id="^firefox$")]
    assert match_window(rules, "firefox", "") is rules[0]


def test_no_match_returns_none():
    rules = [_rule(app_id="^firefox$")]
    assert match_window(rules, "chromium", "") is None


def test_app_id_and_title_both_required_within_one_criterion():
    rules = [_rule(app_id="^firefox$", title="^games")]
    assert match_window(rules, "firefox", "games browser") is rules[0]
    assert match_window(rules, "firefox", "other page") is None


def test_multiple_criteria_are_or():
    rules = [
        WindowRule(
            matches=[
                MatchCriterion(app_id=None, title="^teams"),
                MatchCriterion(app_id=None, title="^citrix"),
            ],
            workspace="work-L",
        )
    ]
    assert match_window(rules, "teams", "teams — work") is rules[0]
    assert match_window(rules, "citrix", "citrix workspace") is rules[0]
    assert match_window(rules, "chrome", "something else") is None


def test_none_criterion_matches_anything():
    rules = [_rule(app_id=None, title=None)]
    assert match_window(rules, "anything", "anything") is rules[0]


def test_first_matching_rule_wins():
    rule_a = _rule(app_id="^firefox$", workspace="first")
    rule_b = _rule(app_id="^firefox$", workspace="second")
    assert match_window([rule_a, rule_b], "firefox", "") is rule_a
