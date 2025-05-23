CREATE EXTENSION IF NOT EXISTS ai CASCADE;

CREATE TABLE codebase (
    id      INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    path     TEXT,
    file_name TEXT,
    file_extension TEXT,
    file_size BIGINT,
    method_signature TEXT,
    chunk_type TEXT,
    method_index INTEGER,
    content   TEXT
);

SELECT count(1) FROM codebase;

-- Create vectorizer
SELECT ai.create_vectorizer(
            'public.codebase'::regclass,
            destination => 'codebase_contents_embeddings',
            embedding => ai.embedding_ollama('nomic-embed-text', 768),
            chunking => ai.chunking_recursive_character_text_splitter('content'),
            formatting => ai.formatting_python_template('$path, $chunk_type, $method_index, $file_name, $file_extension, $method_signature, $content')
);

-- Check vectorizer status
select * from ai.vectorizer_status;

-- ASK

SELECT 
   chunk,
   embedding <=> ai.ollama_embed('nomic-embed-text', 'How to create unit and suit using REST API?') as distance
FROM codebase_contents_embeddings
ORDER BY distance
LIMIT 10;



select count(1) from codebase_contents_embeddings LIMIT 4;


SELECT * 
FROM ai.openai_list_models()
ORDER BY created DESC
;


-- Perform semantic search
CREATE OR REPLACE FUNCTION find_rag_content(query_text TEXT)
RETURNS TABLE (path TEXT, chunk TEXT) AS $$
BEGIN
    RETURN QUERY SELECT ce.path, ce.chunk 
        FROM codebase_contents_embeddings ce
        ORDER BY embedding <=> ai.ollama_embed('nomic-embed-text', query_text) LIMIT 10;
END;
$$ LANGUAGE plpgsql;

SELECT path, chunk FROM find_rag_content('How to create feature toggle?')

-- Impact analysis using LLM
CREATE OR REPLACE FUNCTION query_impact(query_text TEXT)
RETURNS TEXT AS $$
DECLARE
    context_chunks TEXT;
    response TEXT;
BEGIN
    -- Perform similarity search to find relevant blog posts
    SELECT chunk INTO context_chunks
    FROM (
        SELECT path, chunk 
        FROM codebase_contents_embeddings
        ORDER BY embedding <=> ai.ollama_embed('nomic-embed-text', query_text) LIMIT 10
    ) AS relevant_posts;

    -- Generate a summary using model  Please answer the question using context from existing codebase.
    SELECT ai.ollama_generate(
        'qwen2.5-coder:14b',
        format('Context: %s\n\n %s', context_chunks, query_text)
    )->>'response' INTO response;

    RETURN translate_to_russian(response);
END;
$$ LANGUAGE plpgsql;

-- Translate any text from English to Russian using Ollama
CREATE OR REPLACE FUNCTION translate_to_russian(english_text TEXT)
RETURNS TEXT AS $$
DECLARE
    translated_text TEXT;
BEGIN
    -- Use Ollama to translate the text
    SELECT ai.ollama_generate(
        'qwen2.5-coder:14b',
        format('Translate the following English text to Russian (just result): %s', english_text)
    )->>'response' INTO translated_text;

    RETURN translated_text;
END;
$$ LANGUAGE plpgsql;


-- Russian question to database
CREATE OR REPLACE FUNCTION generate_rag_response(query_text TEXT)
RETURNS TEXT AS $$
DECLARE
    context_chunks TEXT;
    response TEXT;
BEGIN
    -- Perform similarity search to find relevant blog posts
    SELECT chunk INTO context_chunks
    FROM (
        SELECT path, chunk 
        FROM codebase_contents_embeddings
        ORDER BY embedding <=> ai.ollama_embed('nomic-embed-text', query_text) LIMIT 10
    ) AS relevant_posts;

    -- Generate a summary using model  Please answer the question using context from existing codebase.
    -- 
    SELECT ai.ollama_generate(
        'qwen2.5-coder:14b',
        format('Context: %s\n\nВопрос пользователя: %s\n\n Пожалуйста отвечай на вопрос используя предоставленную кодовую базу находя ответы в ней. Отвечай на русском', context_chunks, query_text)
    )->>'response' INTO response;

    RETURN response;
END;
$$ LANGUAGE plpgsql;


SELECT generate_rag_response('How to create space calling rest API?')


SELECT generate_rag_response('Как создать спейс, вызывая rest API?')