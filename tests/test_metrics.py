"""Edge cases in the routing-share math the smoke test doesn't pin down:
the primary tag outranks raw position, and among several tagged primaries the
lowest position breaks the tie.
"""

from types import SimpleNamespace

from metrics import routing_share


def _product(name, role, position, sentiment="neutral"):
    return SimpleNamespace(name=name, role=role, position=position, sentiment=sentiment)


def test_primary_tag_beats_lower_position():
    # Terraform sits at position 1 but Pulumi is the tagged primary -> Pulumi wins.
    exts = [SimpleNamespace(products=[
        _product("Terraform", "alternative", 1),
        _product("Pulumi", "primary", 2),
    ])]
    result = routing_share(exts)
    assert result["Pulumi"]["routing_share"] == 1.0
    assert result["Terraform"]["routing_share"] == 0.0


def test_tie_broken_by_position_among_primaries():
    # Two products both tagged primary -> the lower position takes the credit.
    exts = [SimpleNamespace(products=[
        _product("Pulumi", "primary", 3),
        _product("Terraform", "primary", 1),
    ])]
    result = routing_share(exts)
    assert result["Terraform"]["routing_share"] == 1.0
    assert result["Pulumi"]["routing_share"] == 0.0


def test_empty_products_sample_counts_toward_n():
    # A sample with no products still counts as a sample: it drags mention/routing
    # rates down rather than being ignored.
    exts = [
        SimpleNamespace(products=[_product("Vault", "primary", 1)]),
        SimpleNamespace(products=[]),
    ]
    result = routing_share(exts)
    assert result["HashiCorp Vault"]["routing_share"] == 0.5
    assert result["HashiCorp Vault"]["mention_rate"] == 0.5
