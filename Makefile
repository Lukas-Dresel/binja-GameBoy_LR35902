.PHONY: error install uninstall

ifndef BN_PLUGINS
	$(error BN_PLUGINS is undefined)
	@exit -1
endif

error:
	@echo "available targets: install, uninstall"
	@exit -1

install:
	@if [ -L "$(BN_PLUGINS)/LR35902" ]; then \
		echo "already installed"; \
	else \
		echo "installing"; \
		ln -s "$(PWD)" "$(BN_PLUGINS)/LR35902"; \
	fi

uninstall:
	@if [ -L "$(BN_PLUGINS)/LR35902" ]; then \
		echo "uninstalling"; \
		rm "$(BN_PLUGINS)/LR35902"; \
	else \
		echo "not installed"; \
	fi

