SHELL := bash
.PHONY: help typecheck ts-list ts-show
TS_VERSION ?= 5.5.4

.PHONY: help typecheck ts-list ts-show
help: ## Show SDK targets
	@grep -E '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

typecheck: ## Type-check with pinned TS (no emit)
	npx --yes -p typescript@$(TS_VERSION) tsc --noEmit -p tsconfig.json

ts-list: ## List files included by tsconfig (useful when debugging include/exclude)
	npx --yes -p typescript@$(TS_VERSION) tsc --listFilesOnly -p tsconfig.json

ts-show: ## Show effective tsconfig compiler options
	npx --yes -p typescript@$(TS_VERSION) tsc --showConfig -p tsconfig.json
