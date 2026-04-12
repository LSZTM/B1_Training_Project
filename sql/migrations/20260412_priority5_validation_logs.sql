/*
Priority 5 migration
- Adds structured validation logs for live observability.
- Normalizes severity with indexed severity ranks.
- Wraps the existing batch validation procedure with lifecycle logging.
*/

IF OBJECT_ID('dbo.validation_logs', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.validation_logs
    (
        log_id               BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        event_timestamp      DATETIME2(3) NOT NULL CONSTRAINT DF_validation_logs_event_timestamp DEFAULT SYSUTCDATETIME(),
        severity             NVARCHAR(16) NOT NULL,
        severity_rank        AS (
            CASE UPPER(severity)
                WHEN 'DEBUG' THEN 10
                WHEN 'INFO' THEN 20
                WHEN 'WARNING' THEN 30
                WHEN 'ERROR' THEN 40
                WHEN 'CRITICAL' THEN 50
                ELSE 20
            END
        ) PERSISTED,
        event_type           NVARCHAR(64) NOT NULL,
        message              NVARCHAR(4000) NOT NULL,
        source_module        NVARCHAR(256) NOT NULL,
        validation_id        UNIQUEIDENTIFIER NULL,
        correlation_id       UNIQUEIDENTIFIER NOT NULL,
        request_id           NVARCHAR(128) NULL,
        run_id               INT NULL,
        rule_id              INT NULL,
        rule_code            NVARCHAR(128) NULL,
        entity_id            NVARCHAR(128) NULL,
        record_id            NVARCHAR(128) NULL,
        table_name           NVARCHAR(128) NULL,
        column_name          NVARCHAR(128) NULL,
        validation_context   NVARCHAR(256) NULL,
        validation_status    NVARCHAR(32) NULL,
        duration_ms          INT NULL,
        exception_type       NVARCHAR(256) NULL,
        stack_trace          NVARCHAR(MAX) NULL,
        input_summary        NVARCHAR(MAX) NULL,
        output_summary       NVARCHAR(MAX) NULL,
        payload_json         NVARCHAR(MAX) NULL,
        created_at           DATETIME2(3) NOT NULL CONSTRAINT DF_validation_logs_created_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_validation_logs_severity CHECK (UPPER(severity) IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
        CONSTRAINT CK_validation_logs_status CHECK (validation_status IS NULL OR UPPER(validation_status) IN ('STARTED', 'PASSED', 'FAILED', 'COMPLETED'))
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_validation_logs_event_timestamp' AND object_id = OBJECT_ID('dbo.validation_logs'))
BEGIN
    CREATE INDEX IX_validation_logs_event_timestamp
        ON dbo.validation_logs(event_timestamp DESC, log_id DESC);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_validation_logs_severity_rank' AND object_id = OBJECT_ID('dbo.validation_logs'))
BEGIN
    CREATE INDEX IX_validation_logs_severity_rank
        ON dbo.validation_logs(severity_rank DESC, event_timestamp DESC)
        INCLUDE (severity, validation_status, validation_id, correlation_id, rule_code, duration_ms);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_validation_logs_validation_id' AND object_id = OBJECT_ID('dbo.validation_logs'))
BEGIN
    CREATE INDEX IX_validation_logs_validation_id
        ON dbo.validation_logs(validation_id, event_timestamp DESC)
        INCLUDE (severity, validation_status, correlation_id, rule_code, duration_ms);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_validation_logs_correlation_id' AND object_id = OBJECT_ID('dbo.validation_logs'))
BEGIN
    CREATE INDEX IX_validation_logs_correlation_id
        ON dbo.validation_logs(correlation_id, event_timestamp DESC)
        INCLUDE (severity, validation_status, validation_id, rule_code);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_validation_logs_rule_code' AND object_id = OBJECT_ID('dbo.validation_logs'))
BEGIN
    CREATE INDEX IX_validation_logs_rule_code
        ON dbo.validation_logs(rule_code, event_timestamp DESC)
        INCLUDE (severity, validation_status, validation_id, correlation_id, table_name, column_name);
END;
GO

CREATE OR ALTER PROCEDURE dbo.execute_all_validations_with_logging
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @validation_id UNIQUEIDENTIFIER = NEWID();
    DECLARE @correlation_id UNIQUEIDENTIFIER = NEWID();
    DECLARE @started_at DATETIME2(3) = SYSUTCDATETIME();
    DECLARE @before_max_run_id INT = ISNULL((SELECT MAX(run_id) FROM dbo.validation_run_history), 0);

    BEGIN TRY
        INSERT INTO dbo.validation_logs
        (
            severity,
            event_type,
            message,
            source_module,
            validation_id,
            correlation_id,
            validation_context,
            validation_status,
            payload_json
        )
        VALUES
        (
            'INFO',
            'validation.started',
            'Validation batch started.',
            'dbo.execute_all_validations_with_logging',
            @validation_id,
            @correlation_id,
            'all-validations',
            'STARTED',
            CONCAT(
                N'{"procedure":"dbo.execute_all_validations","started_at":"',
                CONVERT(NVARCHAR(33), @started_at, 127),
                N'"}'
            )
        );

        EXEC dbo.execute_all_validations;

        DECLARE @new_runs TABLE
        (
            run_id INT NOT NULL,
            table_name NVARCHAR(128) NULL,
            column_name NVARCHAR(128) NULL,
            rule_code NVARCHAR(64) NULL,
            total_records_scanned INT NULL,
            total_errors INT NULL,
            duration_ms INT NULL,
            status NVARCHAR(32) NULL,
            run_timestamp DATETIME NULL
        );

        INSERT INTO @new_runs
        (
            run_id,
            table_name,
            column_name,
            rule_code,
            total_records_scanned,
            total_errors,
            duration_ms,
            status,
            run_timestamp
        )
        SELECT
            run_id,
            table_name,
            column_name,
            rule_code,
            total_records_scanned,
            total_errors,
            duration_ms,
            status,
            run_timestamp
        FROM dbo.validation_run_history
        WHERE run_id > @before_max_run_id
        ORDER BY run_id ASC;

        INSERT INTO dbo.validation_logs
        (
            severity,
            event_type,
            message,
            source_module,
            validation_id,
            correlation_id,
            run_id,
            rule_code,
            table_name,
            column_name,
            validation_context,
            validation_status,
            duration_ms,
            output_summary,
            payload_json
        )
        SELECT
            CASE
                WHEN UPPER(ISNULL(status, '')) = 'FAILED' OR ISNULL(total_errors, 0) > 0 THEN 'ERROR'
                ELSE 'INFO'
            END AS severity,
            CASE
                WHEN UPPER(ISNULL(status, '')) = 'FAILED' OR ISNULL(total_errors, 0) > 0 THEN 'validation.failed'
                ELSE 'validation.passed'
            END AS event_type,
            CASE
                WHEN UPPER(ISNULL(status, '')) = 'FAILED' OR ISNULL(total_errors, 0) > 0 THEN
                    CONCAT(
                        N'Validation failed for ',
                        ISNULL(table_name, N'(unknown-table)'),
                        N'.',
                        ISNULL(column_name, N'(unknown-column)'),
                        N' using ',
                        ISNULL(rule_code, N'(unknown-rule)'),
                        N'.'
                    )
                ELSE
                    CONCAT(
                        N'Validation passed for ',
                        ISNULL(table_name, N'(unknown-table)'),
                        N'.',
                        ISNULL(column_name, N'(unknown-column)'),
                        N' using ',
                        ISNULL(rule_code, N'(unknown-rule)'),
                        N'.'
                    )
            END AS message,
            'dbo.execute_all_validations_with_logging' AS source_module,
            @validation_id AS validation_id,
            @correlation_id AS correlation_id,
            run_id,
            rule_code,
            table_name,
            column_name,
            CONCAT(
                ISNULL(table_name, N''),
                CASE WHEN table_name IS NOT NULL AND column_name IS NOT NULL THEN N'.' ELSE N'' END,
                ISNULL(column_name, N'')
            ) AS validation_context,
            CASE
                WHEN UPPER(ISNULL(status, '')) = 'FAILED' OR ISNULL(total_errors, 0) > 0 THEN 'FAILED'
                ELSE 'PASSED'
            END AS validation_status,
            duration_ms,
            CONCAT(
                N'{"run_id":', CAST(run_id AS NVARCHAR(20)),
                N',"records_scanned":', CAST(ISNULL(total_records_scanned, 0) AS NVARCHAR(20)),
                N',"total_errors":', CAST(ISNULL(total_errors, 0) AS NVARCHAR(20)),
                N',"duration_ms":', CAST(ISNULL(duration_ms, 0) AS NVARCHAR(20)),
                N',"status":"', ISNULL(status, N'UNKNOWN'), N'"}'
            ) AS output_summary,
            CONCAT(
                N'{"run_timestamp":"', CONVERT(NVARCHAR(33), run_timestamp, 127),
                N'","rule_code":"', ISNULL(rule_code, N''), N'"}'
            ) AS payload_json
        FROM @new_runs;

        DECLARE @run_count INT = (SELECT COUNT(*) FROM @new_runs);
        DECLARE @failed_runs INT = (
            SELECT COUNT(*)
            FROM @new_runs
            WHERE UPPER(ISNULL(status, '')) = 'FAILED' OR ISNULL(total_errors, 0) > 0
        );
        DECLARE @records_scanned INT = (SELECT ISNULL(SUM(ISNULL(total_records_scanned, 0)), 0) FROM @new_runs);
        DECLARE @total_errors INT = (SELECT ISNULL(SUM(ISNULL(total_errors, 0)), 0) FROM @new_runs);
        DECLARE @avg_duration_ms INT = (
            SELECT ISNULL(CAST(AVG(CAST(ISNULL(duration_ms, 0) AS FLOAT)) AS INT), 0)
            FROM @new_runs
        );

        INSERT INTO dbo.validation_logs
        (
            severity,
            event_type,
            message,
            source_module,
            validation_id,
            correlation_id,
            validation_context,
            validation_status,
            duration_ms,
            output_summary,
            payload_json
        )
        VALUES
        (
            'INFO',
            'validation.completed',
            CASE
                WHEN @failed_runs > 0 THEN CONCAT(N'Validation batch completed with ', @failed_runs, N' failed validations.')
                ELSE N'Validation batch completed without failed validations.'
            END,
            'dbo.execute_all_validations_with_logging',
            @validation_id,
            @correlation_id,
            'all-validations',
            'COMPLETED',
            @avg_duration_ms,
            CONCAT(
                N'{"run_count":', CAST(@run_count AS NVARCHAR(20)),
                N',"failed_runs":', CAST(@failed_runs AS NVARCHAR(20)),
                N',"records_scanned":', CAST(@records_scanned AS NVARCHAR(20)),
                N',"total_errors":', CAST(@total_errors AS NVARCHAR(20)),
                N',"avg_duration_ms":', CAST(@avg_duration_ms AS NVARCHAR(20)),
                N'}'
            ),
            CONCAT(
                N'{"started_at":"', CONVERT(NVARCHAR(33), @started_at, 127),
                N'","completed_at":"', CONVERT(NVARCHAR(33), SYSUTCDATETIME(), 127),
                N'"}'
            )
        );

        SELECT
            CAST(@validation_id AS VARCHAR(36)) AS validation_id,
            CAST(@correlation_id AS VARCHAR(36)) AS correlation_id,
            (SELECT MAX(run_id) FROM @new_runs) AS run_id,
            @run_count AS run_count,
            @failed_runs AS failed_runs,
            @records_scanned AS records_scanned,
            @total_errors AS total_errors,
            @avg_duration_ms AS duration_ms,
            'COMPLETED' AS status;
    END TRY
    BEGIN CATCH
        INSERT INTO dbo.validation_logs
        (
            severity,
            event_type,
            message,
            source_module,
            validation_id,
            correlation_id,
            validation_context,
            validation_status,
            exception_type,
            stack_trace,
            payload_json
        )
        VALUES
        (
            'ERROR',
            'validation.failed',
            ERROR_MESSAGE(),
            'dbo.execute_all_validations_with_logging',
            @validation_id,
            @correlation_id,
            'all-validations',
            'FAILED',
            CONCAT(N'SQL_', ERROR_NUMBER()),
            CONCAT(
                N'Procedure=', ISNULL(ERROR_PROCEDURE(), N'(dynamic)'),
                N'; Line=', ERROR_LINE(),
                N'; Message=', ERROR_MESSAGE()
            ),
            CONCAT(
                N'{"error_number":', ERROR_NUMBER(),
                N',"error_state":', ERROR_STATE(),
                N',"error_severity":', ERROR_SEVERITY(),
                N'}'
            )
        );

        THROW;
    END CATCH
END;
GO
