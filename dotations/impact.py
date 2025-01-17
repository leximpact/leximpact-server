from pandas import DataFrame  # type: ignore
from typing import Optional, List

BORNES_STRATES_DEFAULT = [0, 500, 2000, 5000, 10000, 20000, 50000, 100000, 1000000000000]  # bornes des strates en terme de POP INSEE


def get_cas_types_codes_insee():
    return ["76384", "76214"]  # sera paramétrable par l'usager


def build_response_dotations_cas_types(scenario, df_results, prefix_eligible, prefix_montant, communes_cas_types=None, prefix_next_year=None, prefix_annees_convergence=None):
    # construit une réponse d'éligibilité/montant : un tableau contenant un dictionnaire qui a pour clefs
    # "code" (code commune), "eligible" (booleen décrivant si la commune est éligible), "dotationParHab" (dotation moyenne par hab INSEE)
    # [scenario_api]["communes"]["dsr"] et [scenario_api]["communes"]["dsu"]
    # > ["communes"]
    response = []
    code_comm = "Informations générales - Code INSEE de la commune"
    if communes_cas_types is None:
        communes_cas_types = get_cas_types_codes_insee()
    for cas_type in communes_cas_types:
        res_cas_type = df_results[df_results[code_comm].astype(str) == cas_type]
        if not len(df_results):  # commune was not found. We need to tell the client!!!
            response += [{"code": cas_type, "Error": "Commune was not found. Where did you get this code INSEE?"}]
        else:
            pop_cas_type = res_cas_type["population_insee"].values[0]
            res_cas_types_dict = {"code": cas_type}
            if prefix_eligible is not None:
                cas_type_eligible = bool(
                    res_cas_type[prefix_eligible + scenario].values[0]
                )
                res_cas_types_dict["eligible"] = cas_type_eligible
            if prefix_montant is not None:
                montant_cas_type = res_cas_type[prefix_montant + scenario].values[0]
                res_cas_types_dict["dotationParHab"] = float(
                    montant_cas_type / pop_cas_type
                )
            if prefix_next_year is not None:
                montant_cas_type_next_year = res_cas_type[prefix_next_year + scenario].values[0]
                res_cas_types_dict["dotationParHabAnneeSuivante"] = float(montant_cas_type_next_year / pop_cas_type)
            if prefix_annees_convergence is not None:
                montant_cas_type_annee_convergence = res_cas_type[prefix_annees_convergence + scenario].values[0]
                res_cas_types_dict["dureeAvantTerme"] = int(montant_cas_type_annee_convergence)
            response += [res_cas_types_dict]

    return response


def build_response_dotations_eligibilites(scenario, df_results, prefix_eligible):
    # [scenario_api]["communes"]["dsr"]
    # > ["eligibles"]
    response = {}
    response["eligibles"] = int(df_results[prefix_eligible + scenario].sum())

    return response


def build_response_dotations_eligibilites_changements(scenario, df_results, prefix_eligible):
    # ["baseTo" + scenario]["communes"]["dsr"] et dsu
    # > ["nouvellementEligibles"]/["plusEligibles"]/["toujoursEligibles"]
    response = {}
    response["nouvellementEligibles"] = len(df_results[(df_results[prefix_eligible + scenario]) & (~df_results[prefix_eligible + "base"])])
    response["plusEligibles"] = len(df_results[(~df_results[prefix_eligible + scenario]) & (df_results[prefix_eligible + "base"])])
    response["toujoursEligibles"] = len(df_results[(df_results[prefix_eligible + scenario]) & (df_results[prefix_eligible + "base"])])

    return response


def build_response_dotations_strates(scenario, df_results, prefix_eligible=None, prefix_montant=None, strates: Optional[list] = None):
    # [scenario_api]["dotations"]["communes"]["dsr"]
    # > ["strates"]
    BORNES_STRATES = BORNES_STRATES_DEFAULT if strates is None else strates
    # tableau nombre de communes éligibles par strate
    resultats_agreges_bornes: List[dict] = [{} for borne in BORNES_STRATES]

    # pour une borne, aggrège les résultats de toute la population
    # située au niveau supérieur ou égal à la borne
    for id_borne in range(len(BORNES_STRATES)):  # id borne : the borne identity
        borne = BORNES_STRATES[id_borne]
        df_strate = df_results[df_results["population_insee"] >= borne]
        resultats_agreges_bornes[id_borne]["population_insee"] = int(df_strate["population_insee"].sum())
        resultats_agreges_bornes[id_borne]["potentiel_financier"] = float(df_strate["potentiel_financier" + "_" + scenario].sum())
        if prefix_eligible is not None:
            resultats_agreges_bornes[id_borne]["eligibles"] = int(df_strate[prefix_eligible + scenario].sum())
        if prefix_montant is not None:
            resultats_agreges_bornes[id_borne]["montant"] = int(df_strate[prefix_montant + scenario].sum())
        resultats_agreges_bornes[id_borne]["nombre_communes"] = len(df_strate)

    res_strates: List[dict] = [{} for borne in BORNES_STRATES[:-1]]
    for id_borne in range(len(BORNES_STRATES) - 1):
        res_strates[id_borne]["habitants"] = BORNES_STRATES[id_borne]
        pop_strate = resultats_agreges_bornes[id_borne]["population_insee"] - resultats_agreges_bornes[id_borne + 1]["population_insee"]
        res_strates[id_borne]["partPopTotale"] = pop_strate / resultats_agreges_bornes[0]["population_insee"]
        pot_strate = resultats_agreges_bornes[id_borne]["potentiel_financier"] - resultats_agreges_bornes[id_borne + 1]["potentiel_financier"]
        res_strates[id_borne]["potentielFinancierMoyenParHabitant"] = pot_strate / pop_strate

        if prefix_eligible is not None:
            nb_elig_strate = resultats_agreges_bornes[id_borne]["eligibles"] - resultats_agreges_bornes[id_borne + 1]["eligibles"]
            nombre_communes_strate = resultats_agreges_bornes[id_borne]["nombre_communes"] - resultats_agreges_bornes[id_borne + 1]["nombre_communes"]
            res_strates[id_borne]["eligibles"] = nb_elig_strate
            res_strates[id_borne]["partEligibles"] = (nb_elig_strate / nombre_communes_strate) if nombre_communes_strate else 0
        res_strates[id_borne]["dotationMoyenneParHab"] = max(0, resultats_agreges_bornes[id_borne]["montant"] - resultats_agreges_bornes[id_borne + 1]["montant"]) / pop_strate
        res_strates[id_borne]["partDotationTotale"] = (
            (resultats_agreges_bornes[id_borne]["montant"] - resultats_agreges_bornes[id_borne + 1]["montant"]) / resultats_agreges_bornes[0]["montant"]
        ) if resultats_agreges_bornes[0]["montant"] else 0

    return res_strates


def build_response_dotations(scenario: str, df_results: DataFrame, prefix_eligible: Optional[str], prefix_montant: Optional[str], communes_cas_types: Optional[list] = None, strates: Optional[list] = None, prefix_annees_convergence=None, prefix_next_year=None) -> dict:
    resultat = {
        "communes": build_response_dotations_cas_types(scenario, df_results, prefix_eligible, prefix_montant, communes_cas_types=communes_cas_types, prefix_next_year=prefix_next_year, prefix_annees_convergence=prefix_annees_convergence),
        "strates": build_response_dotations_strates(scenario, df_results, prefix_eligible, prefix_montant, strates=strates)
    }
    if prefix_eligible is not None:
        eligibilites = build_response_dotations_eligibilites(scenario, df_results, prefix_eligible)
        resultat = {**resultat, **eligibilites}
    return resultat
