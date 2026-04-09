# TMF Sample Reference Components

This repository contains reference-style sample components for nine TM Forum Open APIs. Each sample follows the same broad structure:

- a top-level folder per TMF API, such as `TMF622` or `TMF760`
- a Helm chart under `charts/<ComponentName>`
- a source tree under `source/<ComponentName>`
- a runnable API microservice plus supporting engine, initialization, metrics, party-role, MongoDB, and optional MCP services

These samples are lightweight runnable baselines. They are intended to show component shape, packaging, deployment layout, and starter service behavior rather than full certification-grade implementations.

Examples:

- `TMF620` is used for `TMFC001 Product Catalog Management`
- `TMF680` is used for `TMFC050 Product Recommendation`
- `TMF678` is used for `TMFC030 Bill Generation Management`
- `TMF760` is used for `TMFC027 Product Configurator`

## API, Component, and Purpose Mapping

| TMF API | Official API Name | What This API Is For | Sample Component | Component README | Helm Chart |
| --- | --- | --- | --- | --- | --- |
| `TMF620` | Product Catalog Management | manage catalogs, categories, offerings, prices, specifications, and import/export jobs | `TMFC001 Product Catalog Management` | [TMF620](TMF620/README.md) | [ProductCatalogManagement](TMF620/charts/ProductCatalogManagement/README.md) |
| `TMF622` | Product Ordering Management | capture and validate customer product orders | `TMFC002 Product Order Capture & Validation` | [TMF622](TMF622/README.md) | [ProductOrderCaptureValidation](TMF622/charts/ProductOrderCaptureValidation/README.md) |
| `TMF632` | Party Management | manage party records such as `individual` and `organization` | `TMFC028 Party Management` | [TMF632](TMF632/README.md) | [PartyManagement](TMF632/charts/PartyManagement/README.md) |
| `TMF666` | Account Management | manage billing, financial, settlement, and related account resources | `TMFC024 Billing Account Management` | [TMF666](TMF666/README.md) | [BillingAccountManagement](TMF666/charts/BillingAccountManagement/README.md) |
| `TMF672` | User Role Permission Management | manage `permission` and `userRole` resources | `TMFC035 Permissions Management` | [TMF672](TMF672/README.md) | [PermissionsManagement](TMF672/charts/PermissionsManagement/README.md) |
| `TMF678` | Customer Bill Management | manage bill cycles, customer bills, and bill-on-demand flows | `TMFC030 Bill Generation Management` | [TMF678](TMF678/README.md) | [BillGenerationManagement](TMF678/charts/BillGenerationManagement/README.md) |
| `TMF680` | Recommendation | generate and retrieve product recommendations | `TMFC050 Product Recommendation` | [TMF680](TMF680/README.md) | [ProductRecommendation](TMF680/charts/ProductRecommendation/README.md) |
| `TMF683` | Party Interaction | manage customer and party interaction records | `TMFC023 Party Interaction Management` | [TMF683](TMF683/README.md) | [PartyInteractionManagement](TMF683/charts/PartyInteractionManagement/README.md) |
| `TMF760` | Product Configuration Management | query and check product configuration results | `TMFC027 Product Configurator` | [TMF760](TMF760/README.md) | [ProductConfigurator](TMF760/charts/ProductConfigurator/README.md) |

## Component Charts At A Glance

| Sample Component | Chart Folder | What The Chart Deploys | Main Resources / Operations | Source README |
| --- | --- | --- | --- | --- |
| `TMFC001 Product Catalog Management` | [`TMF620/charts/ProductCatalogManagement`](TMF620/charts/ProductCatalogManagement/README.md) | TMF620 API, catalog-management engine, metrics listener, Party Role API, MongoDB, bootstrap jobs, optional MCP wrapper | `productCatalog`, `category`, `productOffering`, `productOfferingPrice`, `productSpecification`, `importJob`, `exportJob` | [Source](TMF620/source/ProductCatalogManagement/README.md) |
| `TMFC002 Product Order Capture & Validation` | [`TMF622/charts/ProductOrderCaptureValidation`](TMF622/charts/ProductOrderCaptureValidation/README.md) | TMF622 API, order-validation microservice, metrics listener, Party Role API, MongoDB, bootstrap jobs, optional MCP wrapper | `productOrder` capture and validation | [Source](TMF622/source/ProductOrderCaptureValidation/README.md) |
| `TMFC028 Party Management` | [`TMF632/charts/PartyManagement`](TMF632/charts/PartyManagement/README.md) | TMF632 API, party-management engine, metrics listener, Party Role API, MongoDB, optional MCP wrapper | `individual` and `organization` with full current path surface | [Source](TMF632/source/PartyManagement/README.md) |
| `TMFC024 Billing Account Management` | [`TMF666/charts/BillingAccountManagement`](TMF666/charts/BillingAccountManagement/README.md) | TMF666 API, account-management engine, metrics listener, Party Role API, MongoDB, optional MCP wrapper | `billFormat`, `billPresentationMedia`, `billingAccount`, `billingCycleSpecification`, `financialAccount`, `partyAccount`, `settlementAccount` | [Source](TMF666/source/BillingAccountManagement/README.md) |
| `TMFC035 Permissions Management` | [`TMF672/charts/PermissionsManagement`](TMF672/charts/PermissionsManagement/README.md) | TMF672 API, permissions engine, metrics listener, Party Role API, MongoDB, optional MCP wrapper | `permission` and `userRole`; list/create/get/patch | [Source](TMF672/source/PermissionsManagement/README.md) |
| `TMFC030 Bill Generation Management` | [`TMF678/charts/BillGenerationManagement`](TMF678/charts/BillGenerationManagement/README.md) | TMF678 API, bill-generation engine, metrics listener, Party Role API, MongoDB, bootstrap jobs, optional MCP wrapper | `appliedCustomerBillingRate`, `billCycle`, `customerBill`, `customerBillOnDemand` | [Source](TMF678/source/BillGenerationManagement/README.md) |
| `TMFC050 Product Recommendation` | [`TMF680/charts/ProductRecommendation`](TMF680/charts/ProductRecommendation/README.md) | TMF680 API, recommendation engine, metrics listener, Party Role API, MongoDB, bootstrap jobs, optional MCP wrapper | `queryProductRecommendation` list/create/retrieve | [Source](TMF680/source/ProductRecommendation/README.md) |
| `TMFC023 Party Interaction Management` | [`TMF683/charts/PartyInteractionManagement`](TMF683/charts/PartyInteractionManagement/README.md) | TMF683 API, interaction-management engine, metrics listener, Party Role API, MongoDB, optional MCP wrapper | `partyInteraction` list/create/get/patch/delete | [Source](TMF683/source/PartyInteractionManagement/README.md) |
| `TMFC027 Product Configurator` | [`TMF760/charts/ProductConfigurator`](TMF760/charts/ProductConfigurator/README.md) | TMF760 API, configuration engine, metrics listener, Party Role API, MongoDB, bootstrap jobs, optional MCP wrapper | `queryProductConfiguration` and `checkProductConfiguration` | [Source](TMF760/source/ProductConfigurator/README.md) |

## Helm Chart Repository

The workflow at `.github/workflows/release-helm-charts.yml` lints every chart under `TMF*/charts/*` and, on pushes to `main`, packages them into a Helm repository, publishes the generated files to `gh-pages`, and deploys the same content through GitHub Pages.

GitHub Pages should be enabled for this repository and configured to use **GitHub Actions** as the publishing source. The published repository URL is:

```text
https://<OWNER>.github.io/<REPO>
```

Replace `<OWNER>` and `<REPO>` with the GitHub user or organization and repository name that host this project.

If you want the workflow to enable GitHub Pages automatically when it is not configured yet, add a repository secret named `PAGES_ENABLEMENT_TOKEN` and use a token with permission to administer Pages for the repository. Otherwise, enable Pages once in the repository settings and keep the publishing source set to `GitHub Actions`.

Add the repository and list the published charts:

```bash
helm repo add tmf-sample-ref-components https://<OWNER>.github.io/<REPO>
helm repo update
helm search repo tmf-sample-ref-components
```

Install any of the published charts:

| TMF API | Published Chart | Install Command |
| --- | --- | --- |
| `TMF622` | `productordercapturevalidation` | `helm upgrade --install tmf622 tmf-sample-ref-components/productordercapturevalidation -n components --create-namespace` |
| `TMF632` | `partymanagement` | `helm upgrade --install tmf632 tmf-sample-ref-components/partymanagement -n components --create-namespace` |
| `TMF666` | `billingaccountmanagement` | `helm upgrade --install tmf666 tmf-sample-ref-components/billingaccountmanagement -n components --create-namespace` |
| `TMF672` | `permissionsmanagement` | `helm upgrade --install tmf672 tmf-sample-ref-components/permissionsmanagement -n components --create-namespace` |
| `TMF678` | `billgenerationmanagement` | `helm upgrade --install tmf678 tmf-sample-ref-components/billgenerationmanagement -n components --create-namespace` |
| `TMF680` | `productrecommendation` | `helm upgrade --install tmf680 tmf-sample-ref-components/productrecommendation -n components --create-namespace` |
| `TMF683` | `partyinteractionmanagement` | `helm upgrade --install tmf683 tmf-sample-ref-components/partyinteractionmanagement -n components --create-namespace` |
| `TMF760` | `productconfigurator` | `helm upgrade --install tmf760 tmf-sample-ref-components/productconfigurator -n components --create-namespace` |

To inspect chart defaults before installing, run `helm show values tmf-sample-ref-components/<chart-name>`.

## Common Layout

Each sample component is organized in the same way:

- `TMFxxx/README.md` gives the component-level overview
- `charts/.../README.md` explains what the Helm chart deploys and how to install it
- `source/.../README.md` explains the API service and support microservices
- `tests/` contains component-level tests
- `*.component.yaml` provides the component metadata for the sample

## Where To Start

If you want to explore a specific API-to-component mapping, begin with that component folder's `README.md`. From there, move into the matching `charts/.../README.md` and `source/.../README.md` for deployment and implementation details.
