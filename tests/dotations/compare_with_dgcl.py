from dotations.simulation import simulation_from_dgcl_csv  # type: ignore
from dotations.load_dgcl_data import load_dgcl_file, adapt_dgcl_data, get_dgcl_results  # type: ignore
from openfisca_france_dotations_locales import CountryTaxBenefitSystem  # type: ignore
from time import time
#
# Petit script auxiliaire pour comparer les résultats trouvés avec notre parser + OFDL
# aux résultats trouvés.
#
# On peut en faire des tests, mais il y a un tradeoff entre correspondre plus précisément
# aux résultats DGCL et obtenir des résultats cohérents plus tard.


# Quelques noms de colonne utiles:
code_comm = "Informations générales - Code INSEE de la commune"
nom_comm = "Informations générales - Nom de la commune"


# Columns to compare that contain a bool type
# A pivot table will be printed that counts the number of values that have the different combination
def compare_results_bool(data, nom_actual, nom_expected):
    return data.pivot_table(code_comm, index=nom_actual, columns=nom_expected, aggfunc="count", fill_value=0)


# Columns to compare that contain a number
# There will be great output, e.g. :
# Absolute differences : < 1 €, quantiles extrèmes, deciles de différence
# Différence relative (osef un peu)
# Erreur quadratique
# Norme L1, L2,
def compare_results_real(data, nom_actual, nom_expected):
    res = {}
    data_non_nul = data[(data[nom_actual] != 0) | data[nom_expected] != 0]
    diff = sorted((data_non_nul[nom_actual] - data_non_nul[nom_expected]).tolist())
    nb_non_nul = len(data_non_nul)
    avg_size = sum(data_non_nul[nom_actual]) / nb_non_nul
    avg_size2 = sum([i * i for i in data_non_nul[nom_actual]]) / (nb_non_nul - 1)
    res["Moyenne base"] = avg_size
    res["variance"] = avg_size2 - avg_size * avg_size

    # Norme L1 : ecart absolu moyen
    res["L1"] = sum([abs(dif) for dif in diff]) / nb_non_nul
    # Norme L2 (norme euclidienne) : utile pour l'estimation
    res["L2"] = (sum([dif * dif for dif in diff]) / nb_non_nul)**0.5
    # Ah ben qu'est ce que je disais : la norme L2 permet de regarder
    # quelle part de variance de la variable est expliquée par notre
    # modèle
    res["pourcentage expliqué"] = 1 - res["L2"]**2 / res["variance"]
    # Différence maximale. Sert pas à grand chose.
    res["L∞"] = max([abs(dif) for dif in diff])
    quantiles = [0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.98, 0.99]
    # Statistiques d'ordre sur les différences (min, max et quantiles)
    res["min"] = min(diff)
    res["max"] = max(diff)
    res["quantiles"] = {}
    for q in quantiles:
        rang = int(q * (nb_non_nul - 1) + 0.5)
        res["quantiles"][q] = (rang, diff[rang])
    tolerance_difference = 1

    # nombre de résultats considérés comme égaux (en fonction de la tolérance acceptable)
    res["differents"] = len([d for d in diff if abs(d) > tolerance_difference])
    res["identiques"] = nb_non_nul - res["differents"]
    return res


def print_eligible_comparison():
    PERIOD = "2020"
    data_dgcl = load_dgcl_file()
    data_calc_dgcl = get_dgcl_results(data_dgcl)
    
    data_sim = adapt_dgcl_data(data_dgcl)
    TBS = CountryTaxBenefitSystem()
    sim = simulation_from_dgcl_csv(PERIOD, data_sim, TBS)

    # on va recalculer nous même toutes les colonnes (sauf le code commune)
    colonnes_to_compute = list(data_calc_dgcl.columns[1:])

    for variable_to_compute in colonnes_to_compute:
        data_sim[variable_to_compute] = sim.calculate(variable_to_compute, PERIOD)

    # Merge DGCL results with data_sim
    previous_length_data = len(data_sim)
    data_sim = data_sim.merge(data_calc_dgcl, how="inner", on=code_comm, suffixes=["", "_precalc"])
    assert(len(data_sim) == previous_length_data)
    data_sim.to_csv("data_compare.csv")

    for nom_ofdl in colonnes_to_compute:
        print("Comparaison DGCL vs nous pour le calcul de", nom_ofdl)
        if data_sim[nom_ofdl].dtypes.name == 'bool':
            print(compare_results_bool(data_sim, nom_ofdl, nom_ofdl + "_precalc"))


if __name__ == "__main__":
    st = time()
    print_eligible_comparison()
    print("Elapsed : {:.2f}".format(time() - st))
