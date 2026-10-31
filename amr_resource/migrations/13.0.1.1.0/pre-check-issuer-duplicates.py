"""Stop upgrades before schema initialization if issuer data is ambiguous."""


def migrate(cr, version):
    cr.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
            JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
            JOIN pg_catalog.pg_namespace tn ON tn.oid = t.typnamespace
            JOIN pg_catalog.pg_collation coll ON coll.oid = a.attcollation
            WHERE n.nspname = 'public'
              AND c.relname = 'oidc_issuer_register'
              AND c.relkind = 'r'
              AND a.attname = 'issuer' AND a.attnum > 0 AND NOT a.attisdropped
              AND tn.nspname = 'pg_catalog' AND t.typname IN ('text', 'varchar')
              AND coll.collisdeterministic
              AND pg_catalog.current_setting('server_encoding') = 'UTF8'
              -- A unique index may override the column collation or operator
              -- class. Unknown expression indexes also require review.
              AND NOT EXISTS (
                  SELECT 1 FROM pg_catalog.pg_index i
                  WHERE i.indrelid = c.oid AND i.indisunique
                    AND (i.indexprs IS NOT NULL OR (
                        a.attnum = ANY(i.indkey) AND (
                            EXISTS (
                                SELECT 1 FROM pg_catalog.unnest(i.indcollation) AS ic(oid)
                                JOIN pg_catalog.pg_collation co ON co.oid = ic.oid
                                WHERE NOT co.collisdeterministic
                            ) OR EXISTS (
                                SELECT 1 FROM pg_catalog.unnest(i.indclass) AS op(oid)
                                JOIN pg_catalog.pg_opclass oc ON oc.oid = op.oid
                                WHERE NOT oc.opcdefault
                            )
                        )
                    ))
              )
        )
    """)
    if not cr.fetchone()[0]:
        raise RuntimeError('Issuer registry schema unavailable; upgrade stopped')
    cr.execute("""
        SELECT EXISTS (
            SELECT 1 FROM public.oidc_issuer_register
            WHERE issuer IS NOT NULL
            GROUP BY issuer HAVING COUNT(*) > 1
        )
    """)
    if cr.fetchone()[0]:
        raise RuntimeError('Duplicate issuer registry entries; upgrade stopped')
    # Match the nonempty / ASCII-control restrictions of _exact_string without
    # putting stored issuer values into diagnostics.
    cr.execute("""
        SELECT EXISTS (
            SELECT 1 FROM public.oidc_issuer_register AS r
            WHERE r.issuer IS NULL OR r.issuer = '' OR EXISTS (
                SELECT 1 FROM generate_series(1, char_length(r.issuer)) AS pos(n)
                WHERE ascii(substr(r.issuer, pos.n, 1)) < 33
                   OR ascii(substr(r.issuer, pos.n, 1)) = 127
            )
        )
    """)
    if cr.fetchone()[0]:
        raise RuntimeError('Invalid issuer registry entries; upgrade stopped')
