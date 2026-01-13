-- Create database for Metabase's internal storage
-- This prevents the corrupted H2 database issues

CREATE DATABASE metabase_internal;

-- Grant privileges to the application user
GRANT ALL PRIVILEGES ON DATABASE metabase_internal TO expat_user;
