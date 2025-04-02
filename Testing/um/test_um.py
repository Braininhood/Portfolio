from um import count


def test_single_um():
    assert count("um") == 1
    assert count("Um, thanks for the album.") == 1


def test_multiple_um():
    assert count("um, um... um!") == 3
    assert count("Um, thanks, um...") == 2


def test_no_um():
    assert count("yummy") == 0
    assert count("umbrella") == 0
    assert count("Uh, oh!") == 0


def test_edge_cases():
    assert count("um? Um.") == 2
    assert count("UM um uM Um") == 4
    assert count(" ") == 0
    assert count("") == 0
