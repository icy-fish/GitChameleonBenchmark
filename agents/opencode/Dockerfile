FROM gitchameleon-bench:1.1

ENV PATH="/root/.local/bin:/root/.opencode/bin:${PATH}"

RUN curl -fsSL https://opencode.ai/install | bash && \
    if [ -x /root/.local/bin/opencode ]; then \
        ln -sf /root/.local/bin/opencode /usr/local/bin/opencode; \
    elif [ -x /root/.opencode/bin/opencode ]; then \
        ln -sf /root/.opencode/bin/opencode /usr/local/bin/opencode; \
    elif command -v opencode >/dev/null 2>&1; then \
        ln -sf "$(command -v opencode)" /usr/local/bin/opencode; \
    else \
        echo "opencode binary not found after installation" >&2; \
        exit 1; \
    fi
