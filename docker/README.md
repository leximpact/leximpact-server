# Utilisation de LexImpact Server avec Docker

## Pre-requis

Cloner le projet server et le client dans un dossier et se rendre dans leximpact-server.
```sh
git clone https://github.com/leximpact/leximpact-client.git
git clone https://github.com/leximpact/leximpact-server.git
```

Préparer la configuration :
```sh
cd leximpact-client
cp docker/docker-local.env .env
cd ../leximpact-server
cp docker/docker.env .env
```
Les paramètres par défaut fonctionnent, voir le README principale pour l'explication des paramètres.

## Lancement

```sh
docker-compose up -d
```
Ceci va exécuter :
 - Postgresql sur le port 5479
 - PGAdmin 4 pour administrer la base (facultatif) [http://localhost:5050](http://localhost:5050) login : *test@test.com* , password : *test* (Dans PGAdmin, utiliser le host *postgres_leximpact* et le port *5432* car il est dans le sous-réseau docker)
 - leximpact-server [http://localhost:5079](http://localhost:5079)
 - leximpact-client [http://localhost:9079](http://localhost:9079)


## Arrêt

Pour arrêter :
```sh
docker-compose down
```

La base Postgres et la configuration PGAdmin sont stockées dans des volumes séparés, elles sont donc conservées après la destruction des containeurs.

## Voir les logs

```sh
docker logs leximpact-server_leximpact_server_1
docker logs leximpact-server_leximpact_client_1
```
Ajouter '-f' à la fin de la ligne pour voir les mises à jour s'afficher. Ctrl+c pour arrêter le défillement.

## Executer les tests
```sh
docker exec leximpact-server_leximpact_server_1 pytest
```

## Forcer le build
```sh
docker-compose up --build
```


## Nettoyage
Efface les conteneurs, les volumes et les images :
```sh
docker-compose down -v
docker image rm leximpact-server_leximpact_server leximpact-server_leximpact_client
```