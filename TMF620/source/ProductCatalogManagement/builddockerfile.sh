#!/usr/bin/env bash
set -euo pipefail

PLATFORMS="${PLATFORMS:-linux/amd64}"
VERSION="${VERSION:-1.0.0}"

docker buildx build -t "ravijangra92/tmf620:product-catalog-api-${VERSION}" --platform "$PLATFORMS" -f source/ProductCatalogManagement/productcatalogapi-dockerfile . --push
docker buildx build -t "ravijangra92/tmf620:mcp-server-${VERSION}" --platform "$PLATFORMS" -f source/ProductCatalogManagement/productcatalogmcp-dockerfile . --push
docker buildx build -t "ravijangra92/tmf620:open-metrics-${VERSION}" --platform "$PLATFORMS" -f source/ProductCatalogManagement/openmetrics-dockerfile . --push
docker buildx build -t "ravijangra92/tmf620:party-role-${VERSION}" --platform "$PLATFORMS" -f source/ProductCatalogManagement/partyrole-dockerfile . --push
docker buildx build -t "ravijangra92/tmf620:role-init-${VERSION}" --platform "$PLATFORMS" -f source/ProductCatalogManagement/roleinitialization-dockerfile . --push
docker buildx build -t "ravijangra92/tmf620:product-catalog-init-${VERSION}" --platform "$PLATFORMS" -f source/ProductCatalogManagement/productcataloginitialization-dockerfile . --push

# Extra sample services retained from ProductCatalog. The current Helm chart does not deploy these by default.
docker buildx build -t "ravijangra92/tmf620:promotion-management-api-${VERSION}" --platform "$PLATFORMS" -f source/ProductCatalogManagement/promotionmgmt-dockerfile . --push
docker buildx build -t "ravijangra92/tmf620:permission-spec-api-${VERSION}" --platform "$PLATFORMS" -f source/ProductCatalogManagement/permissionspec-dockerfile . --push
