# GUIDA COMPLETA AL PROGETTO E TUTORIAL DEL SITO (SPIEGATO DA ZERO)
## AI Assisted Software Architecting Council — Corso di Software Architecture 2026/27

> **PER CHI È QUESTA GUIDA?**  
> Questa guida è pensata per chi **parte completamente da zero** (anche se non hai seguito le lezioni del corso di Software Architecture) e vuole capire **alla lettera** ogni singola parola, ogni singolo file del progetto, ogni bottone del sito web e **cosa rispondere alle domande del Prof. Muccini all'esame**.

---

# PARTE 0: Il "Dizionario di Sopravvivenza" (Le parole del corso spiegate semplici)

Prima di vedere il progetto, impariamo le **8 parole chiave** che il prof usa sempre nelle slide. Se capisci queste 8 parole, hai già capito metà esame:

1. **Software Architecture (Architettura del Software)**:
   - *Cos'è*: È la "piantina" di un sistema informatico, proprio come il progetto di un palazzo fatto da un architetto edile. Decide quali pezzi usare (database, server, sistemi di messaggistica) e come farli parlare tra loro.
2. **Quality Attributes / Decision Drivers (Attributi di Qualità — Norma ISO/IEC 25010)**:
   - *Cosa sono*: Sono le "qualità" che il sistema deve avere, definite da uno standard internazionale chiamato **ISO/IEC 25010**. I più importanti sono:
     - **Performance / Latency (Velocità)**: Il sistema deve rispondere subito (es. in meno di 1 secondo).
     - **Reliability / Availability (Affidabilità)**: Il sistema non deve mai cadere o perdere dati, neanche se salta la corrente o internet.
     - **Security (Sicurezza)**: Solo chi è autorizzato può entrare e nessuno può manomettere i dati.
     - **Maintainability / Operability (Facilità di Gestione)**: Quanto è facile per i programmatori mantenere acceso e aggiornare il sistema. Se hai solo 3 tecnici in azienda, non puoi scegliere un sistema complicatissimo che richiede 20 persone per funzionare!
3. **Trade-off (Compromesso)**:
   - *Cos'è*: È la regola base del corso: **non esiste la tecnologia perfetta**. Ogni scelta ha un prezzo (la "coperta corta"): se scegli una tecnologia super potente (alta *Performance*), spesso è difficilissima da gestire (bassa *Operability*) o costa tantissimo. Fare l'architetto significa scegliere il compromesso migliore.
4. **Pattern Architetturale (Soluzione Standard)**:
   - *Cos'è*: È una ricetta già pronta per risolvere un problema tipico. Esempi presenti nel nostro progetto:
     - **Monolite Modulare vs Microservizi**: Fare un unico programma ben ordinato (ottimo per team piccoli) oppure spezzarlo in 20 mini-programmi separati (ottimo se hai 150 programmatori, un incubo se siete in 4).
     - **Apache Kafka vs NATS JetStream**: Due postini che smistano messaggi velocissimi. *Kafka* è un gigante potentissimo ma pesante da gestire; *NATS JetStream* è un singolo file leggerissimo perfetto per piccoli team.
5. **ADR (Architecture Decision Record) e Standard MADR**:
   - *Cos'è*: È il "verbale ufficiale" di una decisione. Quando gli architetti scelgono una tecnologia, compilano una scheda chiamata **ADR** (nel formato standard **MADR**) dove scrivono:
     1. Qual era il problema e quali erano i **Decision Drivers** (es. velocità + team piccolo);
     2. Quali opzioni hanno valutato (**Considered Options**) con i **Pro (`pros`)** e i **Contro (`cons`)** di ciascuna (anche di quelle bocciate!);
     3. Quale opzione ha vinto (**Chosen Option**) e perché;
     4. Chi non era d'accordo e perché (**Minority Dissent**).
6. **LLM (Large Language Model)**:
   - *Cos'è*: È il "cervello" di intelligenza artificiale (come ChatGPT di OpenAI, Gemini di Google, Qwen di Alibaba, Llama di Meta).
7. **Sycophancy (Conformismo / "Effetto Yes-Man" delle AI)**:
   - *Cos'è*: I modelli AI hanno il difetto di dare sempre ragione a chi parla per primo. Se metti 4 AI in una chat e la prima dice una sciocchezza, le altre 3 le dicono *"Ottima idea!"*. Per evitare questo, nel nostro progetto le obblighiamo a **pensare prima da sole in stanze separate** senza sbirciare!
8. **RAG / Grounding (Knowledge Base con Citazioni)**:
   - *Cos'è*: Le AI a volte inventano le cose (*allucinazioni*). Per impedirlo, diamo agli agenti una "biblioteca" di 18 manuali ufficiali (la nostra **Knowledge Base**). Ogni volta che un agente apre bocca, è **obbligato a citare il codice del manuale** (es. `[KB-PAT-01]`, `[KB-ISO-04]`) da cui ha preso la prova!

---

# PARTE 1: Cosa chiede il Prof nella Traccia?

Immagina che **Micron** (l'azienda di microchip che collabora col prof) debba progettare un sistema per raccogliere gli allarmi da **5.000 macchinari della fabbrica**, tenendo tutti i dati **dentro la fabbrica (`on-prem`)**, in **meno di 1 secondo (`<1s latency`)**, ma avendo **solo 3 tecnici (`small ops team`)** per gestirlo.

* **Se lo chiedi a una sola AI (Baseline)**: Quella ti spara subito *"Usa Apache Kafka!"* perché su internet tutti parlano di Kafka, ignorando che 3 poveri tecnici impazzirebbero a gestire un cluster Kafka.
* **Cosa vuole il Prof**: Costruire un **Consiglio di Agenti AI (Architect Council)** formato da più modelli AI diversi che:
  1. Hanno caratteri opposti (chi bada alla semplicità, chi alla sicurezza, chi all'innovazione, chi è scettico);
  2. Prima fanno una proposta in segreto, poi litigano portando le prove dei manuali (`Knowledge Base`), e infine votano;
  3. Ascoltano le correzioni dell'**Architetto Umano** e **imparano** dai suoi gusti per le decisioni future.

---

# PARTE 2: Come Funziona il Nostro Sistema (Tutti i Passaggi e le Novità Scientifiche)

Qui sotto ti spiego passo per passo **cosa succede dentro il nostro codice** e **perché** è stato scritto così, includendo tutte le migliorie dei paper scientifici del prof (*Muccini, Díaz-Pace, Gupta, Miccio, Nishio 2026*).

---

## PASSO 1: I 4 Agenti Architetti + Il Presidente (`backend/config.py` e `backend/agents.py`)
* **Quale regola della traccia risolve**: **Pilastro 1 (Slide 5 e 6)** — *"Almeno 3 famiglie di LLM diverse + caratteri (Stance) diversi, ma stesso mandato da architetto completo"*.
* **Come funziona in pratica**:
  Abbiamo creato una "sala riunioni virtuale" con **4 Architetti alla pari (Peer Architects)** più **1 Presidente (Chair)**:
  1. ⚙️ **Pragmatist (`agent_pragmatist`)** → Cervello: *OpenAI GPT-OSS 120B*. **Carattere**: Vuole cose semplici, veloci da fare e facili da gestire per piccoli team.
  2. 🛡️ **Guardian (`agent_guardian`)** → Cervello: *Google Gemini 2.5 Flash / ALLaM-2*. **Carattere**: Prudente, fissato con la sicurezza, zero perdita di dati e tecnologie collaudate.
  3. 🚀 **Innovator (`agent_innovator`)** → Cervello: *Alibaba Qwen 3.8 27B*. **Carattere**: Visionario, vuole sistemi modernissimi capaci di reggere carichi enormi in futuro.
  4. 🧐 **Skeptic (`agent_skeptic`)** → Cervello: *GPT-OSS 20B / Mistral*. **Carattere**: Lo scettico che fa le pulci a tutti, smonta le mode costose e chiede le prove.
  5. ⚖️ **Chair Agent (`agent_chair`)** → **Ruolo**: Il Presidente neutrale che dirige il dibattito, controlla che nessuno violi le regole e scrive il documento finale ADR.

---

## PASSO 2: La "Biblioteca" Intelligente con Filtri Select/Reject (`data/knowledge_items.json` e `backend/knowledge_base.py`)
* **Quale regola risolve**: **Slide 9 (Grounding)** + Paper scientifico di *Nishio, Washizaki, Muccini et al. (2026) sui "Decision Layers"*.
* **Come funziona (spiegato semplicissimo)**:
  Nel file [`data/knowledge_items.json`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/data/knowledge_items.json) abbiamo inserito **18 schede tecniche ufficiali** (`KB-ISO-01..04`, `KB-PAT-01..08`, `KB-TAC-01..04`, `KB-ADR-01..02`).
  **LA NOVITÀ SCIENTIFICA (Check 1)**: Ogni scheda non è un semplice testo, ma è strutturata come il **foglietto illustrativo di una medicina**:
  - `problem`: Quale problema risolve;
  - `decision_drivers`: Quali qualità ISO 25010 tocca;
  - `selection_conditions` (**"Select when" — Scegli quando...**): es. *"Scegli NATS JetStream quando hai un `small-team` e sei `on-prem`"* → Dà un **bonus di +4.0 punti** a quella scheda!
  - `rejection_conditions` (**"Reject when" — Scarta quando...**): es. *"Scarta i Microservizi o Kafka se hai un `small-team` senza tecnici SRE"* → Dà una **penalità di -5.0 punti**!
  In questo modo il nostro motore di ricerca ([`backend/knowledge_base.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/knowledge_base.py)) seleziona automaticamente le prove giuste e scarta quelle incompatibili con i vincoli del problema!

---

## PASSO 3: Il Dibattito in 5 Fasi + Il "Buttafuori" Finale (`backend/orchestrator.py`)
* **Quale regola risolve**: **Pilastro 2 (Slide 7 e 8)** + Paper *ArchMind / AgenticAKM (2026)*.
* **Cosa succede esattamente quando clicchi "Start Council Debate"**:

  1. **FASE 1 — `FRAME` (Il Presidente apre la riunione)**:
     Il Chair legge il problema, estrae dalla Knowledge Base le schede più adatte e dalla Memoria i consigli passati dell'umano, e li distribuisce sul tavolo.
  2. **FASE 2 — `PROPOSE` (Proposta Segreta e Parallela — "No Peeking")**:
     I 4 agenti vengono interrogati **contemporaneamente in parallelo (`asyncio.gather`) e in stanze separate**. Nessuno può leggere cosa scrivono gli altri 3! Così il *Pragmatist* propone ad esempio NATS, mentre l'*Innovator* propone Kafka, creando un vero scontro di idee.
  3. **FASE 3 — `CRITIQUE & REVISE` (Scontro e Cambio di Idea)**:
     Si aprono le porte: ogni agente legge le proposte dei 3 colleghi.
     - Adesso devono **criticarsi a vicenda** citando i codici della Knowledge Base (es. *"Caro Innovator, la tua idea di usare Kafka viola il principio `[KB-ADR-01]` perché siamo solo in 3 tecnici!"*).
     - Se un agente viene convinto dalle prove di un collega, **cambia ufficialmente voto (`mind_changed = true`)** e scrive il motivo per cui ha cambiato idea (`change_reason`).
  4. **FASE 4 — `CONVERGE` (Votazione Pesata per Fiducia)**:
     Il Presidente raccoglie i voti finali. Ma attenzione: **i voti non valgono tutti 1!** Il voto di un agente che in passato si è dimostrato bravo e allineato con l'umano vale di più (grazie al suo `Trust Weight`, che può arrivare fino a `2.0x`), e chi cita più prove riceve un piccolo bonus.
  5. **IL CONTROLLO DEL "BUTTAFUORI" (`ADR Validation Gate` — Novità Check 4)**:
     Prima di pubblicare la decisione, il Chair fa un controllo automatico di sicurezza (`validate_adr_constraints`):
     - Controlla se per sbaglio l'opzione vincitrice viola un vincolo sacro (es. hanno scelto un servizio Cloud di Amazon quando il problema diceva obbligatoriamente `on-prem` dentro la fabbrica!).
     - Se trova una violazione, **blocca tutto**, sgrida gli agenti e gli fa rifare subito un giro di correzione automatico!
  6. **FASE 5 — `DECIDE` (Il Documento Finale MADR Completo — Novità Check 2)**:
     Superato il controllo, il Chair pubblica l'**ADR finale** secondo lo standard scientifico **MADR** (*Miccio, Tommasel, Díaz-Pace 2026*), che contiene obbligatoriamente:
     - I **Decision Drivers** (le qualità ISO 25010 e i vincoli);
     - L'analisi **Pro (`pros`) e Contro (`cons`) di TUTTE le opzioni**, sia quella che ha vinto (`✅ [CHOSEN]`), sia tutte quelle che sono state **bocciate (`❌ [REJECTED]`)**;
     - Il **Registro del Dissenso (`minority_dissent`)**: chi ha votato contro la maggioranza viene registrato con la sua spiegazione, così l'umano sa anche i rischi segnalati dalla minoranza!

---

## PASSO 4: Come il Sistema "Impara" dall'Umano (`backend/memory.py`)
* **Quale regola risolve**: **Pilastro 3 (Slide 10)** + Paper di *Gupta et al. (2026) "Context Matters"*.
* **I due cicli di Feedback**:
  1. **Short Loop (Correzione al volo nella riunione di oggi)**:
     Tu (l'umano) leggi l'ADR proposto ma vuoi aggiungere un dettaglio (es. *"Ragazzi, non sappiamo usare Java/JVM, cambiate scelta"*). Clicchi il bottone dello Short Loop, gli agenti leggono il tuo messaggio, ridiscutono subito e ti danno l'ADR corretto.
  2. **Long Loop (Insegnamento per tutte le riunioni del futuro)**:
     Quando confermi la tua decisione finale definitiva, il file [`backend/memory.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/memory.py) fa due cose:
     - **Premia gli agenti bravi (`Trust Weights`)**: Gli agenti che avevano votato come te guadagnano fiducia (`+0.12`), quelli che avevano votato male ne perdono un po' (`-0.05`).
     - **Salva una Regola d'Oro (`LEARNED-01`, `LEARNED-02`...)**: Trasforma la tua motivazione in una regola salvata nel file `data/memory_store.json`.
  3. **LA NOVITÀ SCIENTIFICA SULLA MEMORIA (`Last_K + RAFG` — Check 3)**:
     Quando in futuro farai la decisione numero 20, come facciamo a passare le regole passate agli agenti senza intasarli di testo? Seguendo il paper *Gupta et al. (2026)*, non passiamo tutta la storia intera (*All-History*, che confonde i modelli AI), ma usiamo una formula mista chiamata **`Last_K + RAFG`**:
     - **`Last_K` ($K=3$)**: Passiamo le **ultime 3 decisioni più recenti** fatte in ordine di tempo;
     - **`RAFG`**: Cerchiamo nell'archivio storico le **3 decisioni passate più simili per argomento** a quella di oggi.

---

## PASSO 5: I 24 Scenari e gli Esperimenti A e B (`backend/evaluator.py`)
* **Quale regola risolve**: **Slide 11 e 12** (Valutazione Sperimentale).
* **Come sono divisi i 24 scenari (`data/benchmark_scenarios.json`)**:
  - **12 Scenari di Allenamento (`feedback_set`, da `SCEN-01` a `SCEN-12`)**: Usati per dare il feedback al Consiglio e fargli imparare le 12 regole aziendali.
  - **12 Scenari di Esame (`held_out_test_set`, da `SCEN-13` a `SCEN-24`)**: Scenari "inediti", mai visti durante l'allenamento! Servono per dimostrare che il Consiglio ha **capito i concetti** e non ha semplicemente "imparato a memoria".
* **Le Metriche che calcoliamo (Check 5)**:
  - **Decision Accuracy (%)**: Quante volte indovina la scelta esatta dell'esperto umano.
  - **Weighted Quality Score (%)**: Dà 100% alla scelta perfetta e 50% alla seconda scelta accettabile.
  - **Decision Driver Coverage (%)**: Verifica se l'ADR finale ha discusso il **100%** degli attributi di qualità chiesti dal problema.
  - **KB Recall & Citations**: Quante prove ufficiali della Knowledge Base sono state citate.

---

# PARTE 3: Tutorial Semplicissimo del Sito Web (`http://127.0.0.1:8000`)

Ogni volta che apri **http://127.0.0.1:8000**, vedi in alto 5 bottoni che corrispondono alle **5 Schede (Tab)** del portale. Ecco cosa fa ogni singola cosa che vedi sullo schermo:

### 🟣 Barra in Alto (Sempre visibile)
- **`● A2A Bus Live (SSE)`**: Indica che il collegamento in diretta streaming col server Python è attivo.
- **`Learned Principles: X`**: Indica quante regole aziendali ha imparato finora il Consiglio grazie al tuo Long Loop.
- **`🎓 Defense Slides`**: Apre le **nostre slide di presentazione per l'esame** già pronte!
- **`📄 Prof. Slides`**: Apre le slide originali della traccia del Prof. Muccini.

---

### 🔹 SCHEDA 1: `1. Live Council Debate & ADR` (Dove fai parlare gli agenti)
- **A sinistra in alto (Scelta del problema)**:
  - Dal menu **`Load Benchmark Scenario`** puoi scegliere uno qualsiasi dei 24 casi di studio (il primo, `SCEN-01`, è proprio quello dei 5.000 macchinari della fabbrica Micron della Slide 3 del prof!).
  - **`Use Long-Loop Feedback Memory`**: Lasciala spuntata se vuoi che gli agenti usino le regole imparate; togli la spunta se vuoi vedere come ragionavano "da ignoranti" prima del tuo insegnamento.
  - **`Fast Deterministic Sim Mode`**:
    - **Senza spunta**: chiama davvero via internet i modelli su Groq e Google Gemini (ci mette circa 6-10 secondi).
    - **Con la spunta**: usa il simulatore veloce e risponde in meno di 1 secondo (utilissimo se all'esame non va il Wi-Fi!).
  - **Bottone viola `⚡ Start Council Debate`**: Fa partire le 5 fasi del dibattito!
  - **Bottone `vs. Single LLM`**: Fa rispondere i 4 modelli da soli (senza parlarsi) e ti mostra sotto una tabella per confrontarli col Consiglio.
- **A destra (Il Dibattito e il Verbale ADR)**:
  - In alto vedi i **5 rettangoli delle fasi** (`1. Frame` → `2. Propose` → `3. Critique & Revise` → `4. Converge` → `5. Decide`) che si illuminano.
  - Sotto scorrono i messaggi degli agenti. Nota nella fase `CRITIQUE` il bollino giallo **`🔄 Mind Changed`** quando un agente viene convinto dalle prove di un collega!
  - In fondo compare il grande riquadro verde dell'**ADR finale**, con:
    - Il bollino verde **`✓ Validation Gate Passed`** (che dimostra che il controllo automatico è stato superato);
    - I **Decision Drivers (ISO 25010)**;
    - L'elenco **`MADR Considered Options Analysis (Pros & Cons)`** con tutte le opzioni promosse (`✅ [CHOSEN]`) e bocciate (`❌ [REJECTED]`) coi rispettivi Pro e Contro;
    - I riquadri rossi del **`Minority View & Dissent Log`** (chi ha votato contro).
- **A sinistra in basso (I due bottoni del Feedback Umano)**:
  - **Short Loop**: Scrivi una frase nella casella (es. *"Non abbiamo esperienza con Kafka, preferiamo NATS"*) e premi **`💬 Send Short-Loop Critique`**: gli agenti fanno subito un altro giro e aggiornano l'ADR!
  - **Long Loop**: Scegli l'opzione definitiva dal menu a tendina e premi il bottone verde **`✅ Commit Final Decision & Teach Council`**: il sistema impara la regola per il futuro e premia gli agenti che avevano votato bene!

---

### 🔹 SCHEDA 2: `2. Swappable Agent Pool & A2A Trace` (Aggiungere agenti al volo)
- A destra vedi le 4 carte dei nostri agenti con la loro **barra di fiducia (`Trust Weight`)**.
- A sinistra hai il modulo **`➕ Hot-Swap / Add Peer Architect Agent`**: se clicchi **`💾 Hot-Swap / Add Agent to Council`**, aggiungi in tempo reale un **5° agente** (*FinOps Architect*) senza spegnere il server e senza toccare il codice! (Dimostra la regola *Swappable* della Slide 8).
- In basso a destra vedi il codice JSON tecnico di tutti i messaggi scambiati.

---

### 🔹 SCHEDA 3: `3. Grounding KB & Feedback Memory` (La Biblioteca e la Memoria)
- A sinistra vedi i **Pesi di Fiducia** aggiornati di ogni agente e tutte le **Regole Apprese (`[LEARNED-01]`, ...)** con il tasto `Reset Memory` per azzerarle.
- A destra vedi le **18 schede della Knowledge Base** (`[KB-ISO-01]`, `[KB-PAT-01]`, ecc.) che gli agenti usano per citare le fonti.

---

### 🔹 SCHEDA 4: `4. Evaluation Lab (Exp A & Exp B)` (I Grafici e i Numeri per il Prof)
- Clicca **`▶ Run Experiment A`**: dimostra in 1 secondo che sui 12 scenari di test il Consiglio completo fa **100.0%** di accuratezza mentre il miglior modello singolo da solo si ferma a **75.0%** (**+25.0%** per il Consiglio!).
- Clicca **`▶ Run Experiment B`**: dimostra la curva di apprendimento in 4 tappe (0, 4, 8 e 12 scenari di feedback), facendo vedere che l'accuratezza sui 12 scenari di test sale dal **66.7%** (prima del feedback) al **100.0%** (dopo il feedback, **+33.3%**!).

---

### 🔹 SCHEDA 5: `5. Architecture Doc & ADRs` (I Documenti di Progetto)
- Contiene questa guida, il documento di architettura `ARCHITECTURE.md`, il report `EVALUATION_REPORT.md` e i 5 ADR del nostro sistema (`ADR-001` .. `ADR-005`), pronti da mostrare al prof.

---

# PARTE 4: Le 6 Domande che il Prof vi farà all'Esame (con le Risposte Pronte!)

Impara queste 6 risposte e farai un figurone all'orale anche senza aver seguito il corso:

### ❓ Domanda 1: *"Perché avete usato sia LLM diversi sia Stance (caratteri) diversi?"*
> **Risposta**: *"Perché usare un solo modello porta ad avere un unico punto di vista senza contraddittorio. Tuttavia, anche interrogando modelli diversi con lo stesso prompt neutro, gli LLM tendono ad andare subito d'accordo per via del bias di conformismo (sycophancy). Assegnando a ciascuna famiglia di modelli (GPT-OSS 120B, Gemini 2.5 Flash, Qwen 3.8 27B, GPT-OSS 20B) una Stance diversa (Pragmatist, Guardian, Innovator, Skeptic), forziamo una vera divergenza iniziale sui trade-off ISO/IEC 25010 prima di cercare il consenso."*

### ❓ Domanda 2: *"Come evitate che gli agenti si copino a vicenda all'inizio del dibattito?"*
> **Risposta**: *"Nel nostro protocollo a 5 fasi (`orchestrator.py`), la Fase 2 (`PROPOSE`) esegue i 4 agenti in completo isolamento e in parallelo (`asyncio.gather`). Nessun agente riceve le risposte degli altri finché tutti non hanno consegnato la propria proposta iniziale. Solo nella Fase 3 (`CRITIQUE & REVISE`) vedono le proposte dei colleghi e possono cambiare idea (`mind_changed=true`) unicamente se convinti da prove citate dalla Knowledge Base."*

### ❓ Domanda 3: *"Come funziona la vostra Knowledge Base e come evitate che scelgano pattern sbagliati?"*
> **Risposta**: *"Abbiamo strutturato i 18 item della Knowledge Base (`knowledge_items.json`) secondo il modello dei Decision Layers (Nishio, Washizaki, Muccini et al., 2026): ogni pattern ha i `decision_drivers` ISO 25010, le `selection_conditions` ('Select when') e le `rejection_conditions` ('Reject when'). Durante il retrieval (`knowledge_base.py`), il sistema dà un bonus di +4.0 ai pattern le cui condizioni di selezione combaciano coi vincoli del problema e penalizza di -5.0 quelli le cui condizioni di scarto vengono violate."*

### ❓ Domanda 4: *"Come avete strutturato l'ADR finale e cosa succede se gli agenti scelgono un'opzione che viola i vincoli?"*
> **Risposta**: *"L'ADR segue rigorosamente lo standard MADR (Miccio, Tommasel, Díaz-Pace, 2026): include obbligatoriamente i `decision_drivers`, la lista di tutte le opzioni considerate con `pros` e `cons` espliciti anche per le alternative scartate, e il `minority_dissent` per non perdere l'opinione di minoranza. Inoltre, prima della Fase 5 (`DECIDE`), il Chair esegue un `ADR Validation Gate` formale (`validate_adr_constraints`): se l'opzione scelta viola un vincolo ferreo (come scegliere il cloud pubblico quando c'è il vincolo `on-prem`), attiva automaticamente un round interno di auto-correzione."*

### ❓ Domanda 5: *"Come funziona il Feedback Loop e come fa il sistema a migliorare nel tempo senza ri-addestrare i modelli?"*
> **Risposta**: *"Abbiamo due loop: lo Short Loop inietta la critica dell'umano nella sessione corrente facendo fare un round immediato di revisione. Il Long Loop (`memory.py`), quando l'umano conferma la decisione finale, agisce su due leve: aggiorna per rinforzo i pesi di fiducia (`agent_trust_weights`) degli agenti che avevano votato come l'umano, ed estrae un principio architetturale (`LEARNED-XX`). Nelle decisioni successive, usiamo la strategia ibrida `Last_K + RAFG` (Gupta et al., 2026), iniettando le ultime 3 decisioni più le 3 più simili semanticamente, evitando di passare tutta la storia intera."*

### ❓ Domanda 6: *"Come avete svolto gli Esperimenti A e B senza barare (data leakage)?"*
> **Risposta**: *"Abbiamo creato 24 scenari (`benchmark_scenarios.json`) divisi rigorosamente in due insiemi disgiunti: 12 nel `feedback_set` e 12 nell'`held_out_test_set`. Nell'Esperimento B alleniamo la memoria del Consiglio solo sui 12 scenari di feedback (a blocchi di 4) e misuriamo l'accuratezza esclusivamente sui 12 scenari di test mai visti, dove l'accuratezza passa dal 66.7% al 100.0% (+33.3%) e batte il miglior LLM singolo in zero-shot del +25.0% (100% vs 75%)."*
