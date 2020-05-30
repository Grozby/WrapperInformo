import itertools
import logging
import re
import sys

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy.exc import IntegrityError

from entities.base import Base, engine, Session
from entities.fattore import Fattore
from entities.infortunio import Infortunio
from entities.enums.stato_infortunio import StatoInfortunio
from entities.enums.settore import Settore
from entities.enums.locazione import Locazione
from entities.lavoratore import Lavoratore
from utils import parse_int, parse_date, sleep
from selenium.webdriver.common.action_chains import ActionChains


class WrapperInformoSelenium:
    def __init__(self):
        # Basic settings wrapper
        self.no_browser = False
        self.timeout = 5
        self.sleep_between_requests: float = 0.2
        self.initial_search_page_url = "https://www.inail.it/sol-informo/home.do?tipoEvento="
        self.injury_page_url = "https://www.inail.it/sol-informo/dettaglio.do?codiceInfortunio="
        self.factor_json_url = "https://www.inail.it/sol-informo/dettaglioFattore.do"
        self.injury_json_url = "https://www.inail.it/sol-informo/dettagliInfortunio.do"
        self.title_before_description_injury_page = "Descrizione della dinamica e dei relativi fattori"
        self.html_id_locazione = "Localizzazioneterritoriale-"
        self.html_id_settore = "Settore_Attività-"

        # Path of ids
        self.path_ids_pickle = "./assets/dataframe_ids.pkl"
        self.path_ids_csv = "./assets/dataframe_ids.csv"

        # Defining the options for selenium
        options = webdriver.ChromeOptions()
        if self.no_browser:
            options.add_argument('--headless')

        self.driver = webdriver.Chrome("./assets/chromedriver.exe", options=options)

        if isinstance(self.timeout, int) and self.timeout > 0:
            self.driver.implicitly_wait(self.timeout)

        self.ids_dataframe = None
        self.already_retrieved_combinations = []

    def retrieve_filtered_ids(self,
                              stato_infortunio: StatoInfortunio,
                              locazione: Locazione,
                              settore: Settore):
        """
        Funzione usata per recuperare inizialmente gli id dei casi. Saranno raccolti gli id
        rispetto a:
            1) StatoInfortunio: Grave, Mortale.
            2) Località: NordOvest, NordEst, Centro, Sud e Isole.
            3) Settore: Metallurgia, FabbricazioneMacchine

        La funzione, se conclusa con successo, ritorerà un array di stringhe corrispondenti agli id.
        """
        # Si inizia caricando la pagina.
        self.driver.get(self.initial_search_page_url + str(stato_infortunio.value))
        # Appena caricata, selezioniamo i parametri con cui filtrare la ricerca

        self.driver.find_element_by_id(self.html_id_settore + str(settore.value)).click()
        sleep(0.1)
        action = ActionChains(self.driver)
        action.click(self.driver.find_element_by_id(self.html_id_locazione + str(locazione.value))).perform()
        self.driver.execute_script('$( document ).ajaxStop(function() { $( "#tabellaRisultatiId" ).addClass("loaded"); } );')

        # Aspettiamo che il contenuto della pagina sia disponibile. Per capire quando il contenuto sia disponibile
        # andiamo a vedere quando la sezione dei filtri viene nascosta.
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table[@class='table display tabella-base col-md-12 loaded']"))
        )

        # Manteniamo una lista di ID, riferiti agli infortuni con i filtri selezionati.
        ids = []
        last_page = False

        while not last_page:
            page = BeautifulSoup(self.driver.page_source, 'lxml')
            table = page.select("#tabellaRisultatiId tbody tr")

            # Per ogni elemento nella tabella mostrata, salviamo l'ID del caso
            for row in table:
                ids.append(row.contents[0].contents[0].text)
                if int(row.contents[0].contents[0].text) in self.ids_dataframe["id"].unique():
                    print()

            # Per controllare se abbiamo raggiunto l'ultima pagina, controlliamo che il bottone
            # "avanti" esista e che sia disabilitato
            directional_arrows_ul = page.select("#tabella-1_paginate ul")[0]
            last_page = not directional_arrows_ul.contents or \
                        "disabled" in directional_arrows_ul.contents[2].get('class')

            # Se "avanti" è abilitato...
            if not last_page:
                # Clicchiamo il bottone avanti
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@id='tabella-1_paginate']/ul/li[3]/a"))
                )
                sleep(0.25)
                self.driver.find_element_by_xpath("//div[@id='tabella-1_paginate']/ul/li[3]/a").click()
                # E aspettiamo che il contenuto della tabella si aggiorni con la chiamata AJAX
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located((By.XPATH, "//a[contains(.," + ids[-1] + ")]"))
                )

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
                if int(i) in self.ids_dataframe["id"].unique():
                    print()
                self.ids_dataframe = self.ids_dataframe.append({
                    "id": int(i),
                    "StatoInfortunio": types[0].name,
                    "Locazione": types[1].name,
                    "Settore": types[2].name
                }, ignore_index=True)

            self.ids_dataframe.to_pickle(self.path_ids_pickle)
            self.ids_dataframe.to_csv(self.path_ids_csv, index=False)
            logging.debug(
                'Ids per {} - {} - {} aggiunti correttamente.'.format(types[0].name, types[1].name, types[2].name))

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
        self.driver.get(self.injury_page_url + str(injury_id))
        page = BeautifulSoup(self.driver.page_source, 'lxml')

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

    def dispose(self):
        self.driver.quit()
