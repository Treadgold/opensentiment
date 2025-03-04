-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS citus;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search capabilities
CREATE EXTENSION IF NOT EXISTS hstore;   -- For flexible key-value storage

-- Add worker nodes
SELECT citus_add_node('db-worker-1', 5432);
SELECT citus_add_node('db-worker-2', 5432);

-- Reference Tables (replicated across all nodes)
CREATE TABLE IF NOT EXISTS political_ideologies (
    ideology_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_ideology_id INTEGER REFERENCES political_ideologies(ideology_id),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
SELECT create_reference_table('political_ideologies');

CREATE TABLE IF NOT EXISTS bias_dimensions (
    dimension_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    scale_min INTEGER DEFAULT 0,
    scale_max INTEGER DEFAULT 100,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
SELECT create_reference_table('bias_dimensions');

CREATE TABLE IF NOT EXISTS content_types (
    type_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_type_id INTEGER REFERENCES content_types(type_id),
    metadata_schema JSONB,  -- Define expected metadata fields for this content type
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
SELECT create_reference_table('content_types');

-- Distributed Tables
CREATE TABLE IF NOT EXISTS content_sources (
    source_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    type VARCHAR(50),
    country_code CHAR(2),
    language_code VARCHAR(10),
    verified BOOLEAN DEFAULT FALSE,
    baseline_bias_data JSONB,  -- Historical/known bias information
    metadata JSONB,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
SELECT create_distributed_table('content_sources', 'source_id');

CREATE TABLE IF NOT EXISTS content_items (
    item_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES content_sources(source_id),
    content_type_id INTEGER REFERENCES content_types(type_id),
    batch_id BIGINT,  -- For batch processing
    url TEXT,
    title TEXT,
    content TEXT,
    author VARCHAR(255),
    published_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,  -- Type-specific metadata (structure defined in content_types)
    embedding VECTOR(384),  -- For semantic search and clustering
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
SELECT create_distributed_table('content_items', 'batch_id');

CREATE TABLE IF NOT EXISTS analysis_results (
    result_id BIGSERIAL PRIMARY KEY,
    item_id BIGINT REFERENCES content_items(item_id),
    batch_id BIGINT,  -- Same as content_items batch_id for co-location
    
    -- Overall political bias scores
    bias_scores JSONB,  -- Scores for different bias dimensions
    confidence_scores JSONB,  -- Confidence levels for each score
    
    -- Detailed analysis
    ideology_classifications JSONB,  -- Detected ideological leanings
    narrative_markers JSONB,  -- Identified narrative patterns
    topic_analysis JSONB,  -- Topic modeling results
    entity_sentiment JSONB,  -- Entity-level sentiment analysis
    rhetoric_analysis JSONB,  -- Analysis of rhetorical devices
    
    -- Contextual factors
    temporal_context JSONB,  -- Time-based factors
    geographic_context JSONB,  -- Location-based factors
    
    -- Model metadata
    model_version VARCHAR(50),
    analysis_version VARCHAR(50),
    processing_metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
SELECT create_distributed_table('analysis_results', 'batch_id');

-- Create table for tracking content relationships
CREATE TABLE IF NOT EXISTS content_relationships (
    relationship_id BIGSERIAL PRIMARY KEY,
    source_item_id BIGINT REFERENCES content_items(item_id),
    target_item_id BIGINT REFERENCES content_items(item_id),
    relationship_type VARCHAR(50),  -- e.g., 'reply', 'quote', 'share'
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
SELECT create_distributed_table('content_relationships', 'source_item_id');

-- Create table for temporal analysis and trends
CREATE TABLE IF NOT EXISTS temporal_trends (
    trend_id BIGSERIAL PRIMARY KEY,
    time_bucket TIMESTAMP WITH TIME ZONE,
    dimension_id INTEGER REFERENCES bias_dimensions(dimension_id),
    aggregation_level VARCHAR(50),  -- e.g., 'hourly', 'daily', 'weekly'
    metrics JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
SELECT create_distributed_table('temporal_trends', 'trend_id');

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_content_items_published_at ON content_items(published_at);
CREATE INDEX IF NOT EXISTS idx_content_items_content_type ON content_items(content_type_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at ON analysis_results(created_at);
CREATE INDEX IF NOT EXISTS idx_content_sources_domain ON content_sources(domain);
CREATE INDEX IF NOT EXISTS idx_content_items_url ON content_items USING gin (url gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_content_items_title ON content_items USING gin (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_content_items_embedding ON content_items USING ivfflat (embedding vector_cosine_ops);

-- Permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO current_user;

-- Insert some initial content types
INSERT INTO content_types (name, description, metadata_schema) VALUES
('news_article', 'News articles from recognized media outlets', 
 '{"required": ["headline", "author", "publication_date"], "optional": ["section", "category"]}'),
('social_post', 'Social media posts', 
 '{"required": ["platform", "post_type"], "optional": ["hashtags", "mentions"]}'),
('comment', 'Comments on articles or posts', 
 '{"required": ["parent_type", "parent_id"], "optional": ["thread_position"]}'),
('video_content', 'Video content including streams and clips', 
 '{"required": ["duration", "platform"], "optional": ["transcript"]}'),
('blog_post', 'Blog posts and personal articles', 
 '{"required": ["author", "blog_name"], "optional": ["category"]}'),
('podcast_episode', 'Podcast episodes', 
 '{"required": ["show_name", "episode_number"], "optional": ["transcript"]}'),
('academic_paper', 'Academic or research papers', 
 '{"required": ["authors", "institution"], "optional": ["doi", "citations"]}');

-- Insert initial bias dimensions
INSERT INTO bias_dimensions (name, description) VALUES
('political_spectrum', 'Traditional left-right political spectrum'),
('economic_policy', 'Economic policy preferences'),
('social_policy', 'Social policy preferences'),
('institutional_trust', 'Trust in institutions'),
('globalism_nationalism', 'Global vs nationalist orientation'),
('authority_liberty', 'Authority vs individual liberty preference'),
('traditional_progressive', 'Traditional vs progressive values'),
('environmental_policy', 'Environmental policy stance'); 