import json
import datetime

import pytest

from monty.io import zopen

from emmet.core.qchem.task import TaskDocument
from emmet.core.molecules.vibration import VibrationDoc


@pytest.fixture(scope="session")
def test_tasks(test_dir):
    with zopen(test_dir / "liec_tasks.json.gz") as f:
        data = json.load(f)

    for d in data:
        d["last_updated"] = datetime.datetime.strptime(
            d["last_updated"]["string"], "%Y-%m-%d %H:%M:%S.%f"
        )

    tasks = [TaskDocument(**t) for t in data]
    return tasks


@pytest.fixture(scope="session")
def raman_task(test_dir):
    with zopen(test_dir / "raman_task.json.gz") as f:
        data = json.load(f)

    data["last_updated"] = datetime.datetime.strptime(
        data["last_updated"]["string"], "%Y-%m-%d %H:%M:%S.%f"
    )

    task = TaskDocument(**data)
    return task


def test_vibration(test_tasks):
    task = test_tasks[0]

    vib_doc = VibrationDoc.from_task(
        task, molecule_id="b9ba54febc77d2a9177accf4605767db-C1Li2O3-1-2"
    )
    assert vib_doc.property_name == "vibrations"
    assert len(vib_doc.frequencies) == 27
    assert len(vib_doc.frequency_modes) == 27
    assert len(vib_doc.ir_intensities) == 27
    assert vib_doc.frequencies[0] == pytest.approx(49.47)
    assert vib_doc.ir_intensities[0] == pytest.approx(93.886)
    assert vib_doc.ir_activities[0] is True


def test_raman(raman_task):
    vib_doc = VibrationDoc.from_task(
        raman_task, molecule_id="b9ba54febc77d2a9177accf4605767db-C1Li2O3-1-2"
    )

    assert vib_doc.raman_activities is not None
    assert vib_doc.raman_intensities[0] == pytest.approx(0.424)
