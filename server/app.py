import os

import connexion  # type: ignore
from flask_cors import CORS as cors  # type: ignore
import logging
from dotenv import load_dotenv
import warnings
from pandas.core.common import SettingWithCopyWarning  # type: ignore
# Wait for openfisca-core upgrade : from openfisca_core.warnings import OpenFiscaMemoryWarning, OpenFiscaTempfileWarning  # type: ignore

logging.basicConfig(level=logging.INFO)
con = connexion.App("server", specification_dir=".")
con.add_api("api.yaml")
app = con.app
cors(app, origins="*")


if __name__ == "__main__":
    load_dotenv(dotenv_path=".env")
    # Do we have to remove warning ?
    if os.environ.get("IGNORE_WARNING") == "yes":
        logging.warning('--- All SettingWithCopyWarning warnings from Pandas will be ignored ---')
        warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
        # Wait for openfisca-core upgrade : warnings.simplefilter(action="ignore", category=OpenFiscaMemoryWarning)
        # Wait for openfisca-core upgrade : warnings.simplefilter(action="ignore", category=OpenFiscaTempfileWarning)
    con.run(host=os.environ.get("HOST"), port=os.environ.get("PORT"))
