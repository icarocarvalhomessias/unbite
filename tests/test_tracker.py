from unbite.tracker import HabitTracker, Settings

TOUCH = 0.5
AWAY = 3.0


def tracker():
    return HabitTracker(Settings(threshold=0.9, hold=0.6, cooldown=4.0, object_grace=1.5))


def test_alerts_only_after_holding():
    t = tracker()
    assert not t.update(0.0, TOUCH)
    assert not t.update(0.5, TOUCH)
    assert t.update(0.6, TOUCH)


def test_moving_away_resets_the_hold():
    t = tracker()
    t.update(0.0, TOUCH)
    t.update(0.5, AWAY)
    assert not t.update(0.7, TOUCH)
    assert t.update(1.3, TOUCH)


def test_cooldown_between_alerts():
    t = tracker()
    t.update(0.0, TOUCH)
    assert t.update(0.6, TOUCH)
    assert not t.update(3.0, TOUCH)
    assert t.update(4.7, TOUCH)


def test_no_face_or_hand_never_alerts():
    t = tracker()
    assert not any(t.update(s / 10, None) for s in range(50))


def test_object_in_hand_suppresses_and_lingers():
    t = tracker()
    t.update(0.0, TOUCH, object_in_hand=True)
    # The detector misses the phone for a moment: still no alert within the grace time.
    assert not t.update(0.7, TOUCH, object_in_hand=False)
    assert not t.update(1.4, TOUCH, object_in_hand=False)
    # Grace over: the hold starts again from here.
    assert not t.update(1.6, TOUCH)
    assert t.update(2.2, TOUCH)
