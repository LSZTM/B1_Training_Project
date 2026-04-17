IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.validation_schedules') AND type in (N'U'))
BEGIN
    CREATE TABLE dbo.validation_schedules (
        schedule_id INT IDENTITY(1,1) PRIMARY KEY,
        frequency NVARCHAR(50) NOT NULL, -- Daily, Weekly, Monthly
        scheduled_time TIME NOT NULL,
        target_tables NVARCHAR(MAX) NULL, -- JSON or comma-separated list
        is_active BIT DEFAULT 1,
        last_run_at DATETIME2 NULL,
        created_at DATETIME2 DEFAULT SYSUTCDATETIME()
    );
END
GO
