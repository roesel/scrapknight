## minimální TODO
 * *"Udělat dobře jedno UI na jeden účel."*
 * Search
   * indikátor je/není v knihovně
   * kolikrát už v decku karta je
   * odstranit Accept Selection
   * rovnou specific search parameters
   * odstranit výčet knihovny (Library sekce)
 * Deckbox
   * smazat čudlík
   * Accept Selection by mělo "acceptnout"
   * tlačítko "objednat karty co nemám"
   * tlačítko "naproxit karty co nemám" (http://www.mtgpress.net/faq) - to by mělo být super jednoduché
 * Pozadí / DB
   * Vytvořit nějaký "patch" na ruční dofixování toho co direct_match a image_match nezvládnou.
     * Jak to přesně udělat?
     * Nějak chytře, tak aby to věděl link.py script a uměl říct "máme 100 %"
   * ~ DONE mít dokonale načtené všechny karty ze **standard** edic
     * KLI/MPS není na rytíři celá (jen něco málo přes půlku)
     * Není zkontrolováno, jestli jsou opravdu nalinkované všechny.
   * dtto **modern** edice
     * BOK, CHK - problémy s flip kartami, v řešení s tvůrcem API přes github
     * DIS, TSB, PLC - problémy s dual-kartami jako Hit // Run - prodiskutovat nejlepší řešení?
       * nová tabulka na "merged" karty?
     * ZEN - problémy s nekonzistencí rytíře
       * dalo by se ručně namatchovat, ale už tak řešíme jeden problém, možná kontaktovat rytíře?


*(Není tu všechno co jsme probírali, jen to co je opravdu potřeba udělat.)*

## TODO
 * rozhodnout se jak naplňovat databázi
 * zkopírovat "update_time" do Connectoru
 * opravit problémy s foreign keys a views
 * přesunout a rozházet věci z tools.py do libs/
 * +- čudlíky vertikálně kompaktní
 * onchange -- updatovat celkovou cenu multikarty
 * čudlík -- potvrdit podvýběr multikarty
 * čudlík -- najít alternativy dané karty napříč edicemi
 * stejná karta na dvou řádcích -- hodit ji do outputu 2x
 * čudlík "use export list"
 * u multikarty zobrazit prvních x a pak "show more"
 * persistent scrolling -- náhled, input?
 * share -- ukládat link na list do databáze (?)
 * proxy generátor
 * account (databáze karet, decků, ...)
 * trading system
 * DONE opravit, že Scraper v KLI nenajde žádné karty, protože není vícestránková
 * DONE cachování náhledů karet
 * DONE propojení s nějakým mtg api
 * DONE rozdělit build na Bulider, Scraper a Connector
 * DONE přesunout databázový funkce do Database objektu a hlavně zařídit aby vracel selhání
 * DONE vyčistit/okomentovat před pokračováním sdk.py a spol
