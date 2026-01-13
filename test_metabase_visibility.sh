#!/bin/bash
# Test if views are visible to Metabase

echo "================================================"
echo "Testing Database Views Visibility for Metabase"
echo "================================================"
echo ""

echo "1. Checking if views exist..."
docker exec -i expat_insurance_db psql -U expat_user -d expat_insurance -c "\dv"
echo ""

echo "2. Checking view details in information_schema..."
docker exec -i expat_insurance_db psql -U expat_user -d expat_insurance -c "
SELECT
    table_name,
    table_type,
    table_schema
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_type IN ('VIEW', 'BASE TABLE')
    AND table_name LIKE 'vw_%'
ORDER BY table_name;
"
echo ""

echo "3. Testing query access..."
docker exec -i expat_insurance_db psql -U expat_user -d expat_insurance -c "
SELECT 'vw_contracten_readable' as view_name, COUNT(*) as row_count
FROM vw_contracten_readable
UNION ALL
SELECT 'vw_verzekering_regio_landen_readable' as view_name, COUNT(*) as row_count
FROM vw_verzekering_regio_landen_readable;
"
echo ""

echo "4. Checking permissions..."
docker exec -i expat_insurance_db psql -U expat_user -d expat_insurance -c "
SELECT
    schemaname,
    viewname,
    viewowner,
    CASE
        WHEN has_table_privilege('expat_user', schemaname||'.'||viewname, 'SELECT')
        THEN '✓ Can SELECT'
        ELSE '✗ Cannot SELECT'
    END as permission_check
FROM pg_views
WHERE schemaname = 'public'
    AND viewname LIKE 'vw_%';
"
echo ""

echo "================================================"
echo "If all checks pass but Metabase doesn't show the views:"
echo "1. Try 'Discard saved field values' in Metabase Admin"
echo "2. Try restarting Metabase: docker restart expat_insurance_metabase"
echo "3. Consider using materialized views instead (see ALTERNATIVE_materialized_views_migration.py)"
echo "================================================"
