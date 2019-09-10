import pandas  # type: ignore
from pandas.util.testing import assert_frame_equal  # type: ignore
import numpy as np  # type: ignore

from Simulation_engine.simulate_pop_from_reform import (  # type: ignore
    load_data,
    adjustment,
    adjust_total,
    adjust_deciles,
    calcule_maillage_intervalle,
    CAS_TYPE,
    compare,
    dataframe_from_cas_types_description,
    DUMMY_DATA,
    IncomeTaxReform,
    PERIOD,
    simulation,
    simulation_base_castypes,
    CompareOldNew,
    simulation_plf_castypes,
    TBS,
)


def test_load_data_when_h5(mocker):
    with mocker.patch.object(pandas, "read_hdf"):
        filename = "data.h5"
        load_data(filename)
        pandas.read_hdf.assert_called_once()


def test_load_data_when_not_h5(mocker):
    with mocker.patch.object(pandas, "read_csv"):
        filename = "data.zip"
        load_data(filename)
        pandas.read_csv.assert_called_once()


def test_adjustment():
    empiric = 4
    baseline = 2
    assert adjustment(empiric, baseline) == 2


def test_adjust_total():
    actual = adjust_total(2, {"avant": 2, "apres": 4})
    expected = {"avant": 4, "apres": 8}

    assert actual == expected


def test_adjust_deciles():
    actual = adjust_deciles(2, [{"poids": 1, "avant": 2, "apres": 3}])
    expected = [{"poids": 2, "avant": 4, "apres": 6}]

    assert actual == expected


def test_dataframe_from_cas_types_description():
    cas_types_description = {}  # Cf. desc_cas_types()

    expected_data_columns = [
        "index",
        "activite",
        "age",
        "categorie_salarie",
        "chomage_brut",
        "chomage_imposable",
        "contrat_de_travail",
        "date_naissance",
        "effectif_entreprise",
        "heures_remunerees_volume",
        "idfam",
        "idfoy",
        "idmen",
        "pensions_alimentaires_percues",
        "quifam",
        "quifoy",
        "quimen",
        "rag",
        "retraite_brute",
        "ric",
        "rnc",
        "statut_marital",
        "salaire_de_base",
        "taux_csg_remplacement",
        "f4ba",
        "loyer",
        "statut_occupation_logement",
        "taxe_habitation",
        "wprm",
        "zone_apl",
        "quimenof",
        "residence_fiscale_guadeloupe",
        "residence_fiscale_guyane",
        "quifoyof",
        "quifamof",
        "caseL",
        "caseT",
        "caseW",
        "garde_alternee",
        "invalidite",
    ]
    expected_simulation_data = pandas.DataFrame(
        columns=expected_data_columns,
        index=pandas.RangeIndex(start=0, stop=0, step=1),
        dtype="float64",
    )

    simulation_data = dataframe_from_cas_types_description(cas_types_description)
    print("expected_simulation_data", expected_simulation_data)
    print("simulation_data", simulation_data)
    assert_frame_equal(simulation_data, expected_simulation_data)


def test_calcule_maillage_intervalle():
    nom_colonne = "salaire_de_base"
    min_value_colonne = 15600

    expected_data_columns = [nom_colonne]
    expected_data = np.array(
        [min_value_colonne, 17160, 18876, 20763.600, 22839.960, 25123.956],
        dtype="float64",
    )
    expected = pandas.DataFrame(
        [[x] for x in expected_data], columns=expected_data_columns
    )
    for name in ["idfam", "idfoy", "idmen"]:
        expected[name] = range(0, 6)
    for name in ["quifam", "quifoy", "quimen"]:
        expected[name] = 0

    max_value_colonne = 25405
    pourcentage_hausse = 0.1
    valeur_hausse = pourcentage_hausse * min_value_colonne
    revenus_bruts = calcule_maillage_intervalle(
        nom_colonne,
        min_value_colonne,
        max_value_colonne,
        pourcentage_hausse,
        valeur_hausse,
    )

    assert_frame_equal(revenus_bruts, expected, check_dtype=False)


dictreform = {
    "impot_revenu": {
        "bareme": {
            "seuils": [0, 9964, 27159, 73779, 156244],
            "taux": [0, 0.14, 0.30, 0.41, 0.45],
        },
        "decote": {"seuil_celib": 1196, "seuil_couple": 1970, "taux": 0.75},
        "plafond_qf": {
            "abat_dom": {
                "taux_GuadMarReu": 0.3,
                "plaf_GuadMarReu": 2450,
                "taux_GuyMay": 0.4,
                "plaf_GuyMay": 4050,
            },
            "maries_ou_pacses": 1551,
            "celib_enf": 3660,
            "celib": 927,
            "reduc_postplafond": 1547,
            "reduc_postplafond_veuf": 1728,
            "reduction_ss_condition_revenus": {
                "seuil_maj_enf": 3797,
                "seuil1": 18985,
                "seuil2": 21037,
                "taux": 0.20,
            },
        },
    }
}
reform = IncomeTaxReform(TBS, dictreform, PERIOD)


def test_sim_pop_dict_content():
    simulation_reform = simulation(PERIOD, DUMMY_DATA, reform)
    comp_result = compare(PERIOD, {"apres": simulation_reform})
    assert "total" in comp_result
    assert "deciles" in comp_result
    # assert len(comp_result["deciles"])==10 Removed cause with the cas type description
    for key in ["avant", "apres", "plf"]:
        assert key in comp_result["total"]
        assert key in comp_result["deciles"][0]


def test_sim_base_cas_types_dict_content_ok():
    simulation_reform = simulation(PERIOD, CAS_TYPE, reform)
    comp_result = compare(
        PERIOD,
        {
            "avant": simulation_base_castypes,
            "plf": simulation_plf_castypes,
            "apres": simulation_reform,
        },
        compute_deciles=False,
    )
    assert "total" in comp_result
    assert "res_brut" in comp_result
    # assert len(comp_result["deciles"])==10 Removed cause with the cas type description
    for key in ["avant", "apres", "plf"]:
        assert key in comp_result["total"]
        assert key in comp_result["res_brut"]
        assert len(comp_result["res_brut"][key]) == 6


def test_sim_custom_cas_types_dict_content_ok():
    dict_cas = [
        {
            "nombre_declarants": 1,
            "nombre_declarants_retraites": 0,
            "nombre_personnes_a_charge": 1,
            "outre_mer": 0,
            "revenu": 31200,
            "nb_decl_parent_isole": 0,
            "nb_decl_veuf": 0,
            "nb_decl_invalides": 0,
            "nb_pac_invalides": 0,
            "nb_anciens_combattants": 0,
            "nb_pac_charge_partagee": 0,
        },
        {
            "nombre_declarants": 2,
            "nombre_declarants_retraites": 0,
            "nombre_personnes_a_charge": 2,
            "outre_mer": 0,
            "revenu": 31200,
            "nb_decl_parent_isole": 0,
            "nb_decl_veuf": 0,
            "nb_decl_invalides": 0,
            "nb_pac_invalides": 0,
            "nb_anciens_combattants": 1,
            "nb_pac_charge_partagee": 0,
        },
    ]
    comp_result = CompareOldNew(
        isdecile=False, dictreform=dictreform, castypedesc=dict_cas
    )
    assert "total" in comp_result
    assert "res_brut" in comp_result
    # assert len(comp_result["deciles"])==10 Removed cause with the cas type description
    for key in ["avant", "apres", "plf"]:
        assert key in comp_result["total"]
        assert key in comp_result["res_brut"]
        assert len(comp_result["res_brut"][key]) == len(dict_cas)
