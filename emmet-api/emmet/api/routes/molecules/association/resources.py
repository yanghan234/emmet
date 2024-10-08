from maggma.api.resource.read_resource import ReadOnlyResource
from maggma.api.resource.post_resource import PostOnlyResource

from emmet.core.find_structure import FindMolecule
from emmet.core.qchem.molecule import MoleculeDoc

from maggma.api.query_operator import (
    PaginationQuery,
    SparseFieldsQuery,
    NumericQuery,
)

from emmet.api.routes.molecules.molecules.hint_scheme import MoleculesHintScheme
from emmet.api.routes.molecules.molecules.query_operators import (
    FormulaQuery,
    ChemsysQuery,
    CompositionElementsQuery,
    ChargeSpinQuery,
    DeprecationQuery,
    MultiTaskIDQuery,
    MultiMPculeIDQuery,
    FindMoleculeQuery,
    CalcMethodQuery,
    HashQuery,
    StringRepQuery,
)

from emmet.api.core.global_header import GlobalHeaderProcessor
from emmet.api.core.settings import MAPISettings

timeout = MAPISettings().TIMEOUT


def find_molecule_assoc_resource(assoc_store):
    resource = PostOnlyResource(
        assoc_store,
        FindMolecule,
        key_fields=["molecule", "molecule_id"],
        query_operators=[FindMoleculeQuery()],
        tags=["Associated Molecules"],
        sub_path="/assoc/find_molecule/",
        timeout=timeout,
    )

    return resource


def mol_assoc_resource(assoc_store):
    resource = ReadOnlyResource(
        assoc_store,
        MoleculeDoc,
        query_operators=[
            MultiMPculeIDQuery(),
            FormulaQuery(),
            ChemsysQuery(),
            CompositionElementsQuery(),
            ChargeSpinQuery(),
            MultiTaskIDQuery(),
            CalcMethodQuery(),
            HashQuery(),
            StringRepQuery(),
            DeprecationQuery(),
            NumericQuery(model=MoleculeDoc),
            PaginationQuery(),
            SparseFieldsQuery(
                MoleculeDoc,
                default_fields=["molecule_id", "formula_alphabetical", "last_updated"],
            ),
        ],
        header_processor=GlobalHeaderProcessor(),
        tags=["Associated Molecules"],
        sub_path="/assoc/",
        disable_validation=True,
        hint_scheme=MoleculesHintScheme(),
        timeout=MAPISettings().TIMEOUT,
    )

    return resource
