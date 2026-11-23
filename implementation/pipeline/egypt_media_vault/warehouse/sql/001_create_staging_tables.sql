/* =========================================================
   EGYPT-MEDIA-VAULT
   STAGING LAYER
   SQL Server / Azure SQL
   ========================================================= */

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


/* =========================================================
   1. RAW ARTICLES
   Grain: One collected article snapshot per pipeline run.
   Raw payload fields are immutable after insertion.
   Processing metadata may be updated.
   ========================================================= */

IF OBJECT_ID(N'dbo.raw_articles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.raw_articles
    (
        staging_record_id BIGINT IDENTITY(1,1) NOT NULL,

        -- Pipeline and source identifiers (soft references)
        run_id NVARCHAR(100) NOT NULL,
        source_id NVARCHAR(100) NOT NULL,

        -- First landing timestamp in SQL staging
        ingestion_timestamp DATETIME2(3) NOT NULL
            CONSTRAINT DF_raw_articles_ingestion_timestamp
            DEFAULT SYSUTCDATETIME(),

        -- Original collected values
        raw_title NVARCHAR(1000) NULL,
        raw_source_name NVARCHAR(255) NULL,
        original_url NVARCHAR(2048) NULL,
        canonical_url NVARCHAR(2048) NULL,

        raw_publication_text NVARCHAR(500) NULL,
        raw_category_label NVARCHAR(255) NULL,
        raw_description NVARCHAR(MAX) NULL,
        raw_content NVARCHAR(MAX) NULL,
        raw_author NVARCHAR(500) NULL,
        raw_update_text NVARCHAR(500) NULL,

        -- Article media
        -- Original image URL collected from the source.
        image_url NVARCHAR(2048) NULL,

        -- Hashes and fingerprints
        canonical_url_hash CHAR(64) NULL,
        title_hash CHAR(64) NULL,
        content_fingerprint CHAR(64) NULL,

        -- Standardized values
        publication_timestamp DATETIME2(3) NULL,
        timestamp_validity NVARCHAR(20) NOT NULL
            CONSTRAINT DF_raw_articles_timestamp_validity
            DEFAULT N'Unknown',

        standardized_source_name NVARCHAR(255) NULL,
        standardized_category_name NVARCHAR(255) NULL,

        -- Business indicators
        is_syndicated BIT NOT NULL
            CONSTRAINT DF_raw_articles_is_syndicated
            DEFAULT 0,

        -- Processing metadata
        processing_status NVARCHAR(30) NOT NULL
            CONSTRAINT DF_raw_articles_processing_status
            DEFAULT N'Pending',

        article_id NVARCHAR(100) NULL,

        CONSTRAINT PK_raw_articles
            PRIMARY KEY CLUSTERED (staging_record_id),

        CONSTRAINT CK_raw_articles_timestamp_validity
            CHECK (
                timestamp_validity IN
                (N'Valid', N'Invalid', N'Unknown')
            ),

        CONSTRAINT CK_raw_articles_processing_status
            CHECK (
                processing_status IN
                (
                    N'Pending',
                    N'Validated',
                    N'Rejected',
                    N'Normalized',
                    N'Duplicate',
                    N'Updated',
                    N'Stored',
                    N'Failed'
                )
            )
    );
END;
GO


/* =========================================================
   1.1 ADD IMAGE URL TO EXISTING RAW ARTICLES TABLE
   ========================================================= */

IF OBJECT_ID(N'dbo.raw_articles', N'U') IS NULL
BEGIN
    THROW 50001,
        'dbo.raw_articles does not exist.',
        1;
END;
GO


IF COL_LENGTH(N'dbo.raw_articles', N'image_url') IS NULL
BEGIN
    ALTER TABLE dbo.raw_articles
    ADD image_url NVARCHAR(2048) NULL;

    PRINT N'Column image_url added successfully to dbo.raw_articles.';
END
ELSE
BEGIN
    PRINT N'Column image_url already exists. No change required.';
END;
GO


/* =========================================================
   2. RAW ARTICLE ISSUES
   Grain: One issue detected for one staging record.
   Stores validation errors and non-rejecting warnings.
   ========================================================= */

IF OBJECT_ID(N'dbo.raw_article_issues', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.raw_article_issues
    (
        staging_record_id BIGINT NOT NULL,
        issue_seq INT NOT NULL,

        issue_type NVARCHAR(100) NOT NULL,
        field_name NVARCHAR(100) NOT NULL,
        issue_description NVARCHAR(2000) NOT NULL,

        is_rejecting BIT NOT NULL
            CONSTRAINT DF_raw_article_issues_is_rejecting
            DEFAULT 0,

        detected_at DATETIME2(3) NOT NULL
            CONSTRAINT DF_raw_article_issues_detected_at
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_raw_article_issues
            PRIMARY KEY CLUSTERED
            (
                staging_record_id,
                issue_seq
            ),

        CONSTRAINT FK_raw_article_issues_raw_articles
            FOREIGN KEY (staging_record_id)
            REFERENCES dbo.raw_articles (staging_record_id)
    );
END;
GO


/* =========================================================
   3. INDEXES
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_raw_articles_run_source'
      AND object_id = OBJECT_ID(N'dbo.raw_articles')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_raw_articles_run_source
    ON dbo.raw_articles (run_id, source_id);
END;
GO


IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_raw_articles_source_ingestion'
      AND object_id = OBJECT_ID(N'dbo.raw_articles')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_raw_articles_source_ingestion
    ON dbo.raw_articles (source_id, ingestion_timestamp);
END;
GO


IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_raw_articles_canonical_hash'
      AND object_id = OBJECT_ID(N'dbo.raw_articles')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_raw_articles_canonical_hash
    ON dbo.raw_articles (source_id, canonical_url_hash)
    WHERE canonical_url_hash IS NOT NULL;
END;
GO


IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_raw_articles_content_fingerprint'
      AND object_id = OBJECT_ID(N'dbo.raw_articles')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_raw_articles_content_fingerprint
    ON dbo.raw_articles (source_id, content_fingerprint)
    WHERE content_fingerprint IS NOT NULL;
END;
GO


IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_raw_article_issues_rejecting'
      AND object_id = OBJECT_ID(N'dbo.raw_article_issues')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_raw_article_issues_rejecting
    ON dbo.raw_article_issues (is_rejecting, staging_record_id);
END;
GO


/* =========================================================
   4. VERIFICATION
   ========================================================= */

SELECT
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns AS c
INNER JOIN sys.types AS t
    ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID(N'dbo.raw_articles')
  AND c.name = N'image_url';
GO


PRINT N'Staging tables, image_url column, and indexes are ready.';
GO