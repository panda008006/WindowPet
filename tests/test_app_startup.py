from window_pet_app.app import startup_configs


def test_startup_restores_only_last_saved_window():
    configs = [
        {"path": "assets/UsagiPet"},
        {"path": "assets/JiyiPet"},
        {"path": "assets/LogoGuineaPigPet"},
    ]

    assert startup_configs(configs) == [{"path": "assets/LogoGuineaPigPet"}]


def test_startup_ignores_invalid_tail_items():
    configs = [
        {"path": "assets/UsagiPet"},
        42,
        None,
    ]

    assert startup_configs(configs) == [{"path": "assets/UsagiPet"}]
