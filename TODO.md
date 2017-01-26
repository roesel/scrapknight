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
 * Pozadí / DB
   * mít dokonale načtené všechny karty ze **standard** edic
   * dtto **modern** edice

*(Není tu všechno co jsme probírali, jen to co je opravdu potřeba udělat.)*

## TODO
 * rozhodnout se jak naplňovat databázi
 * zkopírovat "update_time" do Connectoru
 * opravit, že Scraper v KLI nenajde žádné karty, protože není vícestránková
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
 * cachování náhledů karet
 * propojení s nějakým mtg api
 * rozdělit build na Bulider, Scraper a Connector
 * přesunout databázový funkce do Database objektu a hlavně zařídit aby vracel selhání !!
 * vyčistit/okomentovat před pokračováním sdk.py a spol
