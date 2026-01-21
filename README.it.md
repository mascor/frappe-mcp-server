# Server MCP per Frappe

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Frappe](https://img.shields.io/badge/Frappe-Framework-blue)](https://frappeframework.com)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)](https://modelcontextprotocol.io)
[![Security Audit](https://img.shields.io/badge/Security%20Audit-Passed-brightgreen)](#report-di-audit-di-sicurezza)
[![Tests](https://img.shields.io/badge/Tests-18%2F18%20Passed-brightgreen)](#riepilogo-risultati-test)

[![Read in English](https://img.shields.io/badge/lang-en-red.svg)](README.md)

Un server **Model Context Protocol (MCP)** sicuro e con audit log per Frappe.
Questa app ti permette di esporre specifici DocType e operazioni ai client MCP (come gli agenti AI) con permessi granulari rigorosi, garantendo un accesso sicuro e controllato ai tuoi dati Frappe.

## Funzionalità

- **Autenticazione Sicura**: accesso dedicato `Utente MCP` tramite Token o API Key.
- **Allowlist Granulare**: Consenti esplicitamente specifici DocType e operazioni (Crea, Leggi, Aggiorna, Elimina).
- **Controllo a Livello di Campo**: Restringi quali campi possono essere letti o scritti.
- **Audit Logging**: Ogni richiesta viene registrata con latenza, stato e riepilogo del payload.
- **Validazione Rigorosa**: Tutti i filtri e gli input vengono validati rispetto alla allowlist.

## Installazione

1.  Scarica l'app:
    ```bash
    bench get-app https://github.com/mascor/frappe-mcp-server
    ```

2.  Installa sul tuo sito:
    ```bash
    bench --site <tuo-sito> install-app mcp_server
    ```

## Configurazione

### 1. Setup Utente MCP & Impostazioni
Puoi usare lo script di setup incluso per configurare rapidamente il server con un utente e un token predefiniti:

```bash
bench --site <tuo-sito> execute mcp_server.setup.setup_mcp
```
Questo farà quanto segue:
- Crea un utente `mcp@example.com` (se non esiste).
- Genera un `X-MCP-Token` sicuro e lo salva nelle **Impostazioni Server MCP**.
- Abilita il Server MCP.

In alternativa, vai su **Impostazioni Server MCP** nella Scrivania (Desk) e configura manualmente.

### 2. Configura Allowlist
Di default, **nessun accesso è consentito**. Devi permettere esplicitamente i DocType.

1.  Vai su **MCP Doctype Allowlist**.
2.  Crea un nuovo record per il DocType che vuoi esporre (es. `ToDo`).
3.  Spunta le operazioni che vuoi consentire (`Allow Read`, `Allow Create`, ecc.).
4.  (Opzionale) restringi campi e filtri nelle tabelle figlie per una sicurezza maggiore.

## Utilizzo

Il server espone strumenti MCP standard via API.

### Autenticazione
Il server supporta l'autenticazione tramite **API Key** (raccomandata per i client MCP).

Includi l'header `Authorization` in tutte le richieste.

### Strumenti (Tools)

#### `ping`
Controllo connessione server.
```bash
curl -X POST https://<tuo-sito>/api/method/mcp_server.api.ping \
     -H "Authorization: token <api_key>:<api_secret>"
```

#### `search_docs`
Cerca documenti con filtri.
```json
{
    "doctype": "ToDo",
    "filters": {"status": "Open"}
}
```

#### `create_doc`
Crea un nuovo documento.
```json
{
    "doctype": "ToDo",
    "data": {
        "description": "Nuovo Task da MCP"
    }
}
```

#### `update_doc`
Aggiorna un documento esistente.
```json
{
    "doctype": "ToDo",
    "name": "TODO-0001",
    "data": {
        "status": "Closed"
    }
}
```

#### `delete_doc`
Elimina un documento.
```json
{
    "doctype": "ToDo",
    "name": "TODO-0001"
}
```

## Audit Log
Controlla **MCP Audit Log** nella Scrivania per vedere la cronologia di tutte le richieste, inclusi stato successo/errore, latenza e diff.

## Licenza
MIT

## Connessione Rapida: Client MCP

Per connetterti a questo server da un Client AI (come Claude Desktop o Cursor), usa il Client Python ufficiale:

[**frappe-mcp-client**](https://github.com/mascor/frappe-mcp-client/blob/main/README.it.md)

Segui le istruzioni di installazione e configurazione nel repository del client per iniziare.

---

# Frappe MCP Server - Report dei Test

## Comandi Disponibili

| Comando | Descrizione | Parametri |
|---------|-------------|-----------|
| `ping` | Verifica connessione server | Nessuno |
| `search_docs` | Cerca documenti | `doctype` (richiesto), `filters` (opzionale), `fields` (opzionale) |
| `get_doc` | Ottieni un documento specifico | `doctype` (richiesto), `name` (richiesto) |
| `create_doc` | Crea un nuovo documento | `doctype` (richiesto), `data` (richiesto) |
| `update_doc` | Aggiorna un documento esistente | `doctype` (richiesto), `name` (richiesto), `data` (richiesto) |
| `get_meta` | Ottieni metadati DocType | `doctype` (richiesto) |
| `delete_doc` | Elimina un documento | `doctype` (richiesto), `name` (richiesto) |

---

## Riepilogo Risultati Test

### Sezione A: Operazioni Standard DocType

| Test | DocType | Operazione | Stato |
|------|---------|------------|-------|
| A1 | Note | create_doc | ✅ PASS |
| A2 | Note | get_doc | ✅ PASS |
| A3 | Note | update_doc | ✅ PASS |
| A4 | Note | search_docs | ✅ PASS |
| A5 | Note | delete_doc | ✅ PASS |
| A6 | Event | create_doc | ✅ PASS |
| A7 | Event | get_meta | ✅ PASS |
| A8 | Event | delete_doc | ✅ PASS |

### Sezione B: Filtri e Campi

| Test | Descrizione | Stato |
|------|-------------|-------|
| B1 | search_docs con filtri | ✅ PASS |
| B2 | search_docs con campi | ✅ PASS |
| B3 | search_docs con filtri + campi | ✅ PASS |

### Sezione C: Casi Limite / Gestione Errori

| Test | Descrizione | Atteso | Stato |
|------|-------------|--------|-------|
| C1 | get_doc documento inesistente | 404 Not Found | ✅ PASS |
| C2 | create_doc campo obbligatorio mancante | 417 Expectation Failed | ✅ PASS |
| C3 | update_doc documento inesistente | 404 Not Found | ✅ PASS |
| C4 | delete_doc documento inesistente | 404 Not Found | ✅ PASS |
| C5 | get_meta DocType inesistente | 403 Forbidden | ✅ PASS |

### Sezione D: Permessi

| Test | Descrizione | Stato |
|------|-------------|-------|
| D1 | search_docs su DocType consentito (User) | ✅ PASS |
| D2 | get_meta su DocType non consentito (Role) | ✅ PASS (403) |

---

## 🎉 Risultato Finale: 18/18 Test Superati

---

## Requisiti di Setup

1. **Installa l'app MCP Server** sul tuo sito Frappe
2. **Crea un utente API** (es. `mcp_user@example.com`)
3. **Genera API Key** per l'utente (Utente → Accesso API → Genera Chiavi)
4. **Assegna ruoli appropriati** all'utente API (es. Amministratore di Sistema)
5. **Configura la Allowlist**
   - Vai su "MCP Doctype Allowlist"
   - Aggiungi i DocType che vuoi esporre via MCP
   - Configura le operazioni consentite (Leggi, Crea, Aggiorna, Elimina, Meta)
6. **Configura il client MCP** con le credenziali API

---

## Risoluzione Problemi (Troubleshooting)

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `403 Forbidden` | Permessi mancanti | Assegna ruoli all'utente API o aggiungi decoratore `@frappe.whitelist()` |
| `403 Forbidden` su tutte le chiamate | Voce Allowlist mancante | Aggiungi DocType a MCP Doctype Allowlist |
| `403 Forbidden` su operazione spec. | Operazione non abilitata | Abilita l'operazione nella Allowlist |
| `403 Forbidden` con filtri | Campo filtro non consentito | Aggiungi campo a Filtri Consentiti o lascia vuoto per tutti |
| `404 Not Found` | Documento inesistente | Verifica nome documento |
| `417 Expectation Failed` | Modulo non trovato | Installa/reinstalla l'app MCP Server |
| `417 Expectation Failed` | Errore validazione | Controlla campi obbligatori nel DocType |
| `500 Internal Server Error` | Errore codice | Esegui `bench --site [sito] logs` |

---

## Note di Sicurezza

- Solo i DocType esplicitamente aggiunti alla Allowlist sono accessibili
- Ogni operazione (Leggi, Crea, Aggiorna, Elimina, Meta) deve essere abilitata esplicitamente
- L'autenticazione API è richiesta per tutte le operazioni
- Considera di restringere DocType sensibili (User, Role, ecc.) in produzione

---

# Report di Audit di Sicurezza

## Panoramica

Il server Frappe MCP è stato sottoposto a test di sicurezza completi per garantire che sia sicuro per l'uso in produzione. Tutti i 15 test di sicurezza sono stati superati con successo.

---

## Risultati Test di Sicurezza

### Autenticazione e Autorizzazione

| Test | Descrizione | Risultato |
|------|-------------|-----------|
| S1 | Campi sensibili (password, api_key, api_secret) non accessibili | ✅ PASS |
| S2 | DocType di sistema (DocType) bloccati | ✅ PASS |
| S3 | DocType Role bloccato | ✅ PASS |
| S4 | System Settings bloccato | ✅ PASS |
| S5 | Email Account (credenziali) bloccato | ✅ PASS |
| S6 | Auto-modifica Allowlist bloccata | ✅ PASS |

### Attacchi Injection

| Test | Descrizione | Risultato |
|------|-------------|-----------|
| S7 | SQL Injection nei filtri | ✅ PASS |
| S8 | SQL Injection nel nome documento | ✅ PASS |
| S12 | XSS nel contenuto documento | ✅ PASS (sanitizzato) |
| S14 | Attacco Path Traversal | ✅ PASS |

### Protezione Dati

| Test | Descrizione | Risultato |
|------|-------------|-----------|
| S9 | Accesso a Error Log bloccato | ✅ PASS |
| S10 | Accesso a Scheduled Job Log bloccato | ✅ PASS |
| S11 | Accesso a File DocType bloccato | ✅ PASS |
| S13 | Campi sensibili auto-filtrati da User | ✅ PASS |
| S15 | Escalation privilegi prevenuta | ✅ PASS |

---

## Funzionalità di Sicurezza

### 1. Controllo Accessi Basato su Allowlist

Solo i DocType esplicitamente aggiunti alla **MCP Doctype Allowlist** sono accessibili tramite API. Ogni DocType può essere configurato con permessi granulari:

- Allow Read (Get, Search)
- Allow Create
- Allow Update
- Allow Delete
- Allow Meta (Schema)

### 2. Filtro Automatico Campi Sensibili

I seguenti campi vengono **rimossi automaticamente** da tutte le risposte API, indipendentemente dai permessi utente o dalla configurazione Allowlist:

- `api_key`
- `api_secret`
- `password`
- `new_password`
- `reset_password_key`

Questo filtro lato server impedisce la fuga di credenziali anche se il DocType User è nella Allowlist.

### 3. Sanitizzazione Input

- **Protezione SQL Injection**: Tutti gli input utente sono parametrizzati tramite l'ORM di Frappe
- **Protezione XSS**: Il contenuto HTML viene sanitizzato automaticamente (es. `<script>` → `&lt;script&gt;`)
- **Protezione Path Traversal**: I nomi dei DocType vengono validati rispetto alla Allowlist

### 4. DocType di Sistema Protetti

I seguenti DocType sensibili sono bloccati di default (non nella Allowlist):

- `DocType` - Schema di sistema
- `Role` - Ruoli permessi
- `System Settings` - Configurazione globale
- `Email Account` - Credenziali email
- `Error Log` - Errori di sistema (possono contenere dati sensibili)
- `Scheduled Job Log` - Log job in background
- `File` - File caricati
- `MCP Doctype Allowlist` - Previene auto-modifica

---

## Best Practice di Sicurezza

### Per il Deployment in Produzione

1. **Minimizza la Allowlist**: Aggiungi solo i DocType strettamente necessari
2. **Restringi le Operazioni**: Abilita solo le operazioni richieste (Read/Create/Update/Delete)
3. **Usa Restrizioni Campi**: Limita quali campi possono essere letti o usati nei filtri
4. **Utente API Separato**: Crea un utente dedicato per MCP con ruoli minimi
5. **Monitora gli Accessi**: Controlla regolarmente i log di accesso API
6. **Ruota le API Key**: Rigenera periodicamente le credenziali API

### Esempio Configurazione Allowlist

```
DocType: Customer
├── Allow Read: ✅
├── Allow Create: ❌
├── Allow Update: ❌
├── Allow Delete: ❌
├── Allow Meta: ✅
├── Allowed Fields: ["name", "customer_name", "email"]
└── Allowed Filters: ["name", "customer_name"]
```

Questa configurazione consente l'accesso in sola lettura ai record Customer con campi limitati.

---

## Riepilogo Conformità

| Categoria | Stato |
|-----------|-------|
| Autenticazione | ✅ Richiesta API Key/Secret |
| Autorizzazione | ✅ Controllo accessi basato su Allowlist |
| Protezione Dati | ✅ Campi sensibili auto-filtrati |
| Validazione Input | ✅ Protetto da SQL/XSS/Path Traversal |
| Audit Trail | ✅ Logging Frappe standard |

---

## Risultato Finale

```
╔══════════════════════════════════════════════════════════════╗
║                    SECURITY AUDIT PASSED                     ║
║                                                              ║
║                    15/15 Test Superati                       ║
║                                                              ║
║          ✅ Pronto per il Deployment in Produzione           ║
╚══════════════════════════════════════════════════════════════╝
```
