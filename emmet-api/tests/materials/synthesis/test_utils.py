import os
from json import load
from emmet.api.routes.materials.synthesis.utils import (
    make_ellipsis,
    mask_paragraphs,
    mask_highlights,
)
from emmet.api.core.settings import MAPISettings
from emmet.core.synthesis import SynthesisSearchResultModel


def test_make_ellipsis():
    text = "Lorem ipsum dolor sit amet"
    altered_text = make_ellipsis(text, limit=10)
    assert altered_text == "Lorem ..."

    altered_text = make_ellipsis(text, limit=10, remove_trailing=False)
    assert altered_text == "... sit amet"


def test_mask_paragraphs():
    with open(os.path.join(MAPISettings().TEST_FILES, "synth_doc.json")) as file:
        synth_doc = load(file)

    doc = SynthesisSearchResultModel(**synth_doc)
    new_doc = mask_paragraphs(doc.model_dump(), limit=10)

    assert new_doc["paragraph_string"] == "Lorem ..."


def test_mask_highlights():
    with open(os.path.join(MAPISettings().TEST_FILES, "synth_doc.json")) as file:
        synth_doc = load(file)

    doc = SynthesisSearchResultModel(**synth_doc)
    new_doc = mask_highlights(doc.model_dump(), limit=10)
    assert new_doc["highlights"][0]["texts"][0]["value"] == "... anim ..."
