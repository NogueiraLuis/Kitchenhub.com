FROM ollama/ollama

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 11434

ENTRYPOINT ["/docker-entrypoint.sh"]