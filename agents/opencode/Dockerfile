FROM gitchameleon-bench:1.1

SHELL ["/bin/bash", "-lc"]

ENV NVM_DIR="/root/.nvm"
ENV PATH="/root/.local/bin:/root/.opencode/bin:${PATH}"

RUN mkdir -p "${NVM_DIR}" && \
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash && \
    source "${NVM_DIR}/nvm.sh" && \
    nvm install node && \
    nvm alias default node && \
    NODE_VERSION="$(nvm version default)" && \
    ln -sf "${NVM_DIR}/versions/node/${NODE_VERSION}/bin/node" /usr/local/bin/node && \
    ln -sf "${NVM_DIR}/versions/node/${NODE_VERSION}/bin/npm" /usr/local/bin/npm && \
    ln -sf "${NVM_DIR}/versions/node/${NODE_VERSION}/bin/npx" /usr/local/bin/npx && \
    curl -fsSL https://opencode.ai/install | bash && \
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

ENTRYPOINT []
