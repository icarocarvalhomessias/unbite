from unbite.geometry import FINGERTIPS, MOUTH_CORNERS, MOUTH_LIPS, Box, nearest_reach


def make_face(center=(100.0, 100.0), width=40.0):
    """A fake 478-point face mesh with only the mouth points placed."""
    cx, cy = center
    face = [(0.0, 0.0)] * 478
    face[MOUTH_CORNERS[0]] = (cx - width / 2, cy)
    face[MOUTH_CORNERS[1]] = (cx + width / 2, cy)
    face[MOUTH_LIPS[0]] = (cx, cy - 5)
    face[MOUTH_LIPS[1]] = (cx, cy + 5)
    return face


def make_hand(tip_at, others_at=(500.0, 500.0)):
    """A fake 21-point hand whose index fingertip sits at `tip_at`."""
    hand = [others_at] * 21
    hand[FINGERTIPS[1]] = tip_at
    return hand


def test_distance_is_measured_in_mouth_widths():
    reach = nearest_reach(make_face(width=40), [make_hand(tip_at=(140.0, 100.0))])
    assert reach is not None
    assert reach.distance == 1.0  # 40 px away, mouth 40 px wide


def test_distance_does_not_depend_on_how_far_you_sit():
    near = nearest_reach(make_face(width=80), [make_hand(tip_at=(180.0, 100.0))])
    far = nearest_reach(make_face(width=20), [make_hand(tip_at=(120.0, 100.0))])
    assert near.distance == far.distance == 1.0


def test_picks_the_closest_fingertip_of_all_hands():
    far_hand = make_hand(tip_at=(300.0, 100.0))
    close_hand = make_hand(tip_at=(104.0, 100.0))
    reach = nearest_reach(make_face(), [far_hand, close_hand])
    assert reach.fingertip == (104.0, 100.0)


def test_no_hands_means_no_reach():
    assert nearest_reach(make_face(), []) is None


def test_box_overlap_and_expansion():
    hand = Box(0, 0, 10, 10)
    phone = Box(11, 0, 21, 10)
    assert not phone.overlaps(hand)
    assert phone.expanded(0.2).overlaps(hand)
