from dotations.search import search_commune_by_name  # type: ignore


def test_paris():
    # Verifie les champs renvoyés
    recherche_resultats = search_commune_by_name("paris")
    # Au moins un resultat
    assert len(recherche_resultats) >= 1
    # Chaque élément du résultat contient les bons champs
    for resultat in recherche_resultats:
        for champ in ["code", "name", "departement", "potentielFinancierParHab", "habitants"]:
            assert champ in resultat


def test_nombre_max_resultats():
    # Verifie les champs renvoyés
    recherche_resultats = search_commune_by_name("a")
    assert len(recherche_resultats) == 20
    # Chaque élément du résultat contient les bons champs
    for resultat in recherche_resultats:
        for champ in ["code", "name", "departement", "potentielFinancierParHab", "habitants"]:
            assert champ in resultat
