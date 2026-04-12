/*
Optional demo seed
- Inserts a compact set of validation log events for the Logs page demo.
- Run this after 20260412_priority5_validation_logs.sql.
*/

IF OBJECT_ID('dbo.validation_logs', 'U') IS NULL
BEGIN
    THROW 50010, 'validation_logs table does not exist. Run the migration first.', 1;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM dbo.validation_logs
    WHERE request_id = 'demo-logs-seed'
)
BEGIN
    INSERT INTO dbo.validation_logs
    (
        severity,
        event_type,
        message,
        source_module,
        validation_id,
        correlation_id,
        request_id,
        run_id,
        rule_code,
        entity_id,
        record_id,
        table_name,
        column_name,
        validation_context,
        validation_status,
        duration_ms,
        exception_type,
        stack_trace,
        input_summary,
        output_summary,
        payload_json
    )
    VALUES
    (
        'INFO',
        'validation.started',
        'Validation batch started.',
        'seed.demo',
        '11111111-1111-1111-1111-111111111111',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        'demo-logs-seed',
        9001,
        'NOT_NULL',
        'customer-1001',
        'customer-1001',
        'Customers',
        'Email',
        'Customers.Email',
        'STARTED',
        0,
        NULL,
        NULL,
        '{"records":120}',
        NULL,
        '{"phase":"started"}'
    ),
    (
        'WARNING',
        'validation.rule.skipped',
        'Skipped optional phone check because source value is blank.',
        'seed.demo',
        '11111111-1111-1111-1111-111111111111',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        'demo-logs-seed',
        9001,
        'is_phone_us',
        'customer-1002',
        'customer-1002',
        'Customers',
        'Phone',
        'Customers.Phone',
        NULL,
        37,
        NULL,
        NULL,
        '{"optional_rule":true}',
        NULL,
        '{"reason":"blank"}'
    ),
    (
        'ERROR',
        'validation.failed',
        'Validation failed for Customers.Email using NOT_NULL.',
        'seed.demo',
        '11111111-1111-1111-1111-111111111111',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        'demo-logs-seed',
        9002,
        'NOT_NULL',
        'customer-1003',
        'customer-1003',
        'Customers',
        'Email',
        'Customers.Email',
        'FAILED',
        245,
        'ValueError',
        'Traceback line 1; Traceback line 2',
        '{"records":120}',
        '{"errors":3}',
        '{"failed_records":3}'
    ),
    (
        'CRITICAL',
        'validation.failed',
        'Validation engine unavailable during dependency outage.',
        'seed.demo',
        '22222222-2222-2222-2222-222222222222',
        'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
        'demo-logs-seed',
        9003,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        'all-validations',
        'FAILED',
        820,
        'ConnectionError',
        'Primary database timeout',
        '{"dependency":"sqlserver"}',
        '{"status":"failed"}',
        '{"impact":"system-wide"}'
    ),
    (
        'INFO',
        'validation.completed',
        'Validation batch completed.',
        'seed.demo',
        '33333333-3333-3333-3333-333333333333',
        'cccccccc-cccc-cccc-cccc-cccccccccccc',
        'demo-logs-seed',
        9004,
        'HasLength',
        'order-2001',
        'order-2001',
        'Orders',
        'OrderCode',
        'Orders.OrderCode',
        'COMPLETED',
        154,
        NULL,
        NULL,
        '{"records":42}',
        '{"errors":0}',
        '{"status":"ok"}'
    );
END;
GO
