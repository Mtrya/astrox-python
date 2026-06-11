from tests.validation._external.gmat.hpop_driver import _force_model_lines, _gmat_epoch


def test_gmat_epoch_accepts_fractional_and_second_precision_iso_timestamps() -> None:
    assert _gmat_epoch("2024-01-01T00:00:00.123Z") == "01 Jan 2024 00:00:00.123"
    assert _gmat_epoch("2024-01-01T00:00:00Z") == "01 Jan 2024 00:00:00.000"


def test_force_model_lines_maps_constant_jacchia_roberts_drag_to_gmat_script_fields() -> None:
    lines = _force_model_lines(
        {
            "gravity": {
                "type": "earth_gravity_field",
                "degree": 0,
                "order": 0,
                "potential_file": "JGM2.cof",
                "tide_model": "None",
            },
            "atmosphere": {
                "model": "jacchia_roberts",
                "data_source": "constant_values",
                "f10p7": 150.0,
                "f10p7_avg": 150.0,
                "kp": 3.0,
            },
            "srp": None,
            "third_bodies": [],
        }
    )

    assert "HpopForceModel.Drag = JacchiaRoberts;" in lines
    assert "HpopForceModel.Drag.AtmosphereModel = 'JacchiaRoberts';" in lines
    assert "HpopForceModel.Drag.HistoricWeatherSource = 'ConstantFluxAndGeoMag';" in lines
    assert "HpopForceModel.Drag.F107 = 150;" in lines
    assert "HpopForceModel.Drag.F107A = 150;" in lines
    assert "HpopForceModel.Drag.MagneticIndex = 3;" in lines
