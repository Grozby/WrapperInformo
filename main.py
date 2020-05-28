from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from infortunio import StatoInfortunio, Localita, Settore
import itertools
import pandas as pd


class WrapperInformo:
    def __init__(self):
        # Basic settings wrapper
        self.no_browser = False
        self.timeout = 5
        self.initial_search_page_url = "https://www.inail.it/sol-informo/home.do?tipoEvento="
        self.details_page_url = "https://www.inail.it/sol-informo/dettaglio.do?codiceInfortunio="
        self.html_id_localita = "Localizzazioneterritoriale-"
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

    def retrieve_ids(self,
                     stato_infortunio: StatoInfortunio,
                     localita: Localita,
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
        self.driver.find_element_by_id(self.html_id_localita + str(localita.value)).click()
        self.driver.find_element_by_id(self.html_id_settore + str(settore.value)).click()

        # Manteniamo una lista di ID, riferiti agli infortuni con i filtri selezionati.
        ids = []
        last_page = False

        while not last_page:
            # Aspettiamo che il contenuto della pagina sia disponibile
            self.driver.find_elements_by_xpath("//table[@id='tabellaRisultatiId']/tbody/tr/td/a")
            page = BeautifulSoup(self.driver.page_source, 'lxml')
            table = page.select("#tabellaRisultatiId tbody tr")

            # Per ogni elemento nella tabella mostrata, salviamo l'ID del caso
            for row in table:
                ids.append(row.contents[0].contents[0].text)

            # Per controllare se abbiamo raggiunto l'ultima pagina, controlliamo che il bottone
            # "avanti" sia disabilitato
            last_page = page.select("#tabella-1_paginate ul")[0] \
                            .contents[2] \
                            .get('class') is "paginate_button disabled"

            # Se non è disabilitato...
            if not last_page:
                # Clicchiamo il bottone avanti
                self.driver.find_element_by_xpath("//div[@id='tabella-1_paginate']/ul/li[3]/a").click()
                # E aspettiamo che il contenuto della tabella non si aggiorni con la chiamata AJAX
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located((By.XPATH, "//a[contains(.," + ids[-1] + ")]"))
                )

        return ids

    def scrape_ids(self):
        """
        Per ogni combinazione di tipologia infortunio, Locazione e Settore,
        recuperiamo la lista ID degli infortuni.
        Aggingiamo anche la località perché nella pagina con i dettagli
        dell'infortunio non è presente la località dell'infortunio.


        """
        self.ids_dataframe = pd.DataFrame(columns=["id", "StatoInfortunio", "Località", "Settore"])

        for types in itertools.product([si for si in StatoInfortunio],
                                       [l for l in Localita],
                                       [s for s in Settore]):

            ids = self.retrieve_ids(stato_infortunio=types[0],
                                    localita=types[1],
                                    settore=types[2])

            # Ogni volta che finisce lo scraping per una determinata combinazione,
            # procediamo ad espandere il dataframe e salvare i dati.

            for i in ids:
                self.ids_dataframe = self.ids_dataframe.append({
                    "id": int(i),
                    "StatoInfortunio": types[0].name,
                    "Località": types[1].name,
                    "Settore": types[2].name
                })

            self.ids_dataframe.to_pickle(self.path_ids_pickle)
            self.ids_dataframe.to_csv(self.path_ids_csv, index=False)


def main():
    wrapper = WrapperInformo()

    try:
        wrapper.ids_dataframe = pd.read_pickle(wrapper.path_ids_pickle)
        # TODO: We are assuming that the dataframe is complete. May be not the case.
        # TODO: If not complete, resume scrape_id with the missing combinations.
    except FileNotFoundError:
        wrapper.scrape_ids()


if __name__ == "__main__":
    main()
