from tests.validation._external.gmat.hpop_driver import _gmat_epoch


def test_gmat_epoch_accepts_fractional_and_second_precision_iso_timestamps() -> None:
    assert _gmat_epoch("2024-01-01T00:00:00.123Z") == "01 Jan 2024 00:00:00.123"
    assert _gmat_epoch("2024-01-01T00:00:00Z") == "01 Jan 2024 00:00:00.000"
