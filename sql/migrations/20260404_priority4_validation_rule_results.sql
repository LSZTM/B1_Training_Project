/*
Priority 4 migration
- Adds per-rule run result tracking table.
*/

IF OBJECT_ID('dbo.validation_rule_results', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.validation_rule_results
    (
        result_id       INT IDENTITY PRIMARY KEY,
        run_id          INT NOT NULL,
        table_name      NVARCHAR(128) NULL,
        column_name     NVARCHAR(128) NULL,
        rule_code       NVARCHAR(64) NULL,
        rows_scanned    INT NULL,
        pass_count      INT NULL,
        fail_count      INT NULL,
        pass_rate       DECIMAL(10,4) NULL,
        run_timestamp   DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_validation_rule_results_run_id
            FOREIGN KEY (run_id) REFERENCES dbo.validation_run_history(run_id)
    );

    CREATE INDEX IX_validation_rule_results_run_id
        ON dbo.validation_rule_results(run_id);
END;
GO
