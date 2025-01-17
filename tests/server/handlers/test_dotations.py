from functools import partial
import json
from pytest import fixture  # type: ignore

from dotations.impact import BORNES_STRATES_DEFAULT, get_cas_types_codes_insee  # type: ignore
from Simulation_engine.simulate_dotations import ACTIVATE_PLF  # type: ignore
from utils.utils_dict import flattened_dict  # type: ignore


def request_strates_from_bornes_strates(bornes_strates):
    bornes_strates[-1] = -1
    return [{"habitants": borne} for borne in bornes_strates[1:]]


def _distance_listes(a, b):
    return max([abs(x - y) for (x, y) in zip(a, b)])


@fixture(scope="module")
def codes_communes_examples():
    return get_cas_types_codes_insee()


@fixture(scope="module")
def request_dotations(codes_communes_examples):
    request = {
        "reforme": {
            "dotations": {
                "montants": {
                    "dgf": 31
                },
                "communes": {
                    "dsr": {
                        "eligibilite": {
                            "popMax": 500  # de 10 000 à 500
                        }
                    },
                    "dsu": {
                        "eligibilite": {
                            "popMinSeuilBas": 500  # de 5 000 à 500
                        }
                    }
                }
            }
        },
        "descriptionCasTypes": [
            {"code": code_insee_cas_type}
            for code_insee_cas_type in codes_communes_examples
        ],
        "strates": request_strates_from_bornes_strates(BORNES_STRATES_DEFAULT),
    }
    return request


@fixture(scope="module")
def response_dotations(client, headers, request_dotations):
    response_function = partial(client.post, "dotations", headers=headers)
    response = response_function(data=json.dumps(request_dotations))
    return json.loads(response.data)


@fixture(scope="module")
def request_dotations_2(codes_communes_examples):
    request = {
        "reforme": {
            "dotations": {
                "montants": {
                    "dgf": 31
                },
                "communes": {
                    "dsu": {
                        "eligibilite": {
                            "popMinSeuilHaut": 8000  # de 10 000 à 8 000
                        }
                    }
                }
            }
        },
        "descriptionCasTypes": [
            {"code": code_insee_cas_type}
            for code_insee_cas_type in codes_communes_examples
        ],
        "strates": request_strates_from_bornes_strates(BORNES_STRATES_DEFAULT),
    }
    return request


@fixture(scope="module")
def response_dotations_2(client, headers, request_dotations_2):
    response_function = partial(client.post, "dotations", headers=headers)
    response = response_function(data=json.dumps(request_dotations_2))
    return json.loads(response.data)


def test_dotations_request_body_error(client, headers):
    request = {}

    response_function = partial(client.post, "dotations", headers=headers)
    response = response_function(data=json.dumps(request))

    assert response.status_code == 400
    assert "Error" in json.loads(response.data)


def test_dotations(client, headers, request_dotations):
    response_function = partial(client.post, "dotations", headers=headers)
    response = response_function(data=json.dumps(request_dotations))

    assert response.status_code == 200


def test_fields_response(response_dotations):
    expected_response_structure = {
        "amendement": {
            "communes": {
                "dsr": {"communes": [], "eligibles": 17049, "strates": []},
                "dsu": {"communes": [], "eligibles": 812, "strates": []},
                "df": {"communes": [], "strates": []},
            }
        },
        "base": {
            "communes": {
                "dsr": {"communes": [], "eligibles": 33164, "strates": []},
                "dsu": {"communes": [], "eligibles": 812, "strates": []},
                "df": {"communes": [], "strates": []},
            }
        },
        "baseToAmendement": {
            "communes": {
                "dsr": {
                    "nouvellementEligibles": 0,
                    "plusEligibles": 16115,
                    "toujoursEligibles": 17049,
                },
                "dsu": {
                    "nouvellementEligibles": 0,
                    "plusEligibles": 0,
                    "toujoursEligibles": 812,
                }
            }
        }
    }

    if ACTIVATE_PLF:
        expected_response_structure["plf"] = {
            "communes": {
                "dsr": {
                    "communes": [],
                    "eligibles": 33159,
                    "strates": []
                },
                "dsu": {
                    "communes": [],
                    "eligibles": 818,
                    "strates": []
                },
                "df": {"communes": [], "strates": []},
            }
        }
        expected_response_structure["baseToPlf"] = {
            "communes": {
                "dsr" : {
                    "nouvellementEligibles": 0,
                    "plusEligibles": 0,
                    "toujoursEligibles": 33159,
                },
                "dsu" : {
                    "nouvellementEligibles": 0,
                    "plusEligibles": 0,
                    "toujoursEligibles": 818,
                }
            }
        }

    result = response_dotations

    # Vérification des clefs du dictionnaire (sauf celles incluses dans un array)
    flattened_result_keys = set(flattened_dict(result).keys())
    flattened_expected_keys = set(flattened_dict(expected_response_structure).keys())
    assert flattened_result_keys == flattened_expected_keys


def test_dsr_reform_eligibilite_montants(response_dotations):
    result = response_dotations
    base_dsr = result["base"]["communes"]["dsr"]
    amendement_dsr = result["amendement"]["communes"]["dsr"]

    # Vérification des valeurs connues :
    # Les nombres de communes éligibles de base sont ceux attendus
    expected_strates_eligibilite_base = [17731, 11113, 3166, 1094, 55, 0, 0, 0]
    assert expected_strates_eligibilite_base == [strate["eligibles"] for strate in base_dsr["strates"]]

    # Moins de communes éligibles après que avant.
    assert (base_dsr["eligibles"] > amendement_dsr["eligibles"])
    # Les nombres affichés dans l'amendement sont cohérents avec la base
    base_to_amendement = result["baseToAmendement"]["communes"]["dsr"]
    assert(amendement_dsr["eligibles"] == base_to_amendement["toujoursEligibles"] + base_to_amendement["nouvellementEligibles"])
    assert(base_dsr["eligibles"] == amendement_dsr["eligibles"] - base_to_amendement["nouvellementEligibles"] + base_to_amendement["plusEligibles"])

    # Montants : cohérence : les strates ont une dotation non nulle si et seulement si elles sont éligibles
    for scenario_strates in [base_dsr["strates"], amendement_dsr["strates"]]:
        for strate in scenario_strates:
            assert((strate["dotationMoyenneParHab"] > 0) == (strate["eligibles"] > 0))
            assert((strate["dotationMoyenneParHab"] > 0) == (strate["partEligibles"] > 0))


def test_dsr_reform_cas_types(response_dotations, codes_communes_examples):
    result = response_dotations
    base_dsr = result["base"]["communes"]["dsr"]
    amendement_dsr = result["amendement"]["communes"]["dsr"]

    # même nombre de cas types en loi actuelle et amendement
    # Les cas_types sont ceux attendus
    assert (codes_communes_examples
            == [cas_type["code"] for cas_type in base_dsr["communes"]]
            == [cas_type["code"] for cas_type in amendement_dsr["communes"]]
            )

    # Vérification des clefs du dictionnaire contenues dans un array :
    # cas-types
    expected_cas_type_keys = set(["code", "eligible", "dotationParHab", "dureeAvantTerme", "dotationParHabAnneeSuivante"])
    for cas_type in base_dsr["communes"] + amendement_dsr["communes"]:
        assert set(cas_type.keys()) == expected_cas_type_keys

    # Les deux cas types ont la même éligibilité avec la loi actuelle (on s'ennuye un peu)
    assert (len(set([cas_type["eligible"] for cas_type in base_dsr["communes"]])) == 1)

    # Montants : cohérence : les cas_types ont une dotation non nulle si et seulement si elles sont éligibles
    for scenario_cas_types in [base_dsr["communes"], amendement_dsr["communes"]]:
        for cas_type in scenario_cas_types:
            assert((cas_type["dotationParHab"] > 0) == cas_type["eligible"])


def test_dsr_reform_strates(response_dotations):
    result = response_dotations
    base_dsr = result["base"]["communes"]["dsr"]
    amendement_dsr = result["amendement"]["communes"]["dsr"]

    assert (len(BORNES_STRATES_DEFAULT) - 1) == len(base_dsr["strates"]) == len(amendement_dsr["strates"])
    assert (BORNES_STRATES_DEFAULT[:-1]
            == [description_strate["habitants"] for description_strate in base_dsr["strates"]]
            == [description_strate["habitants"] for description_strate in amendement_dsr["strates"]]
            )
    # Vérification des clefs du dictionnaire contenues dans un array :
    # strates
    expected_strates_keys = set(["eligibles", "partEligibles", "habitants", "partPopTotale", "potentielFinancierMoyenParHabitant", "dotationMoyenneParHab", "partDotationTotale"])
    for strate in base_dsr["strates"] + amendement_dsr["strates"]:
        assert set(strate.keys()) == expected_strates_keys

    # Vérification des valeurs connues :
    # part des populations des strates
    expected_strates_part_pop = [0.06007980567659335, 0.1634550394057553, 0.14799251658818824, 0.12235336069268536, 0.11186876192680593, 0.1551077737884084, 0.08977134254147147, 0.14937139938009197]
    expected_strates_potentiel_financier = [785.8454228127517, 844.2474469246844, 984.1285236926341, 1081.7606225043514, 1158.1308023454112, 1225.3727419597647, 1330.9551811110707, 1488.5004404928918]  # d'après critères de répartition 2019 loadés
    allowed_error = 0.0001
    for resultat_strates in [base_dsr["strates"], amendement_dsr["strates"]]:
        print([strate["partPopTotale"] for strate in resultat_strates])
        print([strate["potentielFinancierMoyenParHabitant"] for strate in resultat_strates])
        assert(_distance_listes(expected_strates_part_pop, [strate["partPopTotale"] for strate in resultat_strates]) < allowed_error)
        assert(_distance_listes(expected_strates_potentiel_financier, [strate["potentielFinancierMoyenParHabitant"] for strate in resultat_strates]) < allowed_error)


def test_dsu_reform_strates(response_dotations):
    result = response_dotations
    base_dsu = result["base"]["communes"]["dsu"]
    amendement_dsu = result["amendement"]["communes"]["dsu"]

    assert (len(BORNES_STRATES_DEFAULT) - 1) == len(base_dsu["strates"]) == len(amendement_dsu["strates"])
    assert (BORNES_STRATES_DEFAULT[:-1]
            == [description_strate["habitants"] for description_strate in base_dsu["strates"]]
            == [description_strate["habitants"] for description_strate in amendement_dsu["strates"]]
            )
    # Vérification des clefs du dictionnaire contenues dans un array :
    # strates
    expected_strates_keys = set(["eligibles", "partEligibles", "habitants", "partPopTotale", "potentielFinancierMoyenParHabitant", "dotationMoyenneParHab", "partDotationTotale"])
    for strate in base_dsu["strates"] + amendement_dsu["strates"]:
        assert set(strate.keys()) == expected_strates_keys

    # Vérification des valeurs connues :
    # part des populations des strates
    expected_strates_part_pop = [0.06007980567659335, 0.1634550394057553, 0.14799251658818824, 0.12235336069268536, 0.11186876192680593, 0.1551077737884084, 0.08977134254147147, 0.14937139938009197]
    expected_strates_potentiel_financier = [785.8454228127517, 844.2474469246844, 984.1285236926341, 1081.7606225043514, 1158.1308023454112, 1225.3727419597647, 1330.9551811110707, 1488.5004404928918]  # d'après critères de répartition 2019 loadés
    allowed_error = 0.0001
    for resultat_strates in [base_dsu["strates"], amendement_dsu["strates"]]:
        assert(_distance_listes(expected_strates_part_pop, [strate["partPopTotale"] for strate in resultat_strates]) < allowed_error)
        assert(_distance_listes(expected_strates_potentiel_financier, [strate["potentielFinancierMoyenParHabitant"] for strate in resultat_strates]) < allowed_error)


def test_dsr_dsu_reform_eligibles(response_dotations):
    result = response_dotations
    base_dsr = result["base"]["communes"]["dsr"]
    amendement_dsr = result["amendement"]["communes"]["dsr"]
    # Verifie que le nombre de communes éligibles à la dsr a été réduit
    # par l'amendement (qui réduit le maximum d'habitants de 10000 à 500)
    assert base_dsr["eligibles"] > amendement_dsr["eligibles"]

    base_dsu = result["base"]["communes"]["dsu"]
    amendement_dsu = result["amendement"]["communes"]["dsu"]
    # Verifie que le nombre de communes éligibles à la dsu a été accru
    # par l'amendement (qui réduit le minimum d'habitants de 5000 à 500)
    assert base_dsu["eligibles"] < amendement_dsu["eligibles"]


def test_dsu_dotation_positive(response_dotations_2):
    result = response_dotations_2
    amendement_dsu = result["amendement"]["communes"]["dsu"]
    # Verifie que le montant de DSU par habitant des strates n'est pas négatif
    for strate in amendement_dsu["strates"]:
        assert strate["dotationMoyenneParHab"] >= 0
