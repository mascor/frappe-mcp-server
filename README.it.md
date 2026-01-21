# Server MCP per Frappe

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
Includi l'header `X-MCP-Token` in tutte le richieste.

### Strumenti (Tools)

#### `mcp_ping`
Health check e info versione.
```bash
curl -X POST https://<tuo-sito>/api/method/mcp_server.api.mcp_ping \
     -H "X-MCP-Token: <tuo-token>"
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

## Audit Log
Controlla **MCP Audit Log** nella Scrivania per vedere la cronologia di tutte le richieste, inclusi stato successo/errore, latenza e diff.

## Licenza
MIT

## Connessione Rapida: Client MCP

Per connetterti a questo server da un Client AI (come Claude Desktop o Cursor), usa il Client Python ufficiale:

[**frappe-mcp-client**](https://github.com/mascor/frappe-mcp-client/blob/main/README.it.md)

Segui le istruzioni di installazione e configurazione nel repository del client per iniziare.
