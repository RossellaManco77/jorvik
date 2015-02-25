"""
Questo modulo definisce i modelli del modulo anagrafico di Gaia.

- Persona
- Telefono
- Documento
- Utente
- Appartenenza
- Comitato
- Delega
"""

from base.modelli import *
from base.stringhe import normalizza_nome, generatore_nome_file
from base.tratti import *
from base.stringa import *
import phonenumbers


class Persona(ModelloCancellabile, ConGeolocalizzazioneRaggio):
    """
    Rappresenta un record anagrafico in Gaia.
    """

    # Genere
    MASCHIO = 'M'
    FEMMINA = 'F'
    GENERE = (
        (MASCHIO, 'Maschio'),
        (FEMMINA, 'Femmina')
    )

    # Stati
    PERSONA = 'P'
    ASPIRANTE = 'A'
    VOLONTARIO = 'V'
    DIPENDENTE = 'D'
    MILITARE = 'M'
    STATO = (
        (PERSONA,       'Persona'),
        (ASPIRANTE,     'Aspirante'),
        (VOLONTARIO,    'Volontario'),
        (DIPENDENTE,    'Dipendente'),
        (MILITARE,      'Militare'),
    )

    # Informazioni anagrafiche
    nome = models.CharField("Nome", max_length=64)
    cognome = models.CharField("Cognome", max_length=64)
    codice_fiscale = models.CharField("Codice Fiscale", max_length=16, blank=False, unique=True, db_index=True)
    data_nascita = models.DateField("Data di nascita", db_index=True)
    genere = models.CharField("Genere", max_length=1, choices=GENERE, db_index=True)

    # Stato
    stato = models.CharField("Stato", max_length=1, choices=STATO, db_index=True)

    # Informazioni anagrafiche aggiuntive - OPZIONALI (blank=True o default=..)
    comune_nascita = models.CharField("Comune di Nascita", max_length=64, blank=True)
    provincia_nascita = models.CharField("Provincia di Nascita", max_length=2, blank=True)
    stato_nascita = models.CharField("Stato di nascita", max_length=2, default="IT")
    indirizzo_residenza = models.CharField("Indirizzo di residenza", max_length=64, blank=True)
    comune_residenza = models.CharField("Comune di residenza", max_length=64, blank=True)
    provincia_residenza = models.CharField("Provincia di residenza", max_length=2, blank=True)
    stato_residenza = models.CharField("Stato di residenza", max_length=2, default="IT")
    cap_residenza = models.CharField("CAP di Residenza", max_lenght=5, blank=True)
    email_contatto = models.CharField("Email di contatto", max_length=64, blank=True)

    def nome_completo(self):
        """
        Restituisce il nome e cognome
        :return: "Nome Cognome".
        """
        return normalizza_nome(self.nome + " " + self.cognome)

    # Q: Qual e' l'email di questa persona?
    # A: Una persona puo' avere da zero a due indirizzi email.
    #    - Persona.email_contatto e' quella scelta dalla persona per il contatto.
    #    - Persona.utenza.email (o Persona.email_utenza) e' quella utilizzata per accedere al sistema.
    #    - Persona.email puo' essere usato per ottenere, in ordine, l'email di contatto,
    #       oppure, se non impostata, quella di utenza. Se nemmeno una utenza e' disponibile,
    #       viene ritornato None.

    @property
    def email(self):
        """
        Restituisce l'email preferita dalla persona.
        Se impostata, restituisce l'email di contatto, altrimento l'email di utenza.
        :return:
        """
        if self.email_contatto:
            return self.email_contatto
        self.email_utenza

    @property
    def email_utenza(self):
        """
        Restituisce l'email dell'utenza, se presente.
        :return: Email o None
        """
        if self.utenza:
            return self.utenza.email
        return None

    def __str__(self):
        return self.nome_completo()

    class Meta:
        verbose_name_plural = "Persone"

    # Q: Qual e' il numero di telefono di questa persona?
    # A: Una persona puo' avere da zero ad illimitati numeri di telefono.
    #    - Persona.numeri_telefono ottiene l'elenco di oggetti Telefono.
    #    - Per avere un elenco di numeri di telefono formattati, usare ad esempio
    #       numeri = [str(x) for x in Persona.numeri_telefono]
    #    - Usare Persona.aggiungi_numero_telefono per aggiungere un numero di telefono.

    def aggiungi_numero_telefono(self, numero, servizio=False, paese="IT"):
        """
        Aggiunge un numero di telefono per la persona.
        :param numero: Il numero di telefono.
        :param servizio: Vero se il numero e' di servizio. Default False.
        :param paese: Suggerimento per il paese. Default "IT".
        :return: True se l'inserimento funziona, False se il numero e' mal formattato.
        """
        try:
            n = phonenumbers.parse(numero, paese)
        except phonenumbers.phonenumberutil.NumberParseException:
            return False
        f = phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)
        t = Telefono(persona=self, numero=f, servizio=servizio)
        t.save()
        return True


class Telefono(ModelloSemplice, ConMarcaTemporale):
    """
    Rappresenta un numero di telefono.
    NON USARE DIRETTAMENTE. Usare i metodi in Persona.
    """

    persona = models.ForeignKey(Persona, related_name="numeri_telefono")
    numero = models.CharField("Numero di telefono", max_length=16)
    servizio = models.BooleanField("Numero di servizio", default=False)

    class Meta:
        verbose_name = "Numero di telefono"
        verbose_name_plural = "Numeri di telefono"

    def _phonenumber(self):
        return phonenumbers.parse(self.numero)

    def __str__(self):
        """
        Ritorna il numero per la visualizzazione nel formato appropriato (Italiano o Internazionale)
        :return: Stringa che rappresenta il numero di telefono.
        """
        n = self._phonenumber()
        if n.country_code == 39:
            return self.nazionale()
        else:
            return self.internazionale()

    def nazionale(self):
        """
        Ritorna il numero formattato come numero nazionale.
        :return: Stringa che rappresenta il numero in formato nazionale.
        """
        return phonenumbers.format_number(self._phonenumber(), phonenumbers.PhoneNumberFormat.NATIONAL)

    def internazionale(self):
        """
        Ritorna il numero formattato come numero internazionale.
        :return: Stringa che rappresenta il numero in formato internazionale.
        """
        return phonenumbers.format_number(self._phonenumber(), phonenumbers.PhoneNumberFormat.INTERNATIONAL)

    def e164(self):
        """
        Ritorna il numero formattato come numero internazionale E.164.
        :return: Stringa che rappresenta il numero in formato internazionale E.164.
        """
        return phonenumbers.format_number(self._phonenumber(), phonenumbers.PhoneNumberFormat.E164)


class Documento(ModelloSemplice, ConMarcaTemporale):
    """
    Rappresenta un documento caricato da un utente.
    """

    # Tipologie di documento caricabili
    CARTA_IDENTITA = 'I'
    PATENTE_CIVILE = 'P'
    PATENTE_CRI = 'S'
    CODICE_FISCALE = 'C'
    TIPO = (
        (CARTA_IDENTITA, 'Carta d\'identità'),
        (PATENTE_CIVILE, 'Patente Civile'),
        (PATENTE_CRI, 'Patente CRI'),
        (CODICE_FISCALE, 'Codice Fiscale')
    )

    persona = models.ForeignKey(Persona, related_name="documenti", db_index=True)
    file = models.FileField("File", upload_to=generatore_nome_file('documenti/'))

    class Meta:
        verbose_name_plural = "Documenti"


class Utenza(ModelloSemplice):

    class Meta:
        verbose_name_plural = "Utenze"


class Appartenenza(ModelloSemplice, ConMarcaTemporale, ConAutorizzazioni):

    class Meta:
        verbose_name_plural = "Appartenenze"


class Comitato(ModelloAlbero, ConGeolocalizzazione):

    # Nome gia' presente in Modello Albero

    # Estensione del Comitato
    TERRITORIALE = 'T'
    LOCALE = 'L'
    PROVINCIALE = 'P'
    REGIONALE = 'R'
    NAZIONALE = 'N'
    ESTENSIONE = (
        (TERRITORIALE, 'Unità Territoriale'),
        (LOCALE, 'Comitato Locale'),
        (PROVINCIALE, 'Comitato Provinciale'),
        (REGIONALE, 'Comitato Regionale'),
        (NAZIONALE, 'Comitato Nazioanle')
    )

    # Tipologia del comitato
    COMITATO = 'C'
    MILITARE = 'M'
    TIPO = (
        (COMITATO, 'Comitato'),
        (MILITARE, 'Sede Militare'),
    )

    estensione = models.CharField("Estensione", max_length=1, choices=ESTENSIONE, db_index=True)
    tipo = models.CharField("Tipologia", max_length=1, choices=TIPO, default=COMITATO, db_index=True)

    # Dati del comitato
    # Nota: indirizzo e' gia' dentro per via di ConGeolocalizzazione
    via = models.CharField("Via", max_length=64, blank=True)
    civico = models.CharField("Civico", max_length=8, blank=True)
    comune = models.CharField("Comune", max_length=64, blank=True)
    provincia = models.CharField("Provincia", max_length=64, blank=True)
    cap = models.CharField("CAP", max_length=5, blank=True)
    telefono = models.CharField("Telefono", max_length=64, blank=True)
    fax = models.CharField("FAX", max_length=64, blank=True)
    email = models.CharField("Indirizzo e-mail", max_length=64, blank=True)
    codice_fiscale = models.CharField("Codice Fiscale", max_length=32, blank=True)
    partita_iva = models.CharField("Partita IVA", max_length=32, blank=True)

    # Q: Come ottengo i dati del comitato?
    # A: Usa la funzione Comitato.ottieni, ad esempio, Comitato.ottieni('partita_iva').
    #    Questa funzione cerca la prima partita IVA disponibile a "Salire" l'albero.

    def ottieni(self, nome_campo):
        """
        Questa funzione dovrebbe essere usata per ottenere i campi di un comitato.
        Se il campo non e' definito, risale l'albero per ottenerlo.
        :param nome_campo: Nome del campo, es. "codice_fiscale", "partita_iva", ecc.
        :return: Il primo valore disponibile o None se non trovato.
        """
        attuale = self
        while True:
            if attuale.__getattribute__(nome_campo):
                return attuale.__getattribute__(nome_campo)
            if attuale.genitore is None:
                return None
            attuale = attuale.genitore

    class Meta:
        verbose_name_plural = "Comitati"


class Delega(ModelloSemplice, ConMarcaTemporale):

    class Meta:
        verbose_name_plural = "Deleghe"
