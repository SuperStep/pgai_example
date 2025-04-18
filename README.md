PGAI Docs
https://github.com/timescale/pgai/tree/released/docs

Download repo and extract classes and methods into 
```bash
chmod +x rag_git_indexer.py
./rag_git_indexer.py [repo_url] --output out.jsonl
```

Run postgres with vectorizer
```bash
docker compose up -d
```

Run ollama locally or add to docker compose - ai.ollama_host can be changed in [docker-compose.yml](docker-compose.yml)

Upload data to DB
```bash
chmod +x upload_data.py
upload_data.py rag_dataset_with_methods.jsonl
```

Setup RAG in database see [scripts.sql](scripts.sql)

Run frontend for demo
```bash
streamlit run frontend.py
```
