import itertools
import logging
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

from entities.fattore import Fattore
from entities.infortunio import StatoInfortunio, Locazione, Settore, Infortunio
from entities.lavoratore import Lavoratore
from utils import sleep, parse_int, parse_date


class Wrapper:

    def __init__(self):
        self.sleep_between_requests: float = 0.2

        self.factor_json_url = "https://www.inail.it/sol-informo/dettaglioFattore.do"
        self.injury_json_url = "https://www.inail.it/sol-informo/dettagliInfortunio.do"
        self.filters_json_url = "https://www.inail.it/sol-informo/filtra.do"



        self.injury_page_url = "https://www.inail.it/sol-informo/dettaglio.do?codiceInfortunio="
        self.title_before_description_injury_page = "Descrizione della dinamica e dei relativi fattori"

        # Path of ids
        self.path_ids_pickle = "./assets/dataframe_ids.pkl"
        self.path_ids_csv = "./assets/dataframe_ids.csv"
        self.ids_dataframe = None
        self.already_retrieved_combinations = []

    def read_dataframe(self):
        try:
            self.ids_dataframe = pd.read_pickle(self.path_ids_pickle)
            # Apriamo il dataframe contenente tutti gli ID che abbiamo recuperato. Da qui, estraiamo tutte
            # le combinazioni già analizzate di StatoInfortunio, Locazione e Settore.
            #

            self.already_retrieved_combinations = list(
                map(lambda t: (StatoInfortunio[t[0]], Locazione[t[1]], Settore[t[2]]),
                    list(self.ids_dataframe[["StatoInfortunio", "Locazione", "Settore"]]
                         .drop_duplicates()
                         .itertuples(index=False, name=None))
                    )
            )

            # wrapper.ids_dataframe = wrapper.ids_dataframe.drop(
            #     wrapper.ids_dataframe[wrapper.ids_dataframe["Locazione"] == Locazione.SudEIsole.name].index
            # )
            # wrapper.ids_dataframe.to_pickle(wrapper.path_ids_pickle)
            # wrapper.ids_dataframe[(wrapper.ids_dataframe["Locazione"] == Locazione.SudEIsole.name) & (
            #             wrapper.ids_dataframe["Settore"] == Settore.Metallurgia.name) & (
            #                                   wrapper.ids_dataframe["StatoInfortunio"] == StatoInfortunio.Grave.name)]
            print()
        except FileNotFoundError:
            logging.debug('Nessun dataframe presente.')
            self.create_new_dataframe()

    def retrieve_filtered_ids(self,
                              stato_infortunio: StatoInfortunio,
                              locazione: Locazione,
                              settore: Settore):

        ids = []
        last_page = False
        page_number = 1
        payload = {
            "listaFiltri": [
                {
                    "voce": "Settore Attività",
                    "codiceAgg": str(settore.value)
                },
                {
                    "voce": "Localizzazioneterritoriale",
                    "codiceAgg": str(locazione.value)
                }
            ],
            "dates": [],
            "tipoEvento": str(stato_infortunio.value),
            "numeroPagina": page_number,
            "pericoli": []
        }

        while not last_page:
            response = requests.post(self.filters_json_url, json=payload)
            response = response.json()
            lista_infortuni = response.get("result", {}).get("listaInfortuni")

            if isinstance(lista_infortuni, list) and lista_infortuni:
                for o in lista_infortuni:
                    ids.append(o.get("codiceInfortunio"))

                page_number += 1
                payload["numeroPagina"] = page_number
            else:
                last_page = True

            sleep(self.sleep_between_requests)

        return ids

    def create_new_dataframe(self):
        self.ids_dataframe = pd.DataFrame(columns=["id", "StatoInfortunio", "Locazione", "Settore"])

    def scrape_ids(self):
        """
        Per ogni combinazione di tipologia infortunio, Locazione e Settore,
        recuperiamo la lista ID degli infortuni.
        Aggingiamo anche la località perché nella pagina con i dettagli
        dell'infortunio non è presente la località dell'infortunio.
        In already_retrieved_combinations avremo tutte le combinazioni già analizzate e salvate nel dataframe in
        assets. Così facendo, nel caso in cui ci siano problemi durante il recupero degli IDs, manterremo salvati
        gli ID già analizzati.
        Nota: La ricerca nella pagina è fatta con chiamate AJAX per evitare di ri-aggiornare la pagina.
              I filtri non sono passati tramite URL, ma tramite un JSON come session storage.
        """

        for types in itertools.product([si for si in StatoInfortunio],
                                       [lo for lo in Locazione],
                                       [s for s in Settore]):

            if types in self.already_retrieved_combinations:
                continue

            ids = self.retrieve_filtered_ids(stato_infortunio=types[0],
                                             locazione=types[1],
                                             settore=types[2])

            # Ogni volta che finisce lo scraping per una determinata combinazione,
            # procediamo ad espandere il dataframe e salvare i dati.
            logging.debug('Aggiungendo ids per {} - {} - {}.'.format(types[0].name, types[1].name, types[2].name))
            for i in ids:
                self.ids_dataframe = self.ids_dataframe.append({
                    "id": int(i),
                    "StatoInfortunio": types[0].name,
                    "Locazione": types[1].name,
                    "Settore": types[2].name
                }, ignore_index=True)

            self.ids_dataframe.to_pickle(self.path_ids_pickle)
            self.ids_dataframe.to_csv(self.path_ids_csv, index=False)
            logging.debug(
                'Ids per {} - {} - {} aggiunti correttamente.'.format(types[0].name, types[1].name, types[2].name)
            )

    def retrieve_injury_details(self, injury_id, **details):
        """
        Metodo che apre la pagina dell'infortunio specificata da injury_id.
        Questa parte è necessaria per recuperare la descrizione completa,
        più gli ID relativi ai fattori. Con questi ID possiamo poi procedere
        ad eseguire le richieste POST per ottenere i JSON specifici sui
        fattori e sul dettaglio dell'infortunio.

        In details sono contenute:
            - Locazione
            - Settore
            - StatoInfortunio
        """

        # Apriamo la pagina corrispondente all'infortunio
        page = requests.get(
            'https://www.walmart.com/ip/GoGreen-Power-6-Outlet-Surge-Protector-16103MS-2-5-cord-White/46097919')
        page = BeautifulSoup(page, 'lxml')

        injury_description = \
            page.find("h3", string=self.title_before_description_injury_page) \
                .find_next_sibling() \
                .get_text() \
                .strip()

        factors_ids = [tag.get("onclick")[:-1].replace("apriDettagliFattore(", "") for tag in
                       page.find_all("button", {"onclick": re.compile("apriDettagliFattore\([0-9]{1,6}\)")})]

        factors = []
        for f_id in factors_ids:
            factors.append(self.retrieve_factor(f_id))
            sleep(self.sleep_between_requests)

        response = requests.post(self.injury_json_url, injury_id)
        response = response.json()

        # Il JSON è composto da vari JSON Objects, nella quale gran parte dei valori
        # sono ripetuti (Guardare l'esempio in assets).

        workers = []
        for o in response:
            workers.append(Lavoratore(
                lavoratore_id=o.get("codiceInfortunato"),
                sesso=o.get("sesso"),
                nazionalita=o.get("cittadinanza"),
                tipo_contratto=o.get("rapLav"),
                mansione=o.get("mansione"),
                anzianita=o.get("anzianita"),
                numero_addetti_azienda=parse_int(o.get("numAddetti")),
                attivita_prevalente_azienda=o.get("attPrev"),
                sede_lesione=o.get("sedeLesione"),
                natura_lesione=o.get("naturaLesione"),
                giorni_assenza_lavoro=parse_int(o.get("numeroGiorniAssenza")),
                luogo_infortunio=o.get("luogo"),
                attivita_lavoratore_durante_infortunio=o.get("tipoAtt"),
                ambiente_infortunio=o.get("agente"),
                tipo_incidente=o.get("variazEnergia"),
                incidente=o.get("incidente"),
                agente_materiale_incidente=o.get("agenteMatInc")
            ))

        return Infortunio(
            id=injury_id,
            stato=StatoInfortunio(details.get("StatoInfortunio")),
            settore_attivita=Settore(details.get("Settore")),
            locazione=Locazione(details.get("Locazione")),
            descrizione=injury_description,
            data=parse_date(response[0].get("dataInfortunio")),
            ora_ordinale=parse_int(response[0].get("oraLavoro")),
            fattori=factors,
            lavoratori=workers,
        )

    def retrieve_factor(self, factor_id):
        response = requests.post(self.factor_json_url, factor_id)
        response = response.json()
        return Fattore(
            fattore_id=response.get("codiceFattore"),
            descrizione=response.get("descrizioneFattore"),
            tipologia=response.get("tipoFattore"),
            determinante_modulatore=response.get("detMod"),
            tipo_modulazione=response.get("tipoMod"),
            problema_sicurezza=response.get("descrizioneProblSic"),
            confronto_standard=response.get("confrontoStand"),
            valutazione_rischi=response.get("valRisc"),
            stato_processo=response.get("statoProc"),
            classificazione=response.get("classificazione")
        )
