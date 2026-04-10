# TMF621 Trouble Ticket Management

This folder contains a reference-style `TMF621 Trouble Ticket Management` component scaffold built around the official `TMF621 Trouble Ticket v5.0.1` Open API.

The structure mirrors the pattern used for the other components in this repo:
- a Helm chart under `charts/TroubleTicketManagement`
- a source tree under `source/TroubleTicketManagement`
- a TMF621-based core API for `troubleTicket` and `troubleTicketSpecification`
- a metrics listener, role bootstrap job, Party Role API, and optional MCP wrapper

Notes:
- the component is modeled around the official TMF621 `v5.0.1` OAS
- the sample API exposes list, create, retrieve, patch, and delete for `troubleTicket` and `troubleTicketSpecification`
- `hub` registration, retrieval, deletion, and listener callback endpoints are included

Start with:
- `charts/TroubleTicketManagement/README.md`
- `source/TroubleTicketManagement/README.md`
