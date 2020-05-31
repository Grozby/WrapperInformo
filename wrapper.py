import itertools
import logging
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import session, Query

from entities.base import Base, engine, Session
from entities.enums.determinante_modulatore import DeterminanteModulatore
from entities.enums.stato_processo import StatoProcesso
from entities.enums.tipo_incidente import TipoIncidente
from entities.fattore import Fattore
from entities.incidente import Incidente
from entities.infortunio import Infortunio
from entities.enums.stato_infortunio import StatoInfortunio
from entities.enums.settore import Settore
from entities.enums.locazione import Locazione
from entities.lavoratore import Lavoratore
from utils import sleep, parse_int, parse_date, get_injury_state, type_incident


class Wrapper:

    def __init__(self):
        print("Inizializzazione del wrapper...")
        self.sleep_time: float = 0.25

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

    def read_ids_dataframe(self):
        print("Lettura del file degli ID...")
        try:
            self.ids_dataframe = pd.read_pickle(self.path_ids_pickle)
            # Apriamo il dataframe contenente tutti gli ID che abbiamo recuperato. Da qui, estraiamo tutte
            # le combinazioni già analizzate di StatoInfortunio, Locazione e Settore.
            self.already_retrieved_combinations = list(
                map(lambda t: (StatoInfortunio[t[0]], Locazione[t[1]], Settore[t[2]]),
                    list(self.ids_dataframe[["StatoInfortunio", "Locazione", "Settore"]]
                         .drop_duplicates()
                         .itertuples(index=False, name=None))
                    )
            )

            print("Lettura avvenuta con successo!")
        except FileNotFoundError:
            print("Nessun dataframe presente.")
            self.create_new_dataframe()

    def retrieve_filtered_ids(self,
                              injury_state: StatoInfortunio,
                              location: Locazione,
                              sector: Settore):
        ids = []
        last_page = False
        page_number = 1
        payload = {
            "listaFiltri": [
                {
                    "voce": "Settore Attività",
                    "codiceAgg": str(sector.value)
                },
                {
                    "voce": "Localizzazioneterritoriale",
                    "codiceAgg": str(location.value)
                }
            ],
            "dates": [],
            "tipoEvento": str(injury_state.value),
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

            sleep(self.sleep_time)

        return ids

    def create_new_dataframe(self):
        self.ids_dataframe = pd.DataFrame(columns=["id", "StatoInfortunio", "Locazione", "Settore"])

    def scrape_injuries_ids(self):
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
        print("Inizio scraping degli IDs...")
        for types in itertools.product([si for si in StatoInfortunio],
                                       [lo for lo in Locazione],
                                       [s for s in Settore]):

            if types in self.already_retrieved_combinations:
                continue

            ids = self.retrieve_filtered_ids(injury_state=types[0],
                                             location=types[1],
                                             sector=types[2])

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
            print(
                'Ids per {} - {} - {} aggiunti correttamente.'.format(types[0].name, types[1].name, types[2].name)
            )
        print("Tutti gli IDs sono stati salvati.")

    def scrape_injuries_details(self):
        print("Scarico le informazioni dei casi trovati...")
        # Genera lo schema se non presente
        Base.metadata.create_all(engine)

        # Recuperiamo gli ID degli infortuni contenuti nel database.
        s = Session()
        db_injury_ids = list(map(lambda x: int(x.id), list(s.query(Infortunio.id))))
        s.close()

        for index, row in self.ids_dataframe.iterrows():
            if row["id"] not in db_injury_ids:
                try:
                    s = Session()
                    infortunio = self.retrieve_injury_details(
                        injury_id=row["id"],
                        location=Locazione[row["Locazione"]],
                        sector=Settore[row["Settore"]]
                    )
                    s.add(infortunio)
                    s.commit()
                    s.close()
                    print('ID - {} scaricato correttamente.'.format(row["id"]))
                except IntegrityError as e:
                    # Idealmente questo errore viene generato quando proviamo ad inserire un ID già esistente.
                    # Ma, per come è eseguita la procedura, non dovrebbe venire chiamata.
                    logging.debug('Errore: {}', e)

    print("Recupero dei dati eseguito correttamente.")

    def retrieve_injury_details(self,
                                injury_id,
                                location: Locazione,
                                sector: Settore):
        """
        Metodo che apre la pagina dell'infortunio specificata da injury_id.
        Questa parte è necessaria per recuperare la descrizione completa,
        più gli ID relativi ai fattori. Con questi ID possiamo poi procedere
        ad eseguire le richieste POST per ottenere i JSON specifici sui
        fattori e sul dettaglio dell'infortunio.
        """

        # Apriamo la pagina corrispondente all'infortunio
        page_response = requests.get(self.injury_page_url + str(injury_id))
        page = BeautifulSoup(page_response.text, 'lxml')

        # Recuperiamo il JSON relativo ai dettagli dell'infortunio.
        # Il JSON è composto da vari JSON Objects, nella quale gran parte dei valori
        # sono ripetuti (Guardare l'esempio in assets).
        injury_details_response = requests.post(self.injury_json_url, str(injury_id))
        injury_details_response = injury_details_response.json()
        sleep(self.sleep_time)

        # Recuperiamo i tag h3 relativi alle sezioni "Descrizione della dinamica e dei relativi fattori".
        # Prendendo uno di questi tag e navigando al suo genitore, otterremo la div che contiene tutti i fattori
        # relativi ad un singolo lavoratore.
        factors_h3 = page.find_all("h3", string=self.title_before_description_injury_page)

        accidents = []

        for (h3, o) in zip(factors_h3, injury_details_response):
            incident_description = h3.find_next_sibling().get_text().strip()

            factors_ids = [tag.get("onclick")[:-1].replace("apriDettagliFattore(", "") for tag in
                           h3.parent.find_all("button", {"onclick": re.compile("apriDettagliFattore\([0-9]{1,6}\)")})]
            factors = []
            for f_id in factors_ids:
                factors.append(self.retrieve_factor(f_id))
                sleep(self.sleep_time)

            worker = Lavoratore(
                sesso=o.get("sesso"),
                nazionalita=o.get("cittadinanza"),
                tipo_contratto=o.get("rapLav"),
                mansione=o.get("mansione"),
                anzianita=o.get("anzianita"),
                numero_addetti_azienda=parse_int(o.get("numAddetti")),
                attivita_prevalente_azienda=o.get("attPrev"),

            )

            # Lo stato dell'infortunio (Grave o Mortale) lo ricaviamo dai giorni di assenza: per convenzione, se il
            # i numero di giorni non è specificato, l'incidente è Mortale. Altrimenti, è Grave.
            accidents.append(Incidente(
                id=o.get("codiceInfortunato"),
                lavoratore=worker,
                fattori=factors,
                stato_infortunio=get_injury_state(o.get("numeroGiorniAssenza")),
                descrizione_della_dinamica=incident_description,
                luogo_infortunio=o.get("luogo"),
                attivita_lavoratore_durante_infortunio=o.get("tipoAtt"),
                ambiente=o.get("agente"),
                tipo_incidente=type_incident(o.get("variazEnergia")),
                descrizione_incidente=o.get("incidente"),
                agente_materiale=o.get("agenteMatInc"),
                sede_lesione=o.get("sedeLesione"),
                natura_lesione=o.get("naturaLesione"),
                giorni_assenza_lavoro=parse_int(o.get("numeroGiorniAssenza")),
            ))

        return Infortunio(
            id=injury_id,
            settore_attivita=Settore(sector),
            locazione=Locazione(location),
            data=parse_date(injury_details_response[0].get("dataInfortunio")),
            ora_ordinale=parse_int(injury_details_response[0].get("oraLavoro")),
            incidenti=accidents
        )

    def retrieve_factor(self, factor_id):
        response = requests.post(self.factor_json_url, factor_id)
        response = response.json()
        return Fattore(
            fattore_id=response.get("codiceFattore"),
            descrizione=response.get("descrizioneFattore"),
            tipologia=response.get("tipoFattore"),
            determinante_modulatore=DeterminanteModulatore[response.get("detMod")],
            tipo_modulazione=response.get("tipoMod"),
            problema_sicurezza=response.get("descrizioneProblSic"),
            confronto_standard=response.get("confrontoStand"),
            valutazione_rischi=response.get("valRisc"),
            stato_processo=StatoProcesso[response.get("statoProc")],
            classificazione=response.get("classificazione")
        )
