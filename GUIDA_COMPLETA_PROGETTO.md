# GUIDA COMPLETA AL PROGETTO E TUTORIAL DEL PORTALE WEB
## AI Assisted Software Architecting Council (Corso di Software Architecture 2026/27)

Questa guida è stata scritta in modo **semplice, discorsivo e dettagliatissimo** per permettere a tutti e 4 i componenti del gruppo di capire al 100%:
1. **Cosa chiede davvero il Prof. Muccini** (e i mentor di Micron) nelle slide della traccia.
2. **Tutti i passaggi che sono stati svolti** per costruire il progetto, spiegando **cosa fa ogni file** e **perché è stato progettato così**.
3. **Il funzionamento interno del sistema** (passo dopo passo, da quando premi il bottone a quando esce la decisione finale).
4. **Il Tutorial completo del sito web (`http://127.0.0.1:8000`)**, bottone per bottone, incluso un **"Copione pronto per l'esame"** da seguire durante la presentazione live.

---

# PARTE 1: Capire la Traccia del Prof (In Parole Semplici)

## 1.1 Qual è il problema di partenza? (Slide 2)
Nel lavoro reale di un **Software Architect** (specialmente in aziende industriali enormi come **Micron**, che produce semiconduttori e memorie), progettare un sistema non significa trovare la "risposta giusta" su un libro, ma **bilanciare compromessi (trade-off)** tra requisiti che fanno a pugni tra loro:
- Vuoi **massima velocità** (latenza `< 1 secondo`), ma hai **pochi soldi o un team piccolo** (solo 3 tecnici).
- Vuoi **massima sicurezza e zero perdita di dati**, ma non vuoi un sistema così complicato che nessuno sa manutenerlo.

**Cosa succede se chiedi consiglio a una singola AI (es. un singolo prompt su ChatGPT)?**
- Ti dà **una sola risposta**, con tono super sicuro di sé (*one confident view*).
- Spesso cade nell'effetto **"Hype aziendale"**: ti consiglia tecnologie gigantesche usate da Netflix o Google (come cluster Kafka enormi o 20 microservizi) anche se tu hai solo 3 programmatori, perché nessuno la contraddice.

## 1.2 Qual è l'idea del progetto? (Slide 3 e 4)
Nelle aziende vere, le decisioni architetturali importanti non le prende una persona sola chiusa in una stanza, ma un **Consiglio di Architetti (Architecture Review Board)**:
- Ci sono più architetti con **mentalità diverse** (chi bada ai costi e alla semplicità, chi bada alla sicurezza, chi vuole innovare, chi è scettico su tutto).
- Ognuno studia il problema, propone la sua idea, **critica le idee degli altri portando prove tecniche**, e alla fine un **Presidente (Chair)** tira le somme e scrive il documento ufficiale della decisione (**ADR — Architecture Decision Record**), annotando anche chi è rimasto di opinione contraria (**Dissent**).

Il prof vi chiede quindi di costruire **un Consiglio di Agenti AI** basato su **3 Pilastri Obbligatori**:
1. **Pilastro 1 (Diverse Council)**: Almeno 3 agenti architetti basati su **modelli LLM di famiglie diverse** e con **caratteri (Stance) diversi**.
2. **Pilastro 2 (Debate & Consensus)**: Un protocollo strutturato in cui gli agenti prima pensano da soli, poi discutono tra loro scambiandosi messaggi visibili in diretta, e infine convergono su una proposta scritta dal Chair Agent.
3. **Pilastro 3 (Feedback Loop)**: L'architetto umano guida il sistema e gli dà feedback; grazie a questo feedback, il consiglio **impara** e nelle decisioni successive diventa **misurabilmente più bravo**.

---

# PARTE 2: Tutti i Passaggi Svolti e il PERCHÉ di Ogni Scelta

Qui sotto trovi tutti i mattoni che ho costruito nella cartella del progetto, con la spiegazione del **perché** sono stati fatti esattamente così rispetto alle slide del prof.

---

## PASSO 1: Configurazione Multi-LLM e Creazione dei 4+1 Agenti
- **File coinvolti**: [`.env`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/.env), [`backend/config.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/config.py), [`backend/llm_providers.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/llm_providers.py), [`backend/agents.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/agents.py)
- **Riferimento traccia**: Slide 5 (*"The council: peer architects, different minds"*) e Slide 6 (*"Suggested stances: Pragmatist, Guardian, Innovator, Skeptic"*).

### Cosa abbiamo fatto:
Abbiamo creato **4 Agenti Architetti alla pari (Peer Architects)** più **1 Agente Presidente (Chair Agent)**:

1. ⚙️ **Pragmatist Architect (`agent_pragmatist`)**:
   - **Famiglia LLM**: *OpenAI GPT-OSS 120B* (tramite Groq).
   - **Carattere (Stance)**: Pragmatico. Cerca la soluzione più semplice che funziona, veloce da realizzare e facile da gestire per un team piccolo.
2. 🛡️ **Guardian Architect (`agent_guardian`)**:
   - **Famiglia LLM**: *Google Gemini 2.5 Flash* (con backup automatico su *ALLaM-2*).
   - **Carattere (Stance)**: Guardiano prudente. Mette al primo posto sicurezza, affidabilità, tolleranza ai guasti e tecnologie super collaudate.
3. 🚀 **Innovator Architect (`agent_innovator`)**:
   - **Famiglia LLM**: *Alibaba Qwen 3.8 27B* (tramite Groq).
   - **Carattere (Stance)**: Innovatore. Spinge per tecnologie moderne, altissime prestazioni e architetture pronte a scalare 10 volte in futuro.
4. 🧐 **Skeptic Architect (`agent_skeptic`)**:
   - **Famiglia LLM**: *GPT-OSS 20B / Mistral / DeepSeek* (tramite Groq).
   - **Carattere (Stance)**: Scettico. Non si fida delle mode, cerca i costi nascosti di manutenzione (Day-2 Operations) e pretende citazioni di prove reali.
5. ⚖️ **Chair Architect (`agent_chair`)**:
   - **Ruolo**: Moderatore neutrale. Introduce il problema, raccoglie i voti pesati per l'affidabilità di ciascun agente, risolve gli eventuali pareggi e compila il documento finale **ADR**.

### Perché l'abbiamo fatto così?
- **Perché la Slide 5 vieta gli "specialisti ristretti"**: Il prof scrive chiaramente *"Full architect mandate — not a specialist. Same question, same knowledge base, same output contract"*. Quindi tutti e 4 gli agenti hanno il mandato completo di architetto software, ricevono la stessa domanda e leggono la stessa Knowledge Base.
- **Perché servono SIA modelli diversi SIA caratteri diversi? (Slide 5)**: Perché i modelli AI moderni sono addestrati per essere "gentili e d'accordo con l'interlocutore". Dando a ciascuno sia un modello diverso sia una *Stance* precisa, li costringiamo a guardare il problema da angolazioni opposte prima di trovare un punto d'incontro.
- **Perché c'è anche un Simulatore deterministico dentro [`backend/llm_providers.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/llm_providers.py)?** Perché durante una demo d'esame può capitare che il Wi-Fi dell'università cada o che le API gratuite raggiungano il limite di richieste al minuto. Grazie al nostro sistema ibrido, il progetto chiama le vere API cloud in tempo reale, ma se c'è un problema di rete (o se spunti *Fast Deterministic Sim Mode*) usa il motore di ragionamento interno senza **mai** andare in crash davanti al prof!

---

## PASSO 2: Contratto Dati Tipizzato e Message Bus A2A in Tempo Reale
- **File coinvolti**: [`backend/schemas.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/schemas.py), [`backend/bus.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/bus.py)
- **Riferimento traccia**: Slide 5 (*"Same output contract"*) e Slide 8 (*"Must be: Structured, Observable, Traceable, Swappable"*).

### Cosa abbiamo fatto:
1. In [`backend/schemas.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/schemas.py) abbiamo definito con la libreria **Pydantic** due schemi rigorosi:
   - `AgentOutputContract`: obbliga ogni agente a rispondere sempre con una struttura precisa contenente:
     - `selected_option` (l'opzione architetturale scelta)
     - `confidence` (quanto è sicuro da `0.0` a `1.0`)
     - `summary_argument` (la spiegazione tecnica)
     - `tradeoffs` (i compromessi analizzati, es. *Latenza vs Facilità di gestione*)
     - `citations` (i codici dei documenti citati dalla Knowledge Base, es. `["KB-PAT-01", "KB-ADR-01"]`)
     - `mind_changed` (`true` o `false`: dice se l'agente ha cambiato idea rispetto al turno precedente!)
     - `change_reason` (il motivo per cui ha cambiato idea).
   - `A2AMessage`: è la "busta" del messaggio che viaggia tra gli agenti, con ID univoco, orario, fase del dibattito, chi parla, che modello LLM usa, a quali messaggi sta rispondendo (`reply_to_ids`) e quanti millisecondi ci ha messo.
2. In [`backend/bus.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/bus.py) abbiamo costruito `A2AMessageBus`: un canale di comunicazione Publish/Subscribe che registra ogni messaggio e lo spedisce **in diretta streaming (tramite SSE - Server-Sent Events)** al browser web.

### Perché l'abbiamo fatto così?
Perché la **Slide 8** impone 4 regole non negoziabili:
- **Structured** → Garantito dai modelli Pydantic in `schemas.py`.
- **Observable** → Garantito dallo streaming SSE (`/api/stream`) che fa comparire i messaggi in diretta nella UI.
- **Traceable** → Ogni messaggio ha `reply_to_ids` e `citations`, quindi sappiamo sempre *chi ha detto cosa e basandosi su quale fonte*.
- **Swappable** → Possiamo aggiungere o togliere agenti dalla lista in `orchestrator.py` senza toccare il codice del bus o del protocollo.

---

## PASSO 3: Il Protocollo di Dibattito in 5 Fasi
- **File coinvolti**: [`backend/orchestrator.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/orchestrator.py)
- **Riferimento traccia**: Slide 7 (*"Debate protocol: Frame → Propose → Critique & revise → Converge → Decide"*).

### Cosa succede esattamente quando avvii un dibattito?
Il file [`backend/orchestrator.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/orchestrator.py) esegue una macchina a stati divisa in **5 fasi**:

1. **Fase 1 — `FRAME` (Inquadramento)**:
   - Il **Chair Agent** legge la richiesta dell'utente, individua gli attributi di qualità (es. *latenza, operabilità, sicurezza*) e i vincoli (es. *on-prem, piccolo team*), cerca nella Knowledge Base i documenti più utili e nella Memoria le regole apprese in passato, e pubblica il primo messaggio sul bus per aprire i lavori.
2. **Fase 2 — `PROPOSE` (Proposta in Isolamento — "No Peeking")**:
   - **Regola d'oro della Slide 7**: *"Think alone, then debate — LLMs tend to agree with whoever they talk to"*.
   - Ciascuno dei 4 agenti viene interrogato **da solo**, senza poter vedere cosa stanno rispondendo gli altri 3. Ognuno fa la sua proposta iniziale basandosi sul proprio carattere (*Pragmatist*, *Guardian*, *Innovator*, *Skeptic*).
3. **Fase 3 — `CRITIQUE & REVISE` (Critica e Revisione a round limitati)**:
   - Adesso a ogni agente vengono mostrate le proposte fatte dagli altri 3 colleghi nella Fase 2.
   - Ogni agente deve **criticare** chi ha proposto soluzioni diverse dalla sua e decidere se **difendere** la propria scelta iniziale oppure **cambiare idea (`mind_changed = true`)**, ma solo se un collega ha portato prove più forti dalla Knowledge Base o dalla memoria aziendale!
   - Il numero di round è limitato (`MAX_CRITIQUE_ROUNDS`, di default 1 o 2) e si ferma subito se raggiungono l'unanimità, così il dibattito termina sempre in tempi rapidi (*"Bounded rounds — debate must always terminate"*).
4. **Fase 4 — `CONVERGE` (Convergenza e Voto Pesato)**:
   - Il **Chair Agent** raccoglie le posizioni finali dei 4 agenti e calcola il punteggio di ogni opzione.
   - Non è una banale conta dei voti: ogni voto vale in base a:
     $$\text{Peso di Fiducia dell'Agente (Trust Weight)} \times \text{Confidenza} \times \text{Bonus per le fonti citate}$$
   - Se c'è un pareggio (*Deadlock*), il Chair usa le regole apprese dall'umano per sbloccare la situazione.
5. **Fase 5 — `DECIDE` (Generazione ADR + Dissenso di Minoranza)**:
   - Il Chair genera il documento finale **ADR (`ADRDecision`)** con l'opzione vincitrice, i compromessi, le citazioni e una sezione speciale chiamata **`minority_dissent`**: se ad esempio l'*Innovator* non era d'accordo con la maggioranza, la sua opinione contraria e le sue motivazioni **non vengono cancellate**, ma restano scritte nell'ADR per l'architetto umano (*"Keep the minority view — dissent is part of the output"*).

---

## PASSO 4: La Knowledge Base Condivisa (Grounding)
- **File coinvolti**: [`data/knowledge_items.json`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/data/knowledge_items.json), [`backend/knowledge_base.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/knowledge_base.py)
- **Riferimento traccia**: Slide 9 (*"Knowledge: arguments must cite evidence"*).

### Cosa abbiamo fatto:
Abbiamo creato un database JSON strutturato con **18 fonti autorevoli** divise nelle 4 categorie suggerite dalla Slide 9:
1. **Modello di Qualità ISO/IEC 25010 (`KB-ISO-01` .. `KB-ISO-04`)**: Performance Efficiency, Reliability, Security, Maintainability/Operability.
2. **Catalogo dei Pattern Architetturali (`KB-PAT-01` .. `KB-PAT-08`)**: NATS JetStream vs Kafka, Monolite Modulare vs Microservizi, CQRS + Event Sourcing, Saga Orchestrata (Temporal) vs Coreografata, TimescaleDB vs ClickHouse, Edge Store-and-Forward Gateway.
3. **Catalogo delle Tattiche Architetturali (`KB-TAC-01` .. `KB-TAC-04`)**: Transactional Outbox, Circuit Breaker & Bulkhead, Zero-Trust mTLS vs API Gateway OIDC, Strangler Fig + Anti-Corruption Layer.
4. **Principi Aziendali e ADR Passati (`KB-ADR-01` .. `KB-ADR-02`)**: Principio di Proporzionalità Operativa per piccoli team (`<= 5 tecnici`) e Sovranità dei Dati On-Premise nelle camere bianche dei semiconduttori.

Ogni volta che inizia un dibattito, [`backend/knowledge_base.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/knowledge_base.py) cerca i documenti più pertinenti tramite tag, parole chiave e attributi di qualità e li fornisce in modo identico a tutti gli agenti per garantire un **dibattito equo (Fair Debate)**.

---

## PASSO 5: Il Doppio Ciclo di Feedback Umano (Short Loop & Long Loop)
- **File coinvolti**: [`backend/memory.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/memory.py), [`data/memory_store.json`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/data/memory_store.json)
- **Riferimento traccia**: Slide 10 (*"Feedback loop: the human decides, the council learns — Short loop & Long loop"*).

### Come funzionano i due cicli di apprendimento?
1. **Short Loop (Dentro la singola decisione)**:
   - Il consiglio propone una decisione, ma l'architetto umano non è ancora convinto e scrive un commento (es. *"Attenzione: il nostro team di 3 persone non conosce la JVM, riconsiderate il peso operativo"*).
   - Il sistema inietta il messaggio dell'umano nel bus e fa fare **subito un nuovo giro di revisione** agli agenti, che aggiornano la proposta corrente.
2. **Long Loop (Per tutte le decisioni future)**:
   - Quando l'umano approva o sceglie la decisione finale definitiva, [`backend/memory.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/memory.py) fa **due cose fondamentali**:
     - **Aggiorna i Pesi di Fiducia (`agent_trust_weights`)**: Gli agenti che avevano votato come l'umano ricevono un premio di fiducia (`+0.12`, fino a `2.0x`), mentre quelli che avevano torto perdono un po' di peso (`-0.05`). Così nelle votazioni future chi ragiona come l'architetto umano pesa di più!
     - **Estrae un Principio Aziendale Appreso (`LEARNED-01`, `LEARNED-02`, ...)**: Salva la regola spiegata dall'umano dentro [`data/memory_store.json`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/data/memory_store.json). Quando in futuro capiterà uno scenario simile, gli agenti leggeranno quella regola e non ripeteranno lo stesso errore!

---

## PASSO 6: Il Benchmark da 24 Scenari e gli Esperimenti A e B
- **File coinvolti**: [`data/benchmark_scenarios.json`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/data/benchmark_scenarios.json), [`backend/evaluator.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/backend/evaluator.py), [`scripts/run_evaluation.py`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/scripts/run_evaluation.py), [`docs/EVALUATION_REPORT.md`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/docs/EVALUATION_REPORT.md)
- **Riferimento traccia**: Slide 11 (*"Experiment A: Council vs. baseline"*) e Slide 12 (*"Experiment B: Prove decisions get more accurate after feedback"*).

### Perché 24 scenari divisi in 12 + 12?
La Slide 12 chiede **20+ scenari con risposte esperte**, divisi in due insiemi separati:
- **12 Scenari di Feedback (`SCEN-01` .. `SCEN-12`, `split: "feedback"`)**: Usati per "allenare" il consiglio tramite il Long Loop.
- **12 Scenari di Test (`SCEN-13` .. `SCEN-24`, `split: "test"`)**: Tenuti nascosti durante l'allenamento e usati per misurare i voti. Come dice il prof sulla Slide 12: *"Never test on feedback scenarios — that's memorization, not learning!"*.

### Cosa dimostrano i nostri risultati?
- **Esperimento A (Council vs Singoli LLM)**: I singoli LLM chiamati da soli si fermano al **66.7% - 75.0%** di accuratezza e analizzano **1 solo trade-off**. Il nostro Consiglio completo raggiunge il **100.0%** di accuratezza (+25% rispetto al miglior modello singolo) e analizza **8 trade-off** per decisione.
- **Esperimento B (Prima vs Dopo il Feedback sul Test Set)**:
  - **Iterazione 0 (Prima del feedback, 0 regole apprese)**: Accuratezza sul Test Set = **66.7%** (Consenso medio: **74.9%**).
  - **Iterazione 1..3 (Dopo il feedback sui 12 scenari di allenamento)**: Accuratezza sul Test Set = **100.0%** (+33.3% di miglioramento netto!) e Consenso medio = **100.0%**.

---

# PARTE 3: Tutorial Passo-Passo del Sito Web (`http://127.0.0.1:8000`)

## 3.1 Come avviare il Sito Web
Quando vuoi accendere il portale sul tuo PC:
1. Apri il terminale nella cartella `ProgettoMuccini` oppure fai semplicemente doppio click sul file [`start.bat`](file:///c:/Users/berar/OneDrive/Desktop/ProgettoMuccini/start.bat).
2. Apri il browser (Chrome, Edge, Firefox) e vai all'indirizzo:
   👉 **http://127.0.0.1:8000**

In alto nella barra viola vedrai:
- Il pallino verde `● A2A Bus Live (SSE)`: indica che il canale in tempo reale con gli agenti è connesso.
- Quanti principi il consiglio ha imparato finora (`Learned Principles: X`).
- Il pulsante **`📄 Prof. Slides`**: se lo clicchi apre in un'altra scheda le slide originali del prof!

---

## 3.2 Guida alle 5 Schede (Tab) del Portale

### SCHEDA 1: `⚖ 1. Live Council Debate & ADR` (La schermata principale)
Questa schermata è divisa in due colonne:

#### Colonna di Sinistra (I Comandi dell'Architetto Umano):
1. **Menu a tendina "Load Benchmark Scenario"**:
   - Contiene tutti i **24 scenari** pronti. Quando ne selezioni uno, compila automaticamente il Titolo, il Prompt dei requisiti, le 4 Opzioni candidate, gli Attributi di qualità e i Vincoli.
   - *Puoi anche scrivere a mano qualunque testo o opzione tu voglia!*
2. **Le due caselle di spunta (Checkbox)**:
   - `Use Long-Loop Feedback Memory`: se è attiva, il consiglio usa l'esperienza accumulata nei feedback precedenti.
   - `Fast Deterministic Sim Mode`:
     - Se è **DISATTIVATA**, il sito fa vere chiamate via internet ai server di Groq e Google Gemini (ci mette circa 5-12 secondi per completare tutto il dibattito).
     - Se è **ATTIVATA**, usa il simulatore interno e completa il dibattito in mezzo secondo (perfetto per fare prove rapide o se non hai internet).
3. **Bottone Viola `⚡ Start Council Debate`**:
   - Avvia il dibattito completo in 5 fasi!
4. **Bottone `vs. Single LLM`**:
   - Interroga i 4 modelli **uno per uno da soli (senza dibattito)** sullo stesso scenario e ti mostra una tabella in basso a destra: serve per far vedere al prof dal vivo la differenza tra un singolo LLM e il Consiglio!
5. **Riquadro in basso `🔄 Short Loop & Long Loop Feedback`**:
   - **Short Loop**: dopo che il consiglio ha fatto una proposta, scrivi una critica nella casella di testo (es. *"Il nostro team di 3 persone non conosce Kafka, preferiamo un binario singolo come NATS"*) e clicca **`💬 Send Short-Loop Critique & Revise Proposal`**. Vedrai gli agenti rimettersi a discutere e aggiornare l'ADR!
   - **Long Loop**: scegli dal menu a tendina l'opzione finale che tu (umano) decidi di approvare, lascia o modifica la motivazione e clicca il bottone verde **`✅ Commit Final Decision & Teach Council`**. Comparirà una scritta verde che ti conferma che il consiglio ha imparato una nuova regola (`LEARNED-XX`) e ha aggiornato i pesi di fiducia degli agenti!

#### Colonna di Destra (Il Dibattito in Diretta e l'ADR):
1. **Barra delle 5 Fasi in alto (`1. Frame` → `2. Propose` → `3. Critique & Revise` → `4. Converge` → `5. Decide`)**:
   - Si illumina passo dopo passo mentre gli agenti parlano.
2. **Live Council Debate Transcript**:
   - Mostra i messaggi di ogni agente con:
     - Nome dell'agente, **Stance** (es. `Pragmatist`, `Guardian`) e **Famiglia/Modello LLM** usato.
     - Percentuale di confidenza (`Confidence: 88%`).
     - Eventuale badge giallo **`🔄 Mind Changed`** se nel round di critica l'agente ha cambiato idea grazie alle prove dei colleghi!
     - L'elenco dei **Trade-off** analizzati.
     - I badge viola delle **Citazioni (`[KB-PAT-01]`, `[KB-ADR-01]`)**.
3. **Riquadro Verde `Synthesized Architecture Decision Record (ADR)`**:
   - Compare alla fine del dibattito e mostra:
     - Il codice dell'ADR, il tipo di consenso raggiunto (`UNANIMOUS`, `SUPERMAJORITY`, `WEIGHTED_MAJORITY`) e la percentuale.
     - L'opzione vincitrice e la spiegazione del Presidente (Chair).
     - Il riepilogo di chi ha votato cosa.
     - **Minority View & Dissent Log**: i riquadri rossi che conservano l'opinione degli agenti che hanno votato contro la maggioranza!

---

### SCHEDA 2: `🤖 2. Swappable Agent Pool & A2A Trace`
Serve per dimostrare i requisiti architetturali della **Slide 8**:
1. **A destra in alto (`Peer Architect Pool & Learned Trust Weights`)**:
   - Vedi le 4 schede degli agenti attivi, il loro modello LLM, il loro carattere e il loro **Trust Weight** (es. `1.12x`), con il bottone `Disable/Enable` per spegnere o accendere un agente al volo.
2. **A sinistra (`➕ Hot-Swap / Add Peer Architect Agent`)**:
   - È già precompilato con un 5° agente di esempio (*FinOps & Sustainability Architect*). Se clicchi **`💾 Hot-Swap / Add Agent to Council`**, vedrai comparire immediatamente il 5° agente nella griglia a destra! Se poi torni nella Scheda 1 e avvii un dibattito, parteciperanno in 5 invece che in 4, **senza aver toccato una riga di codice**.
   - Il bottone `Reset Pool` riporta gli agenti ai 4 originali.
3. **A destra in basso (`🔍 Raw A2A Message Bus Inspector`)**:
   - Mostra il codice JSON grezzo di tutti i messaggi scambiati nell'ultimo dibattito, per far vedere al prof che lo schema dei messaggi è tipizzato e tracciabile.

---

### SCHEDA 3: `📚 3. Grounding KB & Feedback Memory`
Serve per mostrare la **Slide 9 (Knowledge Base)** e lo stato interno della **Slide 10 (Long Loop Memory)**:
1. **A sinistra (`🧠 Learned Organizational Principles & Trust`)**:
   - Mostra le barre grafiche dei pesi di fiducia (`agent_trust_weights`) di ciascun agente e l'elenco di tutte le regole aziendali (`[LEARNED-01]`, `[LEARNED-02]`, ...) che il consiglio ha imparato grazie ai tuoi feedback.
   - Il bottone `Reset Memory` azzera la memoria se vuoi ricominciare da zero.
2. **A destra (`📚 Shared Architectural Knowledge Base`)**:
   - Mostra tutte le 18 schede della Knowledge Base (`KB-ISO-01` .. `KB-ADR-02`) con titolo, riassunto e fonte ufficiale (*Provenance Source*).

---

### SCHEDA 4: `📊 4. Evaluation Lab (Exp A & Exp B)`
Serve per dimostrare in diretta le **Slide 11 e 12**:
1. **Riquadro Sinistro (`⚖ Council vs. Single-LLM Baselines — Experiment A`)**:
   - Clicca **`▶ Run Experiment A`**: in circa 1 secondo esegue il test sui 12 scenari di test e ti mostra i 3 indicatori giganti (**75.0%** miglior LLM singolo contro **100.0%** del Consiglio completo, con un guadagno di **+25.0%**) più la tabella comparativa riga per riga.
2. **Riquadro Destro (`📈 Feedback Loop Learning Curve — Experiment B`)**:
   - Clicca **`▶ Run Experiment B`**: esegue le 4 iterazioni di apprendimento (0, 4, 8 e 12 scenari di feedback) e mostra come l'accuratezza sui 12 scenari di test salga dal **66.7%** (Prima del feedback) al **100.0%** (Dopo il feedback, **+33.3%**).

---

### SCHEDA 5: `📐 5. Architecture Doc & ADRs`
Contiene tutti i documenti scritti per la consegna (consultabili direttamente dentro il sito!):
- Cliccando i bottoni a sinistra puoi leggere:
  - `Software Architecture Document` (`docs/ARCHITECTURE.md`)
  - `Experimental Evaluation Report` (`docs/EVALUATION_REPORT.md`)
  - I 5 ADR delle nostre scelte progettuali (`ADR-001` .. `ADR-005`)
- In basso a sinistra trovi anche il riquadro **Team Roster** con i 4 componenti del gruppo.

---

# PARTE 4: Copione Consigliato per la Demo d'Esame (10 Minuti)

Quando presenterete il progetto al Prof. Muccini e ai tutor di Micron, potete seguire questa scaletta perfetta:

1. **Minuto 0-2 — Introduzione e Scelte Architetturali (Tab 5 & Tab 2)**:
   - Mostrate la **Tab 2** spiegando il **Pilastro 1**: *"Abbiamo 4 Peer Architects su famiglie di modelli distinte (OpenAI GPT-OSS 120B, Google Gemini 2.5 Flash, Alibaba Qwen 3.8 27B, GPT-OSS 20B/ALLaM) con 4 Stance ortogonali (Pragmatist, Guardian, Innovator, Skeptic) più il Chair Agent."*
   - Cliccate **"Hot-Swap / Add Agent"** nella Tab 2 per far vedere che il sistema è **Swappable** a runtime, poi cliccate `Reset Pool`.
2. **Minuto 2-5 — Dibattito Live in 5 Fasi (Tab 1)**:
   - Andate nella **Tab 1**, lasciate selezionato lo scenario 1 (*Cleanroom Factory Tool Event Ingestion - 5k Tools, che è esattamente l'esempio della Slide 3 del prof*) e cliccate **`⚡ Start Council Debate`**.
   - Mentre compaiono i messaggi in tempo reale, indicate al prof:
     - La **Fase 2 (Propose)** dove gli agenti propongono in isolamento e divergono (es. l'*Innovator* propone Kafka, il *Pragmatist* propone NATS JetStream).
     - La **Fase 3 (Critique)** dove si sfidano citando `[KB-PAT-01]` e `[KB-ADR-01]` e il *Guardian* cambia idea (`🔄 Mind Changed`).
     - L'**ADR finale** in fondo che conserva il **Minority Dissent** dell'*Innovator*.
3. **Minuto 5-7 — Dimostrazione del Feedback Loop (Tab 1 & Tab 3)**:
   - Nella colonna di sinistra della Tab 1, usate prima lo **Short Loop** scrivendo un vincolo aggiuntivo e cliccando *Send Short-Loop Critique*.
   - Poi usate il **Long Loop** cliccando il bottone verde *Commit Final Decision & Teach Council*.
   - Passate alla **Tab 3** per mostrare che il principio `LEARNED-01` è stato salvato in memoria e i *Trust Weights* degli agenti si sono aggiornati.
4. **Minuto 7-10 — Dimostrazione Scientifica con gli Esperimenti A e B (Tab 4)**:
   - Andate nella **Tab 4** e cliccate **`▶ Run Experiment A`** e **`▶ Run Experiment B`**, commentando le due tabelle:
     - *"Nell'Esperimento A il Consiglio batte il miglior LLM singolo del +25% (100% vs 75%) e copre 8 trade-off contro 1."*
     - *"Nell'Esperimento B, testando esclusivamente sui 12 scenari Held-Out mai visti durante il feedback, l'accuratezza sale dal 66.7% al 100% (+33.3%) e il consenso sale dal 74.9% al 100%."*
5. *(Se il prof fa domande sulle scelte architetturali)*: Aprite la **Tab 5** e mostrate i 5 ADR (`ADR-001` .. `ADR-005`) che giustificano ogni vostra scelta progettuale!

