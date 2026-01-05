-- Receipt Metadata Table
-- Stores AI model metadata and parsing information for receipts

CREATE TABLE IF NOT EXISTS `receipt_metadata` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `expense_id` bigint unsigned NOT NULL,
  `model_name` varchar(100) DEFAULT NULL COMMENT 'AI model used (e.g., gemini-2.5-flash)',
  `model_provider` varchar(100) DEFAULT NULL COMMENT 'Provider (e.g., Google)',
  `engine_version` varchar(50) DEFAULT NULL COMMENT 'Receipt engine version',
  `parsing_confidence` decimal(5,4) DEFAULT NULL COMMENT 'Overall confidence score 0.0-1.0',
  `field_confidence` JSON DEFAULT NULL COMMENT 'Per-field confidence scores',
  `raw_response` JSON DEFAULT NULL COMMENT 'Full AI response for debugging',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_receipt_metadata_expense` (`expense_id`),
  CONSTRAINT `fk_receipt_metadata_expense` FOREIGN KEY (`expense_id`) REFERENCES `expenses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
COMMENT='Stores AI parsing metadata for receipt scanning';

-- Index for quick lookups by expense
CREATE INDEX `idx_receipt_metadata_expense` ON `receipt_metadata` (`expense_id`);
