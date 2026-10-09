import tools


def test_lookup_known_and_unknown():
    assert tools.lookup_order("PCL-10482")["total_cents"] == 8900
    assert "error" in tools.lookup_order("PCL-0")
