-- MySQL dump 10.13  Distrib 8.0.43, for Linux (x86_64)
--
-- Host: localhost    Database: nonprofit_finance
-- ------------------------------------------------------
-- Server version	8.0.43-0ubuntu0.24.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `account_info`
--

DROP TABLE IF EXISTS `account_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account_info` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `org_id` bigint unsigned NOT NULL,
  `account_number` varchar(50) NOT NULL,
  `account_type` varchar(100) DEFAULT NULL,
  `bank_name` varchar(100) DEFAULT NULL,
  `statement_start_date` date DEFAULT NULL,
  `statement_end_date` date DEFAULT NULL,
  `import_batch_id` bigint unsigned DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_account_org_batch` (`org_id`,`account_number`,`import_batch_id`),
  KEY `idx_account_info_org` (`org_id`),
  KEY `idx_account_info_account` (`account_number`),
  KEY `idx_account_info_bank` (`bank_name`),
  KEY `idx_account_info_batch` (`import_batch_id`),
  CONSTRAINT `account_info_ibfk_1` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `account_info_ibfk_2` FOREIGN KEY (`import_batch_id`) REFERENCES `import_batches` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `account_info`
--

LOCK TABLES `account_info` WRITE;
/*!40000 ALTER TABLE `account_info` DISABLE KEYS */;
INSERT INTO `account_info` VALUES (2,1,'7735938','53 MOMENTUM CHECKING','Fifth Third Bank','2025-05-22','2025-06-20',2,'2025-09-29 19:02:57','2025-09-29 19:02:57');
/*!40000 ALTER TABLE `account_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `parent_id` bigint unsigned DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `kind` enum('EXPENSE','INCOME') NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `parent_id` (`parent_id`),
  CONSTRAINT `categories_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=351 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,NULL,'Church','EXPENSE',1),(2,NULL,'Housing','EXPENSE',1),(100,1,'Facility Payment','EXPENSE',1),(110,1,'Facility Upkeep','EXPENSE',1),(111,110,'Trash','EXPENSE',1),(112,110,'Furnishings','EXPENSE',1),(113,110,'Tools','EXPENSE',1),(114,110,'Cleaning','EXPENSE',1),(115,110,'Other','EXPENSE',1),(120,1,'Utilities','EXPENSE',1),(121,120,'Church Gas Bill','EXPENSE',1),(122,120,'Church Water Bill','EXPENSE',1),(123,120,'Church Electric Bill','EXPENSE',1),(124,120,'Church Phone/Internet Bill','EXPENSE',1),(125,120,'Other','EXPENSE',1),(130,1,'Food & Supplies','EXPENSE',1),(131,130,'Family Fare','EXPENSE',1),(132,130,'Meijer','EXPENSE',1),(133,130,'Restaurants (members/guests)','EXPENSE',1),(134,130,'Other','EXPENSE',1),(140,1,'Office','EXPENSE',1),(141,140,'Supplies','EXPENSE',1),(142,140,'Apple','EXPENSE',1),(143,140,'Amazon','EXPENSE',1),(144,140,'Postage','EXPENSE',1),(145,140,'Furnishings','EXPENSE',1),(146,140,'Other','EXPENSE',1),(150,1,'Education / Music / TV','EXPENSE',1),(151,150,'CDs','EXPENSE',1),(152,150,'DVDs','EXPENSE',1),(153,150,'Books','EXPENSE',1),(154,150,'Amazon','EXPENSE',1),(155,150,'Other','EXPENSE',1),(160,1,'Travel & Transportation','EXPENSE',1),(161,160,'Fuel','EXPENSE',1),(162,161,'RJ gas','EXPENSE',1),(163,161,'RM gas','EXPENSE',1),(164,160,'Vehicle Maintenance','EXPENSE',1),(165,164,'RJ wash/oil','EXPENSE',1),(166,164,'RM wash/oil','EXPENSE',1),(167,164,'Car repair (RJ)','EXPENSE',1),(168,164,'Car repair (RM)','EXPENSE',1),(169,160,'Vehicle Ownership','EXPENSE',1),(170,169,'Car payment (general)','EXPENSE',1),(171,169,'RJ Car Payment','EXPENSE',1),(172,169,'RM Car Payment','EXPENSE',1),(173,169,'License Tags','EXPENSE',1),(174,173,'RJ','EXPENSE',1),(175,173,'RM','EXPENSE',1),(176,173,'Other','EXPENSE',1),(177,160,'Trips','EXPENSE',1),(178,177,'Airfare','EXPENSE',1),(179,177,'Tolls','EXPENSE',1),(180,177,'AAA','EXPENSE',1),(181,177,'Hotels','EXPENSE',1),(182,177,'Ministry-related travel','EXPENSE',1),(183,160,'Other','EXPENSE',1),(190,1,'Gifts & Love Offerings','EXPENSE',1),(191,190,'EG Adams (work for River of Life)','EXPENSE',1),(192,190,'Individuals','EXPENSE',1),(193,192,'C Baker','EXPENSE',1),(194,192,'A Baker','EXPENSE',1),(195,192,'K Cook','EXPENSE',1),(196,192,'R Menninga','EXPENSE',1),(197,192,'J Menninga','EXPENSE',1),(198,192,'K Roark','EXPENSE',1),(199,192,'H Schneider','EXPENSE',1),(200,192,'R Exposito','EXPENSE',1),(201,192,'K Vander Vliet','EXPENSE',1),(202,192,'J McKay','EXPENSE',1),(203,192,'Sound (R Slawson)','EXPENSE',1),(204,192,'Guest Speakers','EXPENSE',1),(205,192,'Special occasions (name/occasion)','EXPENSE',1),(210,190,'Ministries & Organizations','EXPENSE',1),(211,210,'Chosen People','EXPENSE',1),(212,210,'Columbia Orphanage','EXPENSE',1),(213,210,'Segals in Israel','EXPENSE',1),(214,210,'Intercessors for America','EXPENSE',1),(215,210,'Samaritans Purse','EXPENSE',1),(216,210,'Mel Trotter','EXPENSE',1),(217,210,'Guiding Light','EXPENSE',1),(218,210,'Right to Life','EXPENSE',1),(219,210,'Johnsons in Dominican Republic','EXPENSE',1),(220,210,'Jews for Jesus','EXPENSE',1),(221,210,'Jewish Voice','EXPENSE',1),(222,210,'Salvation Army','EXPENSE',1),(223,210,'Other','EXPENSE',1),(230,1,'Insurance','EXPENSE',1),(231,230,'Building','EXPENSE',1),(232,230,'Boiler','EXPENSE',1),(233,230,'Vehicles','EXPENSE',1),(240,1,'Staff & Benefits','EXPENSE',1),(241,240,'Senior Pastors','EXPENSE',1),(242,241,'RJ — Priority Health (medical expenses)','EXPENSE',1),(243,241,'RM — Priority Health (medical expenses)','EXPENSE',1),(250,1,'Misc.','EXPENSE',1),(300,2,'Housing Payment','EXPENSE',1),(301,300,'House Payment','EXPENSE',1),(310,2,'Utilities','EXPENSE',1),(311,310,'Housing Gas Bill','EXPENSE',1),(312,310,'Housing Water Bill','EXPENSE',1),(313,310,'Housing Trash Bill','EXPENSE',1),(314,310,'Housing Electric Bill','EXPENSE',1),(320,2,'Taxes & Insurance','EXPENSE',1),(321,320,'House Taxes','EXPENSE',1),(322,320,'House Insurance','EXPENSE',1),(330,2,'Services','EXPENSE',1),(331,330,'Service Professor','EXPENSE',1),(340,2,'Upkeep','EXPENSE',1),(341,340,'Décor / Furnishings','EXPENSE',1),(342,340,'Tools','EXPENSE',1),(343,340,'Repair','EXPENSE',1),(344,340,'Outdoor & Lawn Care','EXPENSE',1),(345,340,'Other','EXPENSE',1),(350,2,'Misc.','EXPENSE',1);
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contacts`
--

DROP TABLE IF EXISTS `contacts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contacts` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(160) NOT NULL,
  `email` varchar(190) DEFAULT NULL,
  `phone` varchar(40) DEFAULT NULL,
  `contact_type` enum('PERSON','ORG') NOT NULL DEFAULT 'PERSON',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_contacts_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contacts`
--

LOCK TABLES `contacts` WRITE;
/*!40000 ALTER TABLE `contacts` DISABLE KEYS */;
INSERT INTO `contacts` VALUES (1,'John Donor','john.donor@example.org',NULL,'PERSON','2025-09-25 14:02:22'),(2,'City Print Shop','info@cityprint.example',NULL,'ORG','2025-09-25 14:02:22'),(3,'State Grant Office','grants@state.example',NULL,'ORG','2025-09-25 14:02:22'),(4,'Jane Volunteer',NULL,NULL,'PERSON','2025-09-25 14:02:22');
/*!40000 ALTER TABLE `contacts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `duplicate_flags`
--

DROP TABLE IF EXISTS `duplicate_flags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `duplicate_flags` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `transaction_id` bigint unsigned NOT NULL,
  `duplicate_transaction_id` bigint unsigned NOT NULL,
  `confidence_score` decimal(3,2) NOT NULL,
  `match_criteria` json NOT NULL,
  `status` enum('PENDING','CONFIRMED','REJECTED') NOT NULL DEFAULT 'PENDING',
  `reviewed_by` varchar(100) DEFAULT NULL,
  `reviewed_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_duplicate_pair` (`transaction_id`,`duplicate_transaction_id`),
  KEY `idx_duplicate_flags_transaction` (`transaction_id`),
  KEY `idx_duplicate_flags_duplicate` (`duplicate_transaction_id`),
  KEY `idx_duplicate_flags_status` (`status`),
  KEY `idx_duplicate_flags_confidence` (`confidence_score`),
  CONSTRAINT `duplicate_flags_ibfk_1` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `duplicate_flags_ibfk_2` FOREIGN KEY (`duplicate_transaction_id`) REFERENCES `transactions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `duplicate_flags`
--

LOCK TABLES `duplicate_flags` WRITE;
/*!40000 ALTER TABLE `duplicate_flags` DISABLE KEYS */;
/*!40000 ALTER TABLE `duplicate_flags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `expenses`
--

DROP TABLE IF EXISTS `expenses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expenses` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `org_id` bigint unsigned NOT NULL,
  `expense_date` date NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `category_id` bigint unsigned DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `paid_by_contact_id` bigint unsigned DEFAULT NULL,
  `method` enum('CASH','CARD','BANK','OTHER') NOT NULL DEFAULT 'OTHER',
  `receipt_url` varchar(500) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_expenses_paidby` (`paid_by_contact_id`),
  KEY `idx_expenses_org_date` (`org_id`,`expense_date`),
  KEY `idx_expenses_cat` (`category_id`),
  CONSTRAINT `fk_expenses_cat` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `fk_expenses_org` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`id`),
  CONSTRAINT `fk_expenses_paidby` FOREIGN KEY (`paid_by_contact_id`) REFERENCES `contacts` (`id`),
  CONSTRAINT `chk_expense_amount_pos` CHECK ((`amount` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expenses`
--

LOCK TABLES `expenses` WRITE;
/*!40000 ALTER TABLE `expenses` DISABLE KEYS */;
INSERT INTO `expenses` VALUES (1,1,'2025-07-15',145.75,1,'Flyers for summer fundraiser',2,'CARD','https://drive.example/receipt/001','2025-09-25 14:02:22'),(2,1,'2025-08-02',320.00,2,'Mileage to outreach event',NULL,'OTHER',NULL,'2025-09-25 14:02:22'),(3,1,'2025-08-18',89.50,4,'Printer ink + paper',NULL,'CARD',NULL,'2025-09-25 14:02:22'),(4,1,'2025-09-10',560.00,3,'Venue deposit for gala',NULL,'BANK',NULL,'2025-09-25 14:02:22'),(5,2,'2025-08-05',48.20,1,'Personal: office supplies',NULL,'CARD',NULL,'2025-09-25 14:02:22'),(6,2,'2025-09-01',120.00,2,'Personal: travel to meeting',NULL,'OTHER',NULL,'2025-09-25 14:02:22');
/*!40000 ALTER TABLE `expenses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `import_batches`
--

DROP TABLE IF EXISTS `import_batches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `import_batches` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `org_id` bigint unsigned NOT NULL,
  `filename` varchar(255) NOT NULL,
  `file_format` enum('CSV','PDF','OFX') NOT NULL,
  `import_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `total_transactions` int NOT NULL DEFAULT '0',
  `successful_imports` int NOT NULL DEFAULT '0',
  `failed_imports` int NOT NULL DEFAULT '0',
  `duplicate_count` int NOT NULL DEFAULT '0',
  `status` enum('PENDING','PROCESSING','COMPLETED','FAILED') NOT NULL DEFAULT 'PENDING',
  `error_log` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_import_batches_org` (`org_id`),
  KEY `idx_import_batches_status` (`status`),
  KEY `idx_import_batches_date` (`import_date`),
  CONSTRAINT `import_batches_ibfk_1` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `import_batches`
--

LOCK TABLES `import_batches` WRITE;
/*!40000 ALTER TABLE `import_batches` DISABLE KEYS */;
INSERT INTO `import_batches` VALUES (2,1,'fifth_third_personal_june.pdf','PDF','2025-09-29 19:02:57',48,48,0,0,'COMPLETED',NULL,'2025-09-29 19:02:57'),(3,1,'fifth_third_personal_may.pdf','PDF','2025-09-29 22:29:24',34,0,0,0,'FAILED','strptime() argument 1 must be str, not datetime.date','2025-09-29 22:29:24'),(4,1,'fifth_third_personal_may.pdf','PDF','2025-09-29 22:32:37',34,0,0,0,'FAILED','strptime() argument 1 must be str, not datetime.date','2025-09-29 22:32:37'),(5,1,'fifth_third_personal_may.pdf','PDF','2025-09-29 22:36:20',34,34,0,0,'COMPLETED',NULL,'2025-09-29 22:36:19'),(6,1,'fifth_third_personal.pdf','PDF','2025-10-04 22:41:18',34,0,0,34,'FAILED',NULL,'2025-10-04 22:41:18'),(7,1,'april pers bank statement.pdf','PDF','2025-10-04 22:54:03',36,36,0,0,'COMPLETED',NULL,'2025-10-04 22:54:03'),(8,1,'may Statement2025-05-21.pdf','PDF','2025-10-04 23:00:48',34,0,0,34,'FAILED',NULL,'2025-10-04 23:00:48'),(9,1,'may Statement2025-05-21.pdf','PDF','2025-10-04 23:02:09',34,0,0,34,'FAILED',NULL,'2025-10-04 23:02:08'),(10,1,'may Statement2025-05-21 (1).pdf','PDF','2025-10-04 23:14:14',34,0,0,34,'FAILED',NULL,'2025-10-04 23:14:13'),(11,1,'june Statement2025-06-20.pdf','PDF','2025-10-04 23:16:54',48,34,0,14,'COMPLETED',NULL,'2025-10-04 23:16:54'),(12,1,'june Statement2025-06-20 (1).pdf','PDF','2025-10-05 02:48:58',48,0,0,48,'FAILED',NULL,'2025-10-05 02:48:58'),(13,1,'june Statement2025-06-20 (1).pdf','PDF','2025-10-05 02:52:51',48,0,0,48,'FAILED',NULL,'2025-10-05 02:52:51'),(14,1,'june Statement2025-06-20 (1).pdf','PDF','2025-10-05 02:56:45',48,0,0,48,'FAILED',NULL,'2025-10-05 02:56:45'),(15,1,'june Statement2025-06-20 (1).pdf','PDF','2025-10-05 02:58:06',48,0,0,48,'FAILED',NULL,'2025-10-05 02:58:05'),(16,1,'june Statement2025-06-20 (1).pdf','PDF','2025-10-05 02:59:44',48,0,0,48,'FAILED',NULL,'2025-10-05 02:59:44'),(17,1,'june Statement2025-06-20 (1).pdf','PDF','2025-10-05 03:04:41',48,0,0,48,'FAILED',NULL,'2025-10-05 03:04:41'),(18,1,'Statement2025-01-15 (1)  rol.pdf','PDF','2025-10-05 06:15:59',40,40,0,0,'COMPLETED',NULL,'2025-10-05 06:15:58'),(19,1,'Statement2025-01-15 (1)  rol.pdf','PDF','2025-10-06 12:15:18',40,0,0,40,'FAILED',NULL,'2025-10-06 12:15:17'),(20,1,'Statement2025-01-15 (1)  rol.pdf','PDF','2025-10-06 18:13:04',40,0,0,40,'FAILED',NULL,'2025-10-06 18:13:04'),(21,1,'Statement2025-01-15 (1)  rol.pdf','PDF','2025-10-07 12:29:41',40,0,0,40,'FAILED',NULL,'2025-10-07 12:29:40');
/*!40000 ALTER TABLE `import_batches` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `organizations`
--

DROP TABLE IF EXISTS `organizations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `organizations` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `type` enum('NONPROFIT','PERSONAL') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `organizations`
--

LOCK TABLES `organizations` WRITE;
/*!40000 ALTER TABLE `organizations` DISABLE KEYS */;
INSERT INTO `organizations` VALUES (1,'GoodWorks Nonprofit','NONPROFIT','2025-09-25 14:02:22'),(2,'Personal (You)','PERSONAL','2025-09-25 14:02:22');
/*!40000 ALTER TABLE `organizations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `org_id` bigint unsigned NOT NULL,
  `payment_date` date NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `source_contact_id` bigint unsigned DEFAULT NULL,
  `type` enum('DONATION','GRANT','REIMBURSEMENT','OTHER') NOT NULL,
  `notes` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_payments_source` (`source_contact_id`),
  KEY `idx_payments_org_date` (`org_id`,`payment_date`),
  KEY `idx_payments_type` (`type`),
  CONSTRAINT `fk_payments_org` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`id`),
  CONSTRAINT `fk_payments_source` FOREIGN KEY (`source_contact_id`) REFERENCES `contacts` (`id`),
  CONSTRAINT `chk_payment_amount_pos` CHECK ((`amount` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
INSERT INTO `payments` VALUES (1,1,'2025-07-20',1000.00,1,'DONATION','Summer appeal','2025-09-25 14:02:22'),(2,1,'2025-08-25',5000.00,3,'GRANT','Quarterly disbursement','2025-09-25 14:02:22'),(3,1,'2025-09-12',250.00,1,'DONATION','Gala pre-donation','2025-09-25 14:02:22'),(4,1,'2025-09-18',200.00,NULL,'REIMBURSEMENT','Shared event cost repaid','2025-09-25 14:02:22');
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reports`
--

DROP TABLE IF EXISTS `reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reports` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(160) NOT NULL,
  `date_created` date NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `notes` varchar(255) DEFAULT NULL,
  `file_url` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `chk_report_dates` CHECK ((`start_date` <= `end_date`))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reports`
--

LOCK TABLES `reports` WRITE;
/*!40000 ALTER TABLE `reports` DISABLE KEYS */;
INSERT INTO `reports` VALUES (1,'Q3 2025 Summary','2025-09-23','2025-07-01','2025-09-30','Covers Jul–Sep 2025 activity',NULL);
/*!40000 ALTER TABLE `reports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `org_id` bigint unsigned NOT NULL,
  `transaction_date` date NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `description` text NOT NULL,
  `transaction_type` enum('DEBIT','CREDIT','TRANSFER') NOT NULL,
  `account_number` varchar(50) DEFAULT NULL,
  `bank_reference` varchar(100) DEFAULT NULL,
  `balance_after` decimal(15,2) DEFAULT NULL,
  `category_id` bigint unsigned DEFAULT NULL,
  `import_batch_id` bigint unsigned DEFAULT NULL,
  `raw_data` json DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_transactions_org` (`org_id`),
  KEY `idx_transactions_date` (`transaction_date`),
  KEY `idx_transactions_type` (`transaction_type`),
  KEY `idx_transactions_account` (`account_number`),
  KEY `idx_transactions_batch` (`import_batch_id`),
  KEY `idx_transactions_category` (`category_id`),
  CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`org_id`) REFERENCES `organizations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `transactions_ibfk_2` FOREIGN KEY (`import_batch_id`) REFERENCES `import_batches` (`id`) ON DELETE SET NULL,
  CONSTRAINT `transactions_ibfk_3` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=248 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transactions`
--

LOCK TABLES `transactions` WRITE;
/*!40000 ALTER TABLE `transactions` DISABLE KEYS */;
INSERT INTO `transactions` VALUES (56,1,'2025-06-17',25.00,'Checks #3921, #9343, #9344','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-17\", \"amount\": 25.0, \"org_id\": 1, \"raw_date\": \"06/17\", \"created_at\": \"2025-09-29T19:02:57.509117\", \"raw_amount\": \"25.00\", \"description\": \"3921 i 05/29 9343 i 200.00 9344 i 14.99\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"3921 i 05/29 9343 i 200.00 9344 i 14.99\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 20:19:58'),(57,1,'2025-06-05',200.00,'Check #9342','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-05\", \"amount\": 200.0, \"org_id\": 1, \"raw_date\": \"06/05\", \"created_at\": \"2025-09-29T19:02:57.509125\", \"raw_amount\": \"200.00\", \"description\": \"9342*i\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"9342*i\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(58,1,'2025-05-22',28.45,'PURCHASE AT SQ *HOPE THRIFT ST, Clearwater, FL ON 052125 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-22\", \"amount\": 28.45, \"org_id\": 1, \"raw_date\": \"05/22\", \"created_at\": \"2025-09-29T19:02:57.509129\", \"raw_amount\": \"28.45\", \"description\": \"PURCHASE AT SQ *HOPE THRIFT ST, Clearwater, FL ON 052125 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT SQ *HOPE THRIFT ST, Clearwater, FL ON 052125 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(59,1,'2025-05-22',123.00,'5/3 ONLINE PYMT TO DTE ENERGY- ACCT XXXXXXXX0544','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-22\", \"amount\": 123.0, \"org_id\": 1, \"raw_date\": \"05/22\", \"created_at\": \"2025-09-29T19:02:57.509132\", \"raw_amount\": \"123.00\", \"description\": \"5/3 ONLINE PYMT TO DTE ENERGY- ACCT XXXXXXXX0544\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO DTE ENERGY- ACCT XXXXXXXX0544\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(60,1,'2025-05-23',21.57,'PURCHASE AT GOODWILL SR VALDOS, VALDOSTA, GA ON 052225 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-23\", \"amount\": 21.57, \"org_id\": 1, \"raw_date\": \"05/23\", \"created_at\": \"2025-09-29T19:02:57.509135\", \"raw_amount\": \"21.57\", \"description\": \"PURCHASE AT GOODWILL SR VALDOS, VALDOSTA, GA ON 052225 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT GOODWILL SR VALDOS, VALDOSTA, GA ON 052225 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(61,1,'2025-05-27',24.76,'PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 052525 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-27\", \"amount\": 24.76, \"org_id\": 1, \"raw_date\": \"05/27\", \"created_at\": \"2025-09-29T19:02:57.509138\", \"raw_amount\": \"24.76\", \"description\": \"PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 052525 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 052525 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(62,1,'2025-05-27',36.04,'MERCHANT PAYMENT New 2 You Shoppe - 914069 2929 29th St SE Kentwood MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-27\", \"amount\": 36.04, \"org_id\": 1, \"raw_date\": \"05/27\", \"created_at\": \"2025-09-29T19:02:57.509141\", \"raw_amount\": \"36.04\", \"description\": \"MERCHANT PAYMENT New 2 You Shoppe - 914069 2929 29th St SE Kentwood MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"MERCHANT PAYMENT New 2 You Shoppe - 914069 2929 29th St SE Kentwood MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(63,1,'2025-05-27',45.60,'PURCHASE AT TEXAS ROADHOUSE #2, KENTWOOD, MI ON 052625 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-27\", \"amount\": 45.6, \"org_id\": 1, \"raw_date\": \"05/27\", \"created_at\": \"2025-09-29T19:02:57.509143\", \"raw_amount\": \"45.60\", \"description\": \"PURCHASE AT TEXAS ROADHOUSE #2, KENTWOOD, MI ON 052625 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT TEXAS ROADHOUSE #2, KENTWOOD, MI ON 052625 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(64,1,'2025-05-27',186.92,'MERCHANT PAYMENT MEIJER ST MEIJER - 005017 MEIJER 0505531 28TH ST GRAND RAPIDS MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-27\", \"amount\": 186.92, \"org_id\": 1, \"raw_date\": \"05/27\", \"created_at\": \"2025-09-29T19:02:57.509146\", \"raw_amount\": \"186.92\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 005017 MEIJER 0505531 28TH ST GRAND RAPIDS MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 005017 MEIJER 0505531 28TH ST GRAND RAPIDS MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(65,1,'2025-05-28',31.48,'PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 052825 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-28\", \"amount\": 31.48, \"org_id\": 1, \"raw_date\": \"05/28\", \"created_at\": \"2025-09-29T19:02:57.509162\", \"raw_amount\": \"31.48\", \"description\": \"PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 052825 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 052825 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(66,1,'2025-05-29',78.14,'MERCHANT PAYMENT MEIJER ST MEIJER - 021616 MEIJER #216315 WILSON A GRAND RAPIDS MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-29\", \"amount\": 78.14, \"org_id\": 1, \"raw_date\": \"05/29\", \"created_at\": \"2025-09-29T19:02:57.509166\", \"raw_amount\": \"78.14\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 021616 MEIJER #216315 WILSON A GRAND RAPIDS MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 021616 MEIJER #216315 WILSON A GRAND RAPIDS MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(67,1,'2025-05-29',104.25,'MERCHANT PAYMENT OLLIES BARGAIN O - 444550 1070 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-29\", \"amount\": 104.25, \"org_id\": 1, \"raw_date\": \"05/29\", \"created_at\": \"2025-09-29T19:02:57.509169\", \"raw_amount\": \"104.25\", \"description\": \"MERCHANT PAYMENT OLLIES BARGAIN O - 444550 1070 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"MERCHANT PAYMENT OLLIES BARGAIN O - 444550 1070 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(68,1,'2025-05-29',49.57,'MERCHANT PAYMENT NNT MAYA MEXICAN - 719958 1020 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-29\", \"amount\": 49.57, \"org_id\": 1, \"raw_date\": \"05/29\", \"created_at\": \"2025-09-29T19:02:57.509172\", \"raw_amount\": \"49.57\", \"description\": \"MERCHANT PAYMENT NNT MAYA MEXICAN - 719958 1020 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"MERCHANT PAYMENT NNT MAYA MEXICAN - 719958 1020 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(69,1,'2025-05-30',31.29,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 052925 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-30\", \"amount\": 31.29, \"org_id\": 1, \"raw_date\": \"05/30\", \"created_at\": \"2025-09-29T19:02:57.509175\", \"raw_amount\": \"31.29\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 052925 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 052925 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(70,1,'2025-05-30',191.00,'5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-30\", \"amount\": 191.0, \"org_id\": 1, \"raw_date\": \"05/30\", \"created_at\": \"2025-09-29T19:02:57.509178\", \"raw_amount\": \"191.00\", \"description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(71,1,'2025-05-30',361.65,'5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-30\", \"amount\": 361.65, \"org_id\": 1, \"raw_date\": \"05/30\", \"created_at\": \"2025-09-29T19:02:57.509181\", \"raw_amount\": \"361.65\", \"description\": \"5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(72,1,'2025-06-02',44.68,'PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,122,2,'{\"date\": \"2025-06-02\", \"amount\": 44.68, \"org_id\": 1, \"raw_date\": \"06/02\", \"created_at\": \"2025-09-29T19:02:57.509184\", \"raw_amount\": \"44.68\", \"description\": \"PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-07 12:04:29'),(73,1,'2025-06-02',106.47,'MERCHANT PAYMENT MEIJER ST MEIJER - 002015 MEIJER # 0202425 ALPINE GRAND RAPIDS MI ON 060225 FROM CARD#: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,100,2,'{\"date\": \"2025-06-02\", \"amount\": 106.47, \"org_id\": 1, \"raw_date\": \"06/02\", \"created_at\": \"2025-09-29T19:02:57.509186\", \"raw_amount\": \"106.47\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 002015 MEIJER # 0202425 ALPINE GRAND RAPIDS MI ON 060225 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 002015 MEIJER # 0202425 ALPINE GRAND RAPIDS MI ON 060225 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 18:12:52'),(74,1,'2025-06-02',35.42,'5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783','CREDIT',NULL,NULL,NULL,144,2,'{\"date\": \"2025-06-02\", \"amount\": 35.42, \"org_id\": 1, \"raw_date\": \"06/02\", \"created_at\": \"2025-09-29T19:02:57.509189\", \"raw_amount\": \"35.42\", \"description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:13:16'),(75,1,'2025-06-02',2900.00,'5/3 ONLINE PYMT TO WELLS FARG- ACCT XXXXXXXXXXX7580','CREDIT',NULL,NULL,NULL,311,2,'{\"date\": \"2025-06-02\", \"amount\": 2900.0, \"org_id\": 1, \"raw_date\": \"06/02\", \"created_at\": \"2025-09-29T19:02:57.509192\", \"raw_amount\": \"2,900.00\", \"description\": \"5/3 ONLINE PYMT TO WELLS FARG- ACCT XXXXXXXXXXX7580\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO WELLS FARG- ACCT XXXXXXXXXXX7580\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:15:27'),(76,1,'2025-06-02',3.95,'WORLD DEBIT MONTHLY FEE','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-02\", \"amount\": 3.95, \"org_id\": 1, \"raw_date\": \"06/02\", \"created_at\": \"2025-09-29T19:02:57.509195\", \"raw_amount\": \"3.95\", \"description\": \"WORLD DEBIT MONTHLY FEE\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"WORLD DEBIT MONTHLY FEE\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-03 12:26:01'),(77,1,'2025-06-03',12.66,'PURCHASE AT H J BEAUTY SUPPLY, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,350,2,'{\"date\": \"2025-06-03\", \"amount\": 12.66, \"org_id\": 1, \"raw_date\": \"06/03\", \"created_at\": \"2025-09-29T19:02:57.509198\", \"raw_amount\": \"12.66\", \"description\": \"PURCHASE AT H J BEAUTY SUPPLY, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT H J BEAUTY SUPPLY, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-05 03:07:41'),(78,1,'2025-06-05',24.98,'5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-05\", \"amount\": 24.98, \"org_id\": 1, \"raw_date\": \"06/05\", \"created_at\": \"2025-09-29T19:02:57.509201\", \"raw_amount\": \"24.98\", \"description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(79,1,'2025-06-05',1118.72,'5/3 MORTGAGE LN #XXXXXX5194 PAID BY AUTO BILLPAYER','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-05\", \"amount\": 1118.72, \"org_id\": 1, \"raw_date\": \"06/05\", \"created_at\": \"2025-09-29T19:02:57.509204\", \"raw_amount\": \"1,118.72\", \"description\": \"5/3 MORTGAGE LN #XXXXXX5194 PAID BY AUTO BILLPAYER\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 MORTGAGE LN #XXXXXX5194 PAID BY AUTO BILLPAYER\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(80,1,'2025-06-06',35.84,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-06\", \"amount\": 35.84, \"org_id\": 1, \"raw_date\": \"06/06\", \"created_at\": \"2025-09-29T19:02:57.509206\", \"raw_amount\": \"35.84\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(81,1,'2025-06-09',31.80,'MERCHANT PAYMENT TORRID #5358 - 892302 BYRON CENTER BYRON CENTER MI ON 060925 FROM CARD#: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-09\", \"amount\": 31.8, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-09-29T19:02:57.509209\", \"raw_amount\": \"31.80\", \"description\": \"MERCHANT PAYMENT TORRID #5358 - 892302 BYRON CENTER BYRON CENTER MI ON 060925 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"MERCHANT PAYMENT TORRID #5358 - 892302 BYRON CENTER BYRON CENTER MI ON 060925 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-03 12:40:42'),(82,1,'2025-06-09',48.36,'PURCHASE AT BELTLINE BAR, GRAND RAPIDS, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-09\", \"amount\": 48.36, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-09-29T19:02:57.509212\", \"raw_amount\": \"48.36\", \"description\": \"PURCHASE AT BELTLINE BAR, GRAND RAPIDS, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT BELTLINE BAR, GRAND RAPIDS, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-03 12:40:48'),(83,1,'2025-06-09',72.63,'PURCHASE AT TST*UCCELLOS DOWNT, Grand Rapids, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-09\", \"amount\": 72.63, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-09-29T19:02:57.509215\", \"raw_amount\": \"72.63\", \"description\": \"PURCHASE AT TST*UCCELLOS DOWNT, Grand Rapids, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT TST*UCCELLOS DOWNT, Grand Rapids, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(84,1,'2025-06-09',82.56,'PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-09\", \"amount\": 82.56, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-09-29T19:02:57.509233\", \"raw_amount\": \"82.56\", \"description\": \"PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(85,1,'2025-06-09',1144.33,'PURCHASE AT OFIELD FUNERAL HOM, GRAND RAPIDS, MI ON 060625 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-09\", \"amount\": 1144.33, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-09-29T19:02:57.509237\", \"raw_amount\": \"1,144.33\", \"description\": \"PURCHASE AT OFIELD FUNERAL HOM, GRAND RAPIDS, MI ON 060625 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT OFIELD FUNERAL HOM, GRAND RAPIDS, MI ON 060625 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(86,1,'2025-06-09',1250.00,'5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF # 01133792282','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-09\", \"amount\": 1250.0, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-09-29T19:02:57.509240\", \"raw_amount\": \"1,250.00\", \"description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF # 01133792282\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF # 01133792282\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(87,1,'2025-06-10',31.46,'PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 061025 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-10\", \"amount\": 31.46, \"org_id\": 1, \"raw_date\": \"06/10\", \"created_at\": \"2025-09-29T19:02:57.509243\", \"raw_amount\": \"31.46\", \"description\": \"PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 061025 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 061025 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-03 17:09:31'),(88,1,'2025-06-10',83.68,'PURCHASE AT SMKYBONES WNG-BGR, GRAND RAPIDS, MI ON 060825 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-10\", \"amount\": 83.68, \"org_id\": 1, \"raw_date\": \"06/10\", \"created_at\": \"2025-09-29T19:02:57.509245\", \"raw_amount\": \"83.68\", \"description\": \"PURCHASE AT SMKYBONES WNG-BGR, GRAND RAPIDS, MI ON 060825 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT SMKYBONES WNG-BGR, GRAND RAPIDS, MI ON 060825 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(89,1,'2025-06-11',56.71,'PURCHASE AT CANTINA MEXICAN GR, GRAND RAPIDS, MI ON 060925 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-11\", \"amount\": 56.71, \"org_id\": 1, \"raw_date\": \"06/11\", \"created_at\": \"2025-09-29T19:02:57.509248\", \"raw_amount\": \"56.71\", \"description\": \"PURCHASE AT CANTINA MEXICAN GR, GRAND RAPIDS, MI ON 060925 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT CANTINA MEXICAN GR, GRAND RAPIDS, MI ON 060925 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(90,1,'2025-06-13',30.68,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 061225 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-13\", \"amount\": 30.68, \"org_id\": 1, \"raw_date\": \"06/13\", \"created_at\": \"2025-09-29T19:02:57.509251\", \"raw_amount\": \"30.68\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 061225 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 061225 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(91,1,'2025-06-13',50.00,'5/3 ONLINE PYMT TO BANK OF AM- ACCT XXXXXXXXXXX9076','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-13\", \"amount\": 50.0, \"org_id\": 1, \"raw_date\": \"06/13\", \"created_at\": \"2025-09-29T19:02:57.509254\", \"raw_amount\": \"50.00\", \"description\": \"5/3 ONLINE PYMT TO BANK OF AM- ACCT XXXXXXXXXXX9076\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO BANK OF AM- ACCT XXXXXXXXXXX9076\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(92,1,'2025-06-13',50.00,'5/3 ONLINE PYMT TO US BANK/EL- ACCT XXXXXXXXXXX2905','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-13\", \"amount\": 50.0, \"org_id\": 1, \"raw_date\": \"06/13\", \"created_at\": \"2025-09-29T19:02:57.509257\", \"raw_amount\": \"50.00\", \"description\": \"5/3 ONLINE PYMT TO US BANK/EL- ACCT XXXXXXXXXXX2905\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO US BANK/EL- ACCT XXXXXXXXXXX2905\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(93,1,'2025-06-13',77.40,'5/3 ONLINE PYMT TO DINERS CLU- ACCT XXXXXXXXXXX0587','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-13\", \"amount\": 77.4, \"org_id\": 1, \"raw_date\": \"06/13\", \"created_at\": \"2025-09-29T19:02:57.509260\", \"raw_amount\": \"77.40\", \"description\": \"5/3 ONLINE PYMT TO DINERS CLU- ACCT XXXXXXXXXXX0587\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO DINERS CLU- ACCT XXXXXXXXXXX0587\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(94,1,'2025-06-13',200.00,'5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-13\", \"amount\": 200.0, \"org_id\": 1, \"raw_date\": \"06/13\", \"created_at\": \"2025-09-29T19:02:57.509262\", \"raw_amount\": \"200.00\", \"description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(95,1,'2025-06-17',101.64,'PURCHASE AT TUPELO HONEY GRAND, GRAND RAPIDS, MI ON 061625 FROM CARD#: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-17\", \"amount\": 101.64, \"org_id\": 1, \"raw_date\": \"06/17\", \"created_at\": \"2025-09-29T19:02:57.509265\", \"raw_amount\": \"101.64\", \"description\": \"PURCHASE AT TUPELO HONEY GRAND, GRAND RAPIDS, MI ON 061625 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"PURCHASE AT TUPELO HONEY GRAND, GRAND RAPIDS, MI ON 061625 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(96,1,'2025-06-20',83.44,'5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783','CREDIT',NULL,NULL,NULL,121,2,'{\"date\": \"2025-06-20\", \"amount\": 83.44, \"org_id\": 1, \"raw_date\": \"06/20\", \"created_at\": \"2025-09-29T19:02:57.509268\", \"raw_amount\": \"83.44\", \"description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:10:55'),(97,1,'2025-05-23',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737471','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-23\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"05/23\", \"created_at\": \"2025-09-29T19:02:57.509271\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737471\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737471\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(98,1,'2025-05-30',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737734','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-05-30\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"05/30\", \"created_at\": \"2025-09-29T19:02:57.509274\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737734\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737734\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(99,1,'2025-06-09',1886.00,'EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 061125','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-09\", \"amount\": 1886.0, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-09-29T19:02:57.509276\", \"raw_amount\": \"1,886.00\", \"description\": \"EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 061125\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 061125\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(100,1,'2025-06-09',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01133792797','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-09\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-09-29T19:02:57.509279\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01133792797\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01133792797\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:00:31'),(101,1,'2025-06-13',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01134782523','CREDIT',NULL,NULL,NULL,181,2,'{\"date\": \"2025-06-13\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"06/13\", \"created_at\": \"2025-09-29T19:02:57.509282\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01134782523\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01134782523\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:16:19'),(102,1,'2025-06-16',1708.00,'EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 061825','CREDIT',NULL,NULL,NULL,NULL,2,'{\"date\": \"2025-06-16\", \"amount\": 1708.0, \"org_id\": 1, \"raw_date\": \"06/16\", \"created_at\": \"2025-09-29T19:02:57.509285\", \"raw_amount\": \"1,708.00\", \"description\": \"EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 061825\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 061825\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-09-29 19:02:57'),(103,1,'2025-06-20',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01137577064','CREDIT',NULL,NULL,NULL,344,2,'{\"date\": \"2025-06-20\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"06/20\", \"created_at\": \"2025-09-29T19:02:57.509288\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01137577064\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01137577064\", \"extraction_method\": \"docling\"}','2025-09-29 19:02:57','2025-10-04 14:11:12'),(104,1,'2025-05-14',200.00,'9338 i 05/16 9340 i 04/22 9341 i','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-14\", \"amount\": 200.0, \"org_id\": 1, \"raw_date\": \"05/14\", \"created_at\": \"2025-09-29T22:36:19.913307\", \"raw_amount\": \"200.00\", \"description\": \"9338 i 05/16 9340 i 04/22 9341 i\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"9338 i 05/16 9340 i 04/22 9341 i\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(105,1,'2025-05-13',14.99,'Check 9339','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-13\", \"amount\": 14.99, \"org_id\": 1, \"raw_date\": \"05/13\", \"created_at\": \"2025-09-29T22:36:19.913315\", \"raw_amount\": \"14.99\", \"description\": \"Check #9339\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"Check #9339\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(106,1,'2025-04-24',200.00,'5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-04-24\", \"amount\": 200.0, \"org_id\": 1, \"raw_date\": \"04/24\", \"created_at\": \"2025-09-29T22:36:19.913319\", \"raw_amount\": \"200.00\", \"description\": \"5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-10-04 14:00:31'),(107,1,'2025-04-25',33.82,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 042425 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-04-25\", \"amount\": 33.82, \"org_id\": 1, \"raw_date\": \"04/25\", \"created_at\": \"2025-09-29T22:36:19.913322\", \"raw_amount\": \"33.82\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 042425 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 042425 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(108,1,'2025-04-28',9.12,'PURCHASE AT KILWINS GRAND RAPI, GRAND RAPIDS, MI ON 042725 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-04-28\", \"amount\": 9.12, \"org_id\": 1, \"raw_date\": \"04/28\", \"created_at\": \"2025-09-29T22:36:19.913326\", \"raw_amount\": \"9.12\", \"description\": \"PURCHASE AT KILWINS GRAND RAPI, GRAND RAPIDS, MI ON 042725 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"PURCHASE AT KILWINS GRAND RAPI, GRAND RAPIDS, MI ON 042725 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(109,1,'2025-04-28',50.00,'5/3 ONLINE PYMT TO BANK OF AM- ACCT XXXXXXXXXXX9076','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-04-28\", \"amount\": 50.0, \"org_id\": 1, \"raw_date\": \"04/28\", \"created_at\": \"2025-09-29T22:36:19.913329\", \"raw_amount\": \"50.00\", \"description\": \"5/3 ONLINE PYMT TO BANK OF AM- ACCT XXXXXXXXXXX9076\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO BANK OF AM- ACCT XXXXXXXXXXX9076\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(110,1,'2025-04-28',100.00,'5/3 ONLINE PYMT TO AMERICAN E- ACCT XXXXXXXXXXX1006','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-04-28\", \"amount\": 100.0, \"org_id\": 1, \"raw_date\": \"04/28\", \"created_at\": \"2025-09-29T22:36:19.913332\", \"raw_amount\": \"100.00\", \"description\": \"5/3 ONLINE PYMT TO AMERICAN E- ACCT XXXXXXXXXXX1006\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO AMERICAN E- ACCT XXXXXXXXXXX1006\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(111,1,'2025-04-28',131.83,'5/3 ONLINE PYMT TO DTE ENERGY- ACCT XXXXXXXX0544','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-04-28\", \"amount\": 131.83, \"org_id\": 1, \"raw_date\": \"04/28\", \"created_at\": \"2025-09-29T22:36:19.913335\", \"raw_amount\": \"131.83\", \"description\": \"5/3 ONLINE PYMT TO DTE ENERGY- ACCT XXXXXXXX0544\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO DTE ENERGY- ACCT XXXXXXXX0544\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(112,1,'2025-04-29',46.47,'PURCHASE AT PHOENIX THEATRES W, KENTWOOD, MI ON 042725 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-04-29\", \"amount\": 46.47, \"org_id\": 1, \"raw_date\": \"04/29\", \"created_at\": \"2025-09-29T22:36:19.913338\", \"raw_amount\": \"46.47\", \"description\": \"PURCHASE AT PHOENIX THEATRES W, KENTWOOD, MI ON 042725 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"PURCHASE AT PHOENIX THEATRES W, KENTWOOD, MI ON 042725 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(113,1,'2025-05-01',218.64,'5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-01\", \"amount\": 218.64, \"org_id\": 1, \"raw_date\": \"05/01\", \"created_at\": \"2025-09-29T22:36:19.913341\", \"raw_amount\": \"218.64\", \"description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(114,1,'2025-05-01',3.95,'WORLD DEBIT MONTHLY FEE','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-01\", \"amount\": 3.95, \"org_id\": 1, \"raw_date\": \"05/01\", \"created_at\": \"2025-09-29T22:36:19.913344\", \"raw_amount\": \"3.95\", \"description\": \"WORLD DEBIT MONTHLY FEE\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"WORLD DEBIT MONTHLY FEE\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(115,1,'2025-05-02',46.48,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 050125 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-02\", \"amount\": 46.48, \"org_id\": 1, \"raw_date\": \"05/02\", \"created_at\": \"2025-09-29T22:36:19.913347\", \"raw_amount\": \"46.48\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 050125 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 050125 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-10-04 14:00:31'),(116,1,'2025-05-02',53.00,'PURCHASE AT MERLE NORMAN C0700, GRAND RAPIDS, MI ON 042425 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-02\", \"amount\": 53.0, \"org_id\": 1, \"raw_date\": \"05/02\", \"created_at\": \"2025-09-29T22:36:19.913350\", \"raw_amount\": \"53.00\", \"description\": \"PURCHASE AT MERLE NORMAN C0700, GRAND RAPIDS, MI ON 042425 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"PURCHASE AT MERLE NORMAN C0700, GRAND RAPIDS, MI ON 042425 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-10-04 14:00:31'),(117,1,'2025-05-05',9.53,'MERCHANT PAYMENT MEIJER ST MEIJER - 016157 MEIJER 1612155 PAUL JO LEXINGTON KY ON 050525 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-05\", \"amount\": 9.53, \"org_id\": 1, \"raw_date\": \"05/05\", \"created_at\": \"2025-09-29T22:36:19.913353\", \"raw_amount\": \"9.53\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 016157 MEIJER 1612155 PAUL JO LEXINGTON KY ON 050525 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 016157 MEIJER 1612155 PAUL JO LEXINGTON KY ON 050525 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(118,1,'2025-05-05',44.23,'PURCHASE AT WALGREENS 17180, MOUNT VERNON, KY ON 050425 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-05\", \"amount\": 44.23, \"org_id\": 1, \"raw_date\": \"05/05\", \"created_at\": \"2025-09-29T22:36:19.913356\", \"raw_amount\": \"44.23\", \"description\": \"PURCHASE AT WALGREENS #17180, MOUNT VERNON, KY ON 050425 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"PURCHASE AT WALGREENS #17180, MOUNT VERNON, KY ON 050425 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(119,1,'2025-05-05',75.75,'MERCHANT PAYMENT MEIJER ST MEIJER - 016114 MEIJER 1612155 PAUL JO LEXINGTON KY ON 050525 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-05\", \"amount\": 75.75, \"org_id\": 1, \"raw_date\": \"05/05\", \"created_at\": \"2025-09-29T22:36:19.913359\", \"raw_amount\": \"75.75\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 016114 MEIJER 1612155 PAUL JO LEXINGTON KY ON 050525 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 016114 MEIJER 1612155 PAUL JO LEXINGTON KY ON 050525 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(120,1,'2025-05-05',1118.72,'5/3 MORTGAGE LN XXXXXX5194 PAID BY AUTO BILLPAYER','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-05\", \"amount\": 1118.72, \"org_id\": 1, \"raw_date\": \"05/05\", \"created_at\": \"2025-09-29T22:36:19.913362\", \"raw_amount\": \"1,118.72\", \"description\": \"5/3 MORTGAGE LN #XXXXXX5194 PAID BY AUTO BILLPAYER\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 MORTGAGE LN #XXXXXX5194 PAID BY AUTO BILLPAYER\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(121,1,'2025-05-06',1250.00,'5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF  01119964677','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-06\", \"amount\": 1250.0, \"org_id\": 1, \"raw_date\": \"05/06\", \"created_at\": \"2025-09-29T22:36:19.913365\", \"raw_amount\": \"1,250.00\", \"description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF # 01119964677\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF # 01119964677\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(122,1,'2025-05-07',68.10,'MERCHANT PAYMENT WINN DIXI 2139 3 - 451002 2139 34TH N SAINT PETERSB FL ON 050725 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-07\", \"amount\": 68.1, \"org_id\": 1, \"raw_date\": \"05/07\", \"created_at\": \"2025-09-29T22:36:19.913368\", \"raw_amount\": \"68.10\", \"description\": \"MERCHANT PAYMENT WINN DIXI 2139 3 - 451002 2139 34TH N SAINT PETERSB FL ON 050725 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"MERCHANT PAYMENT WINN DIXI 2139 3 - 451002 2139 34TH N SAINT PETERSB FL ON 050725 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(123,1,'2025-05-09',113.00,'5/3 ONLINE PYMT TO BARCLAYS B- ACCT XXXXXXXXXXX4804','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-09\", \"amount\": 113.0, \"org_id\": 1, \"raw_date\": \"05/09\", \"created_at\": \"2025-09-29T22:36:19.913371\", \"raw_amount\": \"113.00\", \"description\": \"5/3 ONLINE PYMT TO BARCLAYS B- ACCT XXXXXXXXXXX4804\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO BARCLAYS B- ACCT XXXXXXXXXXX4804\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(124,1,'2025-05-12',11.00,'MERCHANT PAYMENT WAL WAL-MART 46 - 900019 201 34TH ST N ST PETERSBURG FL ON 051225 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-12\", \"amount\": 11.0, \"org_id\": 1, \"raw_date\": \"05/12\", \"created_at\": \"2025-09-29T22:36:19.913374\", \"raw_amount\": \"11.00\", \"description\": \"MERCHANT PAYMENT WAL WAL-MART #46 - 900019 201 34TH ST N ST PETERSBURG FL ON 051225 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"MERCHANT PAYMENT WAL WAL-MART #46 - 900019 201 34TH ST N ST PETERSBURG FL ON 051225 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-10-04 14:00:31'),(125,1,'2025-05-12',54.60,'MERCHANT PAYMENT WAL-MART 4690 - 469001 201 34TH ST N ST PETERSBURG FL ON 051225 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-12\", \"amount\": 54.6, \"org_id\": 1, \"raw_date\": \"05/12\", \"created_at\": \"2025-09-29T22:36:19.913377\", \"raw_amount\": \"54.60\", \"description\": \"MERCHANT PAYMENT WAL-MART #4690 - 469001 201 34TH ST N ST PETERSBURG FL ON 051225 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"MERCHANT PAYMENT WAL-MART #4690 - 469001 201 34TH ST N ST PETERSBURG FL ON 051225 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-10-04 14:00:31'),(126,1,'2025-05-12',251.05,'MERCHANT PAYMENT WAL WAL-MART 46 - 900013 201 34TH ST N ST PETERSBURG FL ON 051225 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-12\", \"amount\": 251.05, \"org_id\": 1, \"raw_date\": \"05/12\", \"created_at\": \"2025-09-29T22:36:19.913380\", \"raw_amount\": \"251.05\", \"description\": \"MERCHANT PAYMENT WAL WAL-MART #46 - 900013 201 34TH ST N ST PETERSBURG FL ON 051225 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"MERCHANT PAYMENT WAL WAL-MART #46 - 900013 201 34TH ST N ST PETERSBURG FL ON 051225 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-10-04 14:00:31'),(127,1,'2025-05-13',13.01,'PURCHASE AT GOODWILL GANDY 10, SAINT PETERSB, FL ON 051225 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-13\", \"amount\": 13.01, \"org_id\": 1, \"raw_date\": \"05/13\", \"created_at\": \"2025-09-29T22:36:19.913383\", \"raw_amount\": \"13.01\", \"description\": \"PURCHASE AT GOODWILL GANDY #10, SAINT PETERSB, FL ON 051225 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"PURCHASE AT GOODWILL GANDY #10, SAINT PETERSB, FL ON 051225 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(128,1,'2025-05-13',154.30,'5/3 ONLINE PYMT TO WELLS FARG- ACCT XXXXXXXXXXX7580','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-13\", \"amount\": 154.3, \"org_id\": 1, \"raw_date\": \"05/13\", \"created_at\": \"2025-09-29T22:36:19.913386\", \"raw_amount\": \"154.30\", \"description\": \"5/3 ONLINE PYMT TO WELLS FARG- ACCT XXXXXXXXXXX7580\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO WELLS FARG- ACCT XXXXXXXXXXX7580\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(129,1,'2025-05-14',200.00,'5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-14\", \"amount\": 200.0, \"org_id\": 1, \"raw_date\": \"05/14\", \"created_at\": \"2025-09-29T22:36:19.913389\", \"raw_amount\": \"200.00\", \"description\": \"5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(130,1,'2025-05-15',175.00,'5/3 ONLINE PYMT TO CITY OF GR- ACCT XXX5443','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-15\", \"amount\": 175.0, \"org_id\": 1, \"raw_date\": \"05/15\", \"created_at\": \"2025-09-29T22:36:19.913392\", \"raw_amount\": \"175.00\", \"description\": \"5/3 ONLINE PYMT TO CITY OF GR- ACCT XXX5443\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CITY OF GR- ACCT XXX5443\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(131,1,'2025-05-16',75.00,'5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-16\", \"amount\": 75.0, \"org_id\": 1, \"raw_date\": \"05/16\", \"created_at\": \"2025-09-29T22:36:19.913395\", \"raw_amount\": \"75.00\", \"description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(132,1,'2025-04-25',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF  01118736302','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-04-25\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"04/25\", \"created_at\": \"2025-09-29T22:36:19.913398\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118736302\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118736302\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(133,1,'2025-05-02',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF  01118736746','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-02\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"05/02\", \"created_at\": \"2025-09-29T22:36:19.913402\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118736746\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118736746\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-10-04 14:00:31'),(134,1,'2025-05-09',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF  01118736971','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-09\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"05/09\", \"created_at\": \"2025-09-29T22:36:19.913405\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118736971\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118736971\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(135,1,'2025-05-12',1886.00,'EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 051425','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-12\", \"amount\": 1886.0, \"org_id\": 1, \"raw_date\": \"05/12\", \"created_at\": \"2025-09-29T22:36:19.913408\", \"raw_amount\": \"1,886.00\", \"description\": \"EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 051425\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 051425\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(136,1,'2025-05-16',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF  01118737207','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-16\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"05/16\", \"created_at\": \"2025-09-29T22:36:19.913411\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737207\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737207\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(137,1,'2025-05-19',1708.00,'EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 052125','CREDIT',NULL,NULL,NULL,NULL,5,'{\"date\": \"2025-05-19\", \"amount\": 1708.0, \"org_id\": 1, \"raw_date\": \"05/19\", \"created_at\": \"2025-09-29T22:36:19.913414\", \"raw_amount\": \"1,708.00\", \"description\": \"EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 052125\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf\", \"raw_description\": \"EARLY PAY: SSA TREAS 310 XXSOC SEC XXXXXXXXXA SSA 052125\", \"extraction_method\": \"docling\"}','2025-09-29 22:36:20','2025-09-29 22:36:20'),(138,1,'2025-04-14',20.00,'9333 i 03/27 9335 i 04/15 200.00 9337 i 200.00','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-14\", \"amount\": 20.0, \"org_id\": 1, \"raw_date\": \"04/14\", \"created_at\": \"2025-10-04T22:54:03.095703\", \"raw_amount\": \"20.00\", \"description\": \"9333 i 03/27 9335 i 04/15 200.00 9337 i 200.00\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"9333 i 03/27 9335 i 04/15 200.00 9337 i 200.00\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(139,1,'2025-04-17',200.00,'9334 i 03/25 9336 i 14.99','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-17\", \"amount\": 200.0, \"org_id\": 1, \"raw_date\": \"04/17\", \"created_at\": \"2025-10-04T22:54:03.095716\", \"raw_amount\": \"200.00\", \"description\": \"9334 i 03/25 9336 i 14.99\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"9334 i 03/25 9336 i 14.99\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(140,1,'2025-03-24',24.14,'PURCHASE AT GOODWILL - WYOMING, WYOMING, MI ON 032325 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-03-24\", \"amount\": 24.14, \"org_id\": 1, \"raw_date\": \"03/24\", \"created_at\": \"2025-10-04T22:54:03.095720\", \"raw_amount\": \"24.14\", \"description\": \"PURCHASE AT GOODWILL - WYOMING, WYOMING, MI ON 032325 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT GOODWILL - WYOMING, WYOMING, MI ON 032325 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(141,1,'2025-03-24',49.57,'MERCHANT PAYMENT MAYA MEXICAN GRI - 719958 1020 28TH ST SW WYOMING MI ON 032425 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-03-24\", \"amount\": 49.57, \"org_id\": 1, \"raw_date\": \"03/24\", \"created_at\": \"2025-10-04T22:54:03.095724\", \"raw_amount\": \"49.57\", \"description\": \"MERCHANT PAYMENT MAYA MEXICAN GRI - 719958 1020 28TH ST SW WYOMING MI ON 032425 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"MERCHANT PAYMENT MAYA MEXICAN GRI - 719958 1020 28TH ST SW WYOMING MI ON 032425 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(142,1,'2025-03-25',181.52,'5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-03-25\", \"amount\": 181.52, \"org_id\": 1, \"raw_date\": \"03/25\", \"created_at\": \"2025-10-04T22:54:03.095727\", \"raw_amount\": \"181.52\", \"description\": \"5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO FIRST BANK- ACCT XXXXXXXXXXX8416\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(143,1,'2025-03-26',214.51,'MERCHANT PAYMENT MEIJER ST MEIJER - 002014 MEIJER  0202425 ALPINE GRAND RAPIDS MI ON 032625 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-03-26\", \"amount\": 214.51, \"org_id\": 1, \"raw_date\": \"03/26\", \"created_at\": \"2025-10-04T22:54:03.095730\", \"raw_amount\": \"214.51\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 002014 MEIJER # 0202425 ALPINE GRAND RAPIDS MI ON 032625 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 002014 MEIJER # 0202425 ALPINE GRAND RAPIDS MI ON 032625 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(144,1,'2025-03-27',37.29,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 032025 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-03-27\", \"amount\": 37.29, \"org_id\": 1, \"raw_date\": \"03/27\", \"created_at\": \"2025-10-04T22:54:03.095733\", \"raw_amount\": \"37.29\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 032025 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 032025 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(145,1,'2025-03-27',19.46,'5/3 ONLINE PYMT TO DTE ENERGY- ACCT XXXXXXXX0544','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-03-27\", \"amount\": 19.46, \"org_id\": 1, \"raw_date\": \"03/27\", \"created_at\": \"2025-10-04T22:54:03.095737\", \"raw_amount\": \"19.46\", \"description\": \"5/3 ONLINE PYMT TO DTE ENERGY- ACCT XXXXXXXX0544\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO DTE ENERGY- ACCT XXXXXXXX0544\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(146,1,'2025-03-27',244.69,'5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-03-27\", \"amount\": 244.69, \"org_id\": 1, \"raw_date\": \"03/27\", \"created_at\": \"2025-10-04T22:54:03.095740\", \"raw_amount\": \"244.69\", \"description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX7996\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(147,1,'2025-03-28',39.62,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 032725 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-03-28\", \"amount\": 39.62, \"org_id\": 1, \"raw_date\": \"03/28\", \"created_at\": \"2025-10-04T22:54:03.095743\", \"raw_amount\": \"39.62\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 032725 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 032725 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(148,1,'2025-04-01',70.04,'PURCHASE AT TEXAS ROADHOUSE 2, KENTWOOD, MI ON 040125 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-01\", \"amount\": 70.04, \"org_id\": 1, \"raw_date\": \"04/01\", \"created_at\": \"2025-10-04T22:54:03.095746\", \"raw_amount\": \"70.04\", \"description\": \"PURCHASE AT TEXAS ROADHOUSE #2, KENTWOOD, MI ON 040125 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT TEXAS ROADHOUSE #2, KENTWOOD, MI ON 040125 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(149,1,'2025-04-01',147.09,'MERCHANT PAYMENT MEIJER ST MEIJER - 031115 MEIJER 3111540 28TH ST GRAND RAPIDS MI ON 040125 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-01\", \"amount\": 147.09, \"org_id\": 1, \"raw_date\": \"04/01\", \"created_at\": \"2025-10-04T22:54:03.095749\", \"raw_amount\": \"147.09\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 031115 MEIJER 3111540 28TH ST GRAND RAPIDS MI ON 040125 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 031115 MEIJER 3111540 28TH ST GRAND RAPIDS MI ON 040125 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(150,1,'2025-04-01',1250.00,'5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF  01111113979','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-01\", \"amount\": 1250.0, \"org_id\": 1, \"raw_date\": \"04/01\", \"created_at\": \"2025-10-04T22:54:03.095752\", \"raw_amount\": \"1,250.00\", \"description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF # 01111113979\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF # 01111113979\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(151,1,'2025-04-01',3.95,'WORLD DEBIT MONTHLY FEE','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-01\", \"amount\": 3.95, \"org_id\": 1, \"raw_date\": \"04/01\", \"created_at\": \"2025-10-04T22:54:03.095755\", \"raw_amount\": \"3.95\", \"description\": \"WORLD DEBIT MONTHLY FEE\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"WORLD DEBIT MONTHLY FEE\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(152,1,'2025-04-02',84.10,'5/3 ONLINE PYMT TO BARCLAYS B- ACCT XXXXXXXXXXX4875','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-02\", \"amount\": 84.1, \"org_id\": 1, \"raw_date\": \"04/02\", \"created_at\": \"2025-10-04T22:54:03.095759\", \"raw_amount\": \"84.10\", \"description\": \"5/3 ONLINE PYMT TO BARCLAYS B- ACCT XXXXXXXXXXX4875\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO BARCLAYS B- ACCT XXXXXXXXXXX4875\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(153,1,'2025-04-04',24.00,'5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-04\", \"amount\": 24.0, \"org_id\": 1, \"raw_date\": \"04/04\", \"created_at\": \"2025-10-04T22:54:03.095762\", \"raw_amount\": \"24.00\", \"description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(154,1,'2025-04-04',1118.72,'5/3 MORTGAGE LN XXXXXX5194 PAID BY AUTO BILLPAYER','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-04\", \"amount\": 1118.72, \"org_id\": 1, \"raw_date\": \"04/04\", \"created_at\": \"2025-10-04T22:54:03.095765\", \"raw_amount\": \"1,118.72\", \"description\": \"5/3 MORTGAGE LN #XXXXXX5194 PAID BY AUTO BILLPAYER\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 MORTGAGE LN #XXXXXX5194 PAID BY AUTO BILLPAYER\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(155,1,'2025-04-07',47.91,'PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 040625 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-07\", \"amount\": 47.91, \"org_id\": 1, \"raw_date\": \"04/07\", \"created_at\": \"2025-10-04T22:54:03.095768\", \"raw_amount\": \"47.91\", \"description\": \"PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 040625 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 040625 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(156,1,'2025-04-07',163.76,'MERCHANT PAYMENT MEIJER ST MEIJER - 005017 MEIJER 0505531 28TH ST GRAND RAPIDS MI ON 040725 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-07\", \"amount\": 163.76, \"org_id\": 1, \"raw_date\": \"04/07\", \"created_at\": \"2025-10-04T22:54:03.095772\", \"raw_amount\": \"163.76\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 005017 MEIJER 0505531 28TH ST GRAND RAPIDS MI ON 040725 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 005017 MEIJER 0505531 28TH ST GRAND RAPIDS MI ON 040725 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(157,1,'2025-04-07',23.05,'5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-07\", \"amount\": 23.05, \"org_id\": 1, \"raw_date\": \"04/07\", \"created_at\": \"2025-10-04T22:54:03.095775\", \"raw_amount\": \"23.05\", \"description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(158,1,'2025-04-08',37.92,'MERCHANT PAYMENT DENNYS 7909 - 790902 KENTWOOD KENTWOOD MI ON 040825 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-08\", \"amount\": 37.92, \"org_id\": 1, \"raw_date\": \"04/08\", \"created_at\": \"2025-10-04T22:54:03.095778\", \"raw_amount\": \"37.92\", \"description\": \"MERCHANT PAYMENT DENNY\'S #7909 - 790902 KENTWOOD KENTWOOD MI ON 040825 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"MERCHANT PAYMENT DENNY\'S #7909 - 790902 KENTWOOD KENTWOOD MI ON 040825 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(159,1,'2025-04-09',10.90,'PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 040825 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-09\", \"amount\": 10.9, \"org_id\": 1, \"raw_date\": \"04/09\", \"created_at\": \"2025-10-04T22:54:03.095781\", \"raw_amount\": \"10.90\", \"description\": \"PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 040825 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 040825 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(160,1,'2025-04-11',35.34,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 041025 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-11\", \"amount\": 35.34, \"org_id\": 1, \"raw_date\": \"04/11\", \"created_at\": \"2025-10-04T22:54:03.095784\", \"raw_amount\": \"35.34\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 041025 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 041025 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(161,1,'2025-04-11',82.54,'5/3 ONLINE PYMT TO WELLS FARG- ACCT XXXXXXXXXXX7580','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-11\", \"amount\": 82.54, \"org_id\": 1, \"raw_date\": \"04/11\", \"created_at\": \"2025-10-04T22:54:03.095787\", \"raw_amount\": \"82.54\", \"description\": \"5/3 ONLINE PYMT TO WELLS FARG- ACCT XXXXXXXXXXX7580\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO WELLS FARG- ACCT XXXXXXXXXXX7580\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(162,1,'2025-04-14',161.22,'MERCHANT PAYMENT MEIJER ST MEIJER - 031116 MEIJER 3111540 28TH ST GRAND RAPIDS MI ON 041425 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-14\", \"amount\": 161.22, \"org_id\": 1, \"raw_date\": \"04/14\", \"created_at\": \"2025-10-04T22:54:03.095790\", \"raw_amount\": \"161.22\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 031116 MEIJER 3111540 28TH ST GRAND RAPIDS MI ON 041425 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 031116 MEIJER 3111540 28TH ST GRAND RAPIDS MI ON 041425 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(163,1,'2025-04-15',10.57,'PURCHASE AT GOODWILL - 29TH ST, KENTWOOD, MI ON 041425 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-15\", \"amount\": 10.57, \"org_id\": 1, \"raw_date\": \"04/15\", \"created_at\": \"2025-10-04T22:54:03.095793\", \"raw_amount\": \"10.57\", \"description\": \"PURCHASE AT GOODWILL - 29TH ST, KENTWOOD, MI ON 041425 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT GOODWILL - 29TH ST, KENTWOOD, MI ON 041425 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(164,1,'2025-04-16',16.89,'PURCHASE AT MR BURGER RESTAURA, GRAND RAPIDS, MI ON 041425 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-16\", \"amount\": 16.89, \"org_id\": 1, \"raw_date\": \"04/16\", \"created_at\": \"2025-10-04T22:54:03.095796\", \"raw_amount\": \"16.89\", \"description\": \"PURCHASE AT MR BURGER RESTAURA, GRAND RAPIDS, MI ON 041425 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT MR BURGER RESTAURA, GRAND RAPIDS, MI ON 041425 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(165,1,'2025-04-16',400.00,'5/3 ONLINE PYMT TO DINERS CLU- ACCT XXXXXXXXXXX4887','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-16\", \"amount\": 400.0, \"org_id\": 1, \"raw_date\": \"04/16\", \"created_at\": \"2025-10-04T22:54:03.095800\", \"raw_amount\": \"400.00\", \"description\": \"5/3 ONLINE PYMT TO DINERS CLU- ACCT XXXXXXXXXXX4887\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO DINERS CLU- ACCT XXXXXXXXXXX4887\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(166,1,'2025-04-17',30.00,'5/3 ONLINE PYMT TO DISCOVER C- ACCT XXXXXXXXXXX3580','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-17\", \"amount\": 30.0, \"org_id\": 1, \"raw_date\": \"04/17\", \"created_at\": \"2025-10-04T22:54:03.095803\", \"raw_amount\": \"30.00\", \"description\": \"5/3 ONLINE PYMT TO DISCOVER C- ACCT XXXXXXXXXXX3580\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO DISCOVER C- ACCT XXXXXXXXXXX3580\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(167,1,'2025-04-18',34.16,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 041725 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-18\", \"amount\": 34.16, \"org_id\": 1, \"raw_date\": \"04/18\", \"created_at\": \"2025-10-04T22:54:03.095806\", \"raw_amount\": \"34.16\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 041725 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 041725 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(168,1,'2025-04-18',0.98,'5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-18\", \"amount\": 0.98, \"org_id\": 1, \"raw_date\": \"04/18\", \"created_at\": \"2025-10-04T22:54:03.095809\", \"raw_amount\": \"0.98\", \"description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX9915\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(169,1,'2025-04-18',186.07,'5/3 ONLINE PYMT TO CITY OF GR- ACCT XXX5443','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-18\", \"amount\": 186.07, \"org_id\": 1, \"raw_date\": \"04/18\", \"created_at\": \"2025-10-04T22:54:03.095812\", \"raw_amount\": \"186.07\", \"description\": \"5/3 ONLINE PYMT TO CITY OF GR- ACCT XXX5443\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CITY OF GR- ACCT XXX5443\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(170,1,'2025-04-18',677.56,'5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-18\", \"amount\": 677.56, \"org_id\": 1, \"raw_date\": \"04/18\", \"created_at\": \"2025-10-04T22:54:03.095815\", \"raw_amount\": \"677.56\", \"description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX5783\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(171,1,'2025-04-21',41.22,'PURCHASE AT TEXAS ROADHOUSE 2, KENTWOOD, MI ON 042125 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-21\", \"amount\": 41.22, \"org_id\": 1, \"raw_date\": \"04/21\", \"created_at\": \"2025-10-04T22:54:03.095818\", \"raw_amount\": \"41.22\", \"description\": \"PURCHASE AT TEXAS ROADHOUSE #2, KENTWOOD, MI ON 042125 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"PURCHASE AT TEXAS ROADHOUSE #2, KENTWOOD, MI ON 042125 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(172,1,'2025-04-21',170.70,'MERCHANT PAYMENT MEIJER ST MEIJER - 002014 MEIJER  0202425 ALPINE GRAND RAPIDS MI ON 042125 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-21\", \"amount\": 170.7, \"org_id\": 1, \"raw_date\": \"04/21\", \"created_at\": \"2025-10-04T22:54:03.095821\", \"raw_amount\": \"170.70\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 002014 MEIJER # 0202425 ALPINE GRAND RAPIDS MI ON 042125 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 002014 MEIJER # 0202425 ALPINE GRAND RAPIDS MI ON 042125 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(173,1,'2025-04-21',308.82,'5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX0062','CREDIT',NULL,NULL,NULL,NULL,7,'{\"date\": \"2025-04-21\", \"amount\": 308.82, \"org_id\": 1, \"raw_date\": \"04/21\", \"created_at\": \"2025-10-04T22:54:03.095824\", \"raw_amount\": \"308.82\", \"description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX0062\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/april pers bank statement.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CHASE MC &- ACCT XXXXXXXXXXX0062\", \"extraction_method\": \"docling\"}','2025-10-04 22:54:04','2025-10-04 22:54:04'),(174,1,'2025-06-17',25.00,'Checks 3921, 9343, 9344','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-17\", \"amount\": 25.0, \"org_id\": 1, \"raw_date\": \"06/17\", \"created_at\": \"2025-10-04T23:16:54.213828\", \"raw_amount\": \"25.00\", \"description\": \"Checks #3921, #9343, #9344\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"Checks #3921, #9343, #9344\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(175,1,'2025-06-05',200.00,'Check 9342','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-05\", \"amount\": 200.0, \"org_id\": 1, \"raw_date\": \"06/05\", \"created_at\": \"2025-10-04T23:16:54.213839\", \"raw_amount\": \"200.00\", \"description\": \"Check #9342\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"Check #9342\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(176,1,'2025-05-22',28.45,'PURCHASE AT SQ HOPE THRIFT ST, Clearwater, FL ON 052125 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-22\", \"amount\": 28.45, \"org_id\": 1, \"raw_date\": \"05/22\", \"created_at\": \"2025-10-04T23:16:54.213844\", \"raw_amount\": \"28.45\", \"description\": \"PURCHASE AT SQ *HOPE THRIFT ST, Clearwater, FL ON 052125 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT SQ *HOPE THRIFT ST, Clearwater, FL ON 052125 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(177,1,'2025-05-23',21.57,'PURCHASE AT GOODWILL SR VALDOS, VALDOSTA, GA ON 052225 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-23\", \"amount\": 21.57, \"org_id\": 1, \"raw_date\": \"05/23\", \"created_at\": \"2025-10-04T23:16:54.213852\", \"raw_amount\": \"21.57\", \"description\": \"PURCHASE AT GOODWILL SR VALDOS, VALDOSTA, GA ON 052225 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT GOODWILL SR VALDOS, VALDOSTA, GA ON 052225 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(178,1,'2025-05-27',24.76,'PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 052525 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-27\", \"amount\": 24.76, \"org_id\": 1, \"raw_date\": \"05/27\", \"created_at\": \"2025-10-04T23:16:54.213856\", \"raw_amount\": \"24.76\", \"description\": \"PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 052525 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT GOODWILL - CASCADE, GRAND RAPIDS, MI ON 052525 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(179,1,'2025-05-27',36.04,'MERCHANT PAYMENT New 2 You Shoppe - 914069 2929 29th St SE Kentwood MI ON 052725 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-27\", \"amount\": 36.04, \"org_id\": 1, \"raw_date\": \"05/27\", \"created_at\": \"2025-10-04T23:16:54.213859\", \"raw_amount\": \"36.04\", \"description\": \"MERCHANT PAYMENT New 2 You Shoppe - 914069 2929 29th St SE Kentwood MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"MERCHANT PAYMENT New 2 You Shoppe - 914069 2929 29th St SE Kentwood MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(180,1,'2025-05-27',45.60,'PURCHASE AT TEXAS ROADHOUSE 2, KENTWOOD, MI ON 052625 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-27\", \"amount\": 45.6, \"org_id\": 1, \"raw_date\": \"05/27\", \"created_at\": \"2025-10-04T23:16:54.213863\", \"raw_amount\": \"45.60\", \"description\": \"PURCHASE AT TEXAS ROADHOUSE #2, KENTWOOD, MI ON 052625 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT TEXAS ROADHOUSE #2, KENTWOOD, MI ON 052625 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(181,1,'2025-05-27',186.92,'MERCHANT PAYMENT MEIJER ST MEIJER - 005017 MEIJER 0505531 28TH ST GRAND RAPIDS MI ON 052725 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-27\", \"amount\": 186.92, \"org_id\": 1, \"raw_date\": \"05/27\", \"created_at\": \"2025-10-04T23:16:54.213867\", \"raw_amount\": \"186.92\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 005017 MEIJER 0505531 28TH ST GRAND RAPIDS MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 005017 MEIJER 0505531 28TH ST GRAND RAPIDS MI ON 052725 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(182,1,'2025-05-28',31.48,'PURCHASE AT TST RUSS SOUTHE, GRAND RAPIDS, MI ON 052825 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-28\", \"amount\": 31.48, \"org_id\": 1, \"raw_date\": \"05/28\", \"created_at\": \"2025-10-04T23:16:54.213870\", \"raw_amount\": \"31.48\", \"description\": \"PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 052825 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 052825 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(183,1,'2025-05-29',78.14,'MERCHANT PAYMENT MEIJER ST MEIJER - 021616 MEIJER 216315 WILSON A GRAND RAPIDS MI ON 052925 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-29\", \"amount\": 78.14, \"org_id\": 1, \"raw_date\": \"05/29\", \"created_at\": \"2025-10-04T23:16:54.213874\", \"raw_amount\": \"78.14\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 021616 MEIJER #216315 WILSON A GRAND RAPIDS MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 021616 MEIJER #216315 WILSON A GRAND RAPIDS MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:56','2025-10-04 23:16:56'),(184,1,'2025-05-29',104.25,'MERCHANT PAYMENT OLLIES BARGAIN O - 444550 1070 28TH ST SW WYOMING MI ON 052925 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-29\", \"amount\": 104.25, \"org_id\": 1, \"raw_date\": \"05/29\", \"created_at\": \"2025-10-04T23:16:54.213878\", \"raw_amount\": \"104.25\", \"description\": \"MERCHANT PAYMENT OLLIES BARGAIN O - 444550 1070 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"MERCHANT PAYMENT OLLIES BARGAIN O - 444550 1070 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(185,1,'2025-05-29',49.57,'MERCHANT PAYMENT NNT MAYA MEXICAN - 719958 1020 28TH ST SW WYOMING MI ON 052925 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-29\", \"amount\": 49.57, \"org_id\": 1, \"raw_date\": \"05/29\", \"created_at\": \"2025-10-04T23:16:54.213882\", \"raw_amount\": \"49.57\", \"description\": \"MERCHANT PAYMENT NNT MAYA MEXICAN - 719958 1020 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"MERCHANT PAYMENT NNT MAYA MEXICAN - 719958 1020 28TH ST SW WYOMING MI ON 052925 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(186,1,'2025-05-30',31.29,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 052925 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-30\", \"amount\": 31.29, \"org_id\": 1, \"raw_date\": \"05/30\", \"created_at\": \"2025-10-04T23:16:54.213886\", \"raw_amount\": \"31.29\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 052925 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 052925 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(187,1,'2025-06-02',44.68,'PURCHASE AT TST BESTSIDE BAR, GRAND RAPIDS, MI ON 060225 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,331,11,'{\"date\": \"2025-06-02\", \"amount\": 44.68, \"org_id\": 1, \"raw_date\": \"06/02\", \"created_at\": \"2025-10-04T23:16:54.213897\", \"raw_amount\": \"44.68\", \"description\": \"PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-07 12:03:04'),(188,1,'2025-06-02',106.47,'MERCHANT PAYMENT MEIJER ST MEIJER - 002015 MEIJER  0202425 ALPINE GRAND RAPIDS MI ON 060225 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-02\", \"amount\": 106.47, \"org_id\": 1, \"raw_date\": \"06/02\", \"created_at\": \"2025-10-04T23:16:54.213901\", \"raw_amount\": \"106.47\", \"description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 002015 MEIJER # 0202425 ALPINE GRAND RAPIDS MI ON 060225 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"MERCHANT PAYMENT MEIJER ST MEIJER - 002015 MEIJER # 0202425 ALPINE GRAND RAPIDS MI ON 060225 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(189,1,'2025-06-03',12.66,'PURCHASE AT H J BEAUTY SUPPLY, GRAND RAPIDS, MI ON 060225 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-03\", \"amount\": 12.66, \"org_id\": 1, \"raw_date\": \"06/03\", \"created_at\": \"2025-10-04T23:16:54.213915\", \"raw_amount\": \"12.66\", \"description\": \"PURCHASE AT H J BEAUTY SUPPLY, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT H J BEAUTY SUPPLY, GRAND RAPIDS, MI ON 060225 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(190,1,'2025-06-05',1118.72,'5/3 MORTGAGE LN XXXXXX5194 PAID BY AUTO BILLPAYER','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-05\", \"amount\": 1118.72, \"org_id\": 1, \"raw_date\": \"06/05\", \"created_at\": \"2025-10-04T23:16:54.213922\", \"raw_amount\": \"1,118.72\", \"description\": \"5/3 MORTGAGE LN #XXXXXX5194 PAID BY AUTO BILLPAYER\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"5/3 MORTGAGE LN #XXXXXX5194 PAID BY AUTO BILLPAYER\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(191,1,'2025-06-06',35.84,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 060525 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-06\", \"amount\": 35.84, \"org_id\": 1, \"raw_date\": \"06/06\", \"created_at\": \"2025-10-04T23:16:54.213932\", \"raw_amount\": \"35.84\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(192,1,'2025-06-09',31.80,'MERCHANT PAYMENT TORRID 5358 - 892302 BYRON CENTER BYRON CENTER MI ON 060925 FROM CARD: XXXXXXXXXXXX950X','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-09\", \"amount\": 31.8, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-10-04T23:16:54.213937\", \"raw_amount\": \"31.80\", \"description\": \"MERCHANT PAYMENT TORRID #5358 - 892302 BYRON CENTER BYRON CENTER MI ON 060925 FROM CARD#: XXXXXXXXXXXX950X\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"MERCHANT PAYMENT TORRID #5358 - 892302 BYRON CENTER BYRON CENTER MI ON 060925 FROM CARD#: XXXXXXXXXXXX950X\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(193,1,'2025-06-09',48.36,'PURCHASE AT BELTLINE BAR, GRAND RAPIDS, MI ON 060525 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-09\", \"amount\": 48.36, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-10-04T23:16:54.213941\", \"raw_amount\": \"48.36\", \"description\": \"PURCHASE AT BELTLINE BAR, GRAND RAPIDS, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT BELTLINE BAR, GRAND RAPIDS, MI ON 060525 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(194,1,'2025-06-09',72.63,'PURCHASE AT TSTUCCELLOS DOWNT, Grand Rapids, MI ON 060725 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-09\", \"amount\": 72.63, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-10-04T23:16:54.213944\", \"raw_amount\": \"72.63\", \"description\": \"PURCHASE AT TST*UCCELLOS DOWNT, Grand Rapids, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT TST*UCCELLOS DOWNT, Grand Rapids, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(195,1,'2025-06-09',82.56,'PURCHASE AT TST BESTSIDE BAR, GRAND RAPIDS, MI ON 060725 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-09\", \"amount\": 82.56, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-10-04T23:16:54.213948\", \"raw_amount\": \"82.56\", \"description\": \"PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT TST* BESTSIDE BAR, GRAND RAPIDS, MI ON 060725 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(196,1,'2025-06-09',1144.33,'PURCHASE AT OFIELD FUNERAL HOM, GRAND RAPIDS, MI ON 060625 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-09\", \"amount\": 1144.33, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-10-04T23:16:54.213951\", \"raw_amount\": \"1,144.33\", \"description\": \"PURCHASE AT OFIELD FUNERAL HOM, GRAND RAPIDS, MI ON 060625 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT OFIELD FUNERAL HOM, GRAND RAPIDS, MI ON 060625 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(197,1,'2025-06-09',1250.00,'5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF  01133792282','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-09\", \"amount\": 1250.0, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-10-04T23:16:54.213955\", \"raw_amount\": \"1,250.00\", \"description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF # 01133792282\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX6285 REF # 01133792282\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(198,1,'2025-06-10',31.46,'PURCHASE AT TST RUSS SOUTHE, GRAND RAPIDS, MI ON 061025 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-10\", \"amount\": 31.46, \"org_id\": 1, \"raw_date\": \"06/10\", \"created_at\": \"2025-10-04T23:16:54.213959\", \"raw_amount\": \"31.46\", \"description\": \"PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 061025 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT TST* RUSS\' SOUTHE, GRAND RAPIDS, MI ON 061025 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(199,1,'2025-06-10',83.68,'PURCHASE AT SMKYBONES WNG-BGR, GRAND RAPIDS, MI ON 060825 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-10\", \"amount\": 83.68, \"org_id\": 1, \"raw_date\": \"06/10\", \"created_at\": \"2025-10-04T23:16:54.213962\", \"raw_amount\": \"83.68\", \"description\": \"PURCHASE AT SMKYBONES WNG-BGR, GRAND RAPIDS, MI ON 060825 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT SMKYBONES WNG-BGR, GRAND RAPIDS, MI ON 060825 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(200,1,'2025-06-11',56.71,'PURCHASE AT CANTINA MEXICAN GR, GRAND RAPIDS, MI ON 060925 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-11\", \"amount\": 56.71, \"org_id\": 1, \"raw_date\": \"06/11\", \"created_at\": \"2025-10-04T23:16:54.213966\", \"raw_amount\": \"56.71\", \"description\": \"PURCHASE AT CANTINA MEXICAN GR, GRAND RAPIDS, MI ON 060925 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT CANTINA MEXICAN GR, GRAND RAPIDS, MI ON 060925 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(201,1,'2025-06-13',30.68,'PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 061225 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-13\", \"amount\": 30.68, \"org_id\": 1, \"raw_date\": \"06/13\", \"created_at\": \"2025-10-04T23:16:54.213969\", \"raw_amount\": \"30.68\", \"description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 061225 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT APPLEBEES 8382, COMSTOCK P, MI ON 061225 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(202,1,'2025-06-17',101.64,'PURCHASE AT TUPELO HONEY GRAND, GRAND RAPIDS, MI ON 061625 FROM CARD: XXXXXXXXXXXX9509','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-17\", \"amount\": 101.64, \"org_id\": 1, \"raw_date\": \"06/17\", \"created_at\": \"2025-10-04T23:16:54.213987\", \"raw_amount\": \"101.64\", \"description\": \"PURCHASE AT TUPELO HONEY GRAND, GRAND RAPIDS, MI ON 061625 FROM CARD#: XXXXXXXXXXXX9509\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"PURCHASE AT TUPELO HONEY GRAND, GRAND RAPIDS, MI ON 061625 FROM CARD#: XXXXXXXXXXXX9509\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(203,1,'2025-05-23',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF  01118737471','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-23\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"05/23\", \"created_at\": \"2025-10-04T23:16:54.213994\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737471\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737471\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(204,1,'2025-05-30',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF  01118737734','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-05-30\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"05/30\", \"created_at\": \"2025-10-04T23:16:54.213998\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737734\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01118737734\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(205,1,'2025-06-09',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF  01133792797','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-09\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"06/09\", \"created_at\": \"2025-10-04T23:16:54.214005\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01133792797\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01133792797\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(206,1,'2025-06-13',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF  01134782523','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-13\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"06/13\", \"created_at\": \"2025-10-04T23:16:54.214009\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01134782523\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01134782523\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(207,1,'2025-06-20',1800.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF  01137577064','CREDIT',NULL,NULL,NULL,NULL,11,'{\"date\": \"2025-06-20\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"06/20\", \"created_at\": \"2025-10-04T23:16:54.214016\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01137577064\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/june Statement2025-06-20.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX6285 REF # 01137577064\", \"extraction_method\": \"docling\"}','2025-10-04 23:16:57','2025-10-04 23:16:57'),(208,1,'2024-01-06',150.00,'2359 i 12/30 11005 i 12/23 28.25 11013 i 100.00','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-06\", \"amount\": 150.0, \"org_id\": 1, \"raw_date\": \"01/06\", \"created_at\": \"2025-10-05T06:15:58.680611\", \"raw_amount\": \"150.00\", \"description\": \"2359 i 12/30 11005 i 12/23 28.25 11013 i 100.00\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"2359 i 12/30 11005 i 12/23 28.25 11013 i 100.00\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(209,1,'2024-01-15',300.00,'2360 i 12/24 11006 i 12/30 226.00 11017i 299.00','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-15\", \"amount\": 300.0, \"org_id\": 1, \"raw_date\": \"01/15\", \"created_at\": \"2025-10-05T06:15:58.680624\", \"raw_amount\": \"300.00\", \"description\": \"2360 i 12/24 11006 i 12/30 226.00 11017*i 299.00\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"2360 i 12/24 11006 i 12/30 226.00 11017*i 299.00\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(210,1,'2024-01-14',100.00,'10999i 12/23 11007 i 12/20 353.00 11018 i 30.00','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-14\", \"amount\": 100.0, \"org_id\": 1, \"raw_date\": \"01/14\", \"created_at\": \"2025-10-05T06:15:58.680632\", \"raw_amount\": \"100.00\", \"description\": \"10999*i 12/23 11007 i 12/20 353.00 11018 i 30.00\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"10999*i 12/23 11007 i 12/20 353.00 11018 i 30.00\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(211,1,'2024-01-15',930.16,'11000 i 12/24 11008 i 12/18 24.76 11021i 25.00','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-15\", \"amount\": 930.16, \"org_id\": 1, \"raw_date\": \"01/15\", \"created_at\": \"2025-10-05T06:15:58.680640\", \"raw_amount\": \"930.16\", \"description\": \"11000 i 12/24 11008 i 12/18 24.76 11021*i 25.00\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"11000 i 12/24 11008 i 12/18 24.76 11021*i 25.00\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(212,1,'2024-01-13',94.50,'11001 i 12/23 11009 i 12/19 34.00 11022 i 226.00','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-13\", \"amount\": 94.5, \"org_id\": 1, \"raw_date\": \"01/13\", \"created_at\": \"2025-10-05T06:15:58.680648\", \"raw_amount\": \"94.50\", \"description\": \"11001 i 12/23 11009 i 12/19 34.00 11022 i 226.00\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"11001 i 12/23 11009 i 12/19 34.00 11022 i 226.00\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(213,1,'2024-01-13',48.00,'11002 i 12/20 11010 i 12/19 225.00 11023 i 25.00','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-13\", \"amount\": 48.0, \"org_id\": 1, \"raw_date\": \"01/13\", \"created_at\": \"2025-10-05T06:15:58.680655\", \"raw_amount\": \"48.00\", \"description\": \"11002 i 12/20 11010 i 12/19 225.00 11023 i 25.00\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"11002 i 12/20 11010 i 12/19 225.00 11023 i 25.00\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(214,1,'2024-01-15',43.30,'11003 i 12/19 11011 i 12/18 26.10 11024 i 100.00','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-15\", \"amount\": 43.3, \"org_id\": 1, \"raw_date\": \"01/15\", \"created_at\": \"2025-10-05T06:15:58.680663\", \"raw_amount\": \"43.30\", \"description\": \"11003 i 12/19 11011 i 12/18 26.10 11024 i 100.00\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"11003 i 12/19 11011 i 12/18 26.10 11024 i 100.00\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(215,1,'2024-01-14',290.00,'11004 i 12/24 11012 i 12/18 100.00 11027i 100.00','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-14\", \"amount\": 290.0, \"org_id\": 1, \"raw_date\": \"01/14\", \"created_at\": \"2025-10-05T06:15:58.680671\", \"raw_amount\": \"290.00\", \"description\": \"11004 i 12/24 11012 i 12/18 100.00 11027*i 100.00\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"11004 i 12/24 11012 i 12/18 100.00 11027*i 100.00\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(216,1,'2024-12-17',65.00,'5/3 ONLINE PYMT TO GUIDING LI- ACCT 255','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-17\", \"amount\": 65.0, \"org_id\": 1, \"raw_date\": \"12/17\", \"created_at\": \"2025-10-05T06:15:58.680678\", \"raw_amount\": \"65.00\", \"description\": \"5/3 ONLINE PYMT TO GUIDING LI- ACCT 255\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO GUIDING LI- ACCT 255\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(217,1,'2024-12-19',136.77,'5/3 ONLINE PYMT TO AT&T MOBIL- ACCT XXXXXXXX5668','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-19\", \"amount\": 136.77, \"org_id\": 1, \"raw_date\": \"12/19\", \"created_at\": \"2025-10-05T06:15:58.680686\", \"raw_amount\": \"136.77\", \"description\": \"5/3 ONLINE PYMT TO AT&T MOBIL- ACCT XXXXXXXX5668\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO AT&T MOBIL- ACCT XXXXXXXX5668\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(218,1,'2024-12-20',800.00,'5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF  01078762412','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-20\", \"amount\": 800.0, \"org_id\": 1, \"raw_date\": \"12/20\", \"created_at\": \"2025-10-05T06:15:58.680694\", \"raw_amount\": \"800.00\", \"description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01078762412\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01078762412\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(219,1,'2024-12-23',140.91,'5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX3762','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-23\", \"amount\": 140.91, \"org_id\": 1, \"raw_date\": \"12/23\", \"created_at\": \"2025-10-05T06:15:58.680702\", \"raw_amount\": \"140.91\", \"description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX3762\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO CONSUMERS- ACCT XXXXXXXX3762\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(220,1,'2024-12-23',1000.00,'5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF  01079870543','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-23\", \"amount\": 1000.0, \"org_id\": 1, \"raw_date\": \"12/23\", \"created_at\": \"2025-10-05T06:15:58.680710\", \"raw_amount\": \"1,000.00\", \"description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01079870543\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01079870543\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(221,1,'2024-12-27',1800.00,'5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF  01080233293','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-27\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"12/27\", \"created_at\": \"2025-10-05T06:15:58.680718\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01080233293\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01080233293\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(222,1,'2024-12-30',67.00,'5/3 ONLINE PYMT TO PRIORITY H- ACCT XXXXX9392','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-30\", \"amount\": 67.0, \"org_id\": 1, \"raw_date\": \"12/30\", \"created_at\": \"2025-10-05T06:15:58.680725\", \"raw_amount\": \"67.00\", \"description\": \"5/3 ONLINE PYMT TO PRIORITY H- ACCT XXXXX9392\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO PRIORITY H- ACCT XXXXX9392\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(223,1,'2024-12-30',91.39,'5/3 ONLINE PYMT TO PRIORITY H- ACCT XXXXX7890','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-30\", \"amount\": 91.39, \"org_id\": 1, \"raw_date\": \"12/30\", \"created_at\": \"2025-10-05T06:15:58.680734\", \"raw_amount\": \"91.39\", \"description\": \"5/3 ONLINE PYMT TO PRIORITY H- ACCT XXXXX7890\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO PRIORITY H- ACCT XXXXX7890\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(224,1,'2024-12-30',204.10,'5/3 ONLINE PYMT TO AMERICAN E- ACCT XXXXXXXXXXX3009','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-30\", \"amount\": 204.1, \"org_id\": 1, \"raw_date\": \"12/30\", \"created_at\": \"2025-10-05T06:15:58.680741\", \"raw_amount\": \"204.10\", \"description\": \"5/3 ONLINE PYMT TO AMERICAN E- ACCT XXXXXXXXXXX3009\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO AMERICAN E- ACCT XXXXXXXXXXX3009\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(225,1,'2024-01-03',1800.00,'5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF  01080233495','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-03\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"01/03\", \"created_at\": \"2025-10-05T06:15:58.680749\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01080233495\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01080233495\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(226,1,'2024-01-07',80.24,'5/3 ONLINE PYMT TO AT&T U-VER- ACCT XXXXX6008','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-07\", \"amount\": 80.24, \"org_id\": 1, \"raw_date\": \"01/07\", \"created_at\": \"2025-10-05T06:15:58.680757\", \"raw_amount\": \"80.24\", \"description\": \"5/3 ONLINE PYMT TO AT&T U-VER- ACCT XXXXX6008\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO AT&T U-VER- ACCT XXXXX6008\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(227,1,'2024-01-10',70.00,'5/3 ONLINE PYMT TO GUIDING LI- ACCT 255','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-10\", \"amount\": 70.0, \"org_id\": 1, \"raw_date\": \"01/10\", \"created_at\": \"2025-10-05T06:15:58.680764\", \"raw_amount\": \"70.00\", \"description\": \"5/3 ONLINE PYMT TO GUIDING LI- ACCT 255\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO GUIDING LI- ACCT 255\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(228,1,'2024-01-10',375.00,'5/3 ONLINE PYMT TO SAMARITAN- ACCT 8855','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-10\", \"amount\": 375.0, \"org_id\": 1, \"raw_date\": \"01/10\", \"created_at\": \"2025-10-05T06:15:58.680772\", \"raw_amount\": \"375.00\", \"description\": \"5/3 ONLINE PYMT TO SAMARITAN\'- ACCT 8855\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO SAMARITAN\'- ACCT 8855\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(229,1,'2024-01-10',1800.00,'5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF  01080233871','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-10\", \"amount\": 1800.0, \"org_id\": 1, \"raw_date\": \"01/10\", \"created_at\": \"2025-10-05T06:15:58.680780\", \"raw_amount\": \"1,800.00\", \"description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01080233871\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER TO CK: XXXXXX5938 REF # 01080233871\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(230,1,'2024-01-13',200.00,'5/3 ONLINE PYMT TO AT&T U-VER- ACCT XXXXX8457','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-13\", \"amount\": 200.0, \"org_id\": 1, \"raw_date\": \"01/13\", \"created_at\": \"2025-10-05T06:15:58.680787\", \"raw_amount\": \"200.00\", \"description\": \"5/3 ONLINE PYMT TO AT&T U-VER- ACCT XXXXX8457\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE PYMT TO AT&T U-VER- ACCT XXXXX8457\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(231,1,'2024-12-16',4770.00,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-16\", \"amount\": 4770.0, \"org_id\": 1, \"raw_date\": \"12/16\", \"created_at\": \"2025-10-05T06:15:58.680795\", \"raw_amount\": \"4,770.00\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(232,1,'2024-12-19',134.00,'WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER R Patterson 121924','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-19\", \"amount\": 134.0, \"org_id\": 1, \"raw_date\": \"12/19\", \"created_at\": \"2025-10-05T06:15:58.680803\", \"raw_amount\": \"134.00\", \"description\": \"WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER R Patterson 121924\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER R Patterson 121924\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(233,1,'2024-12-19',302.00,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-19\", \"amount\": 302.0, \"org_id\": 1, \"raw_date\": \"12/19\", \"created_at\": \"2025-10-05T06:15:58.680810\", \"raw_amount\": \"302.00\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(234,1,'2024-12-20',93.74,'SHS OF WEST MICH PAY 731682 6semk34l784 122024','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-20\", \"amount\": 93.74, \"org_id\": 1, \"raw_date\": \"12/20\", \"created_at\": \"2025-10-05T06:15:58.680818\", \"raw_amount\": \"93.74\", \"description\": \"SHS OF WEST MICH PAY 731682 6semk34l784 122024\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"SHS OF WEST MICH PAY 731682 6semk34l784 122024\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(235,1,'2024-12-23',25.00,'WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER R Patterson 122324','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-23\", \"amount\": 25.0, \"org_id\": 1, \"raw_date\": \"12/23\", \"created_at\": \"2025-10-05T06:15:58.680826\", \"raw_amount\": \"25.00\", \"description\": \"WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER R Patterson 122324\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER R Patterson 122324\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(236,1,'2024-12-23',1956.00,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-23\", \"amount\": 1956.0, \"org_id\": 1, \"raw_date\": \"12/23\", \"created_at\": \"2025-10-05T06:15:58.680834\", \"raw_amount\": \"1,956.00\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(237,1,'2024-12-26',33.56,'SHS OF WEST MICH PAY 890258 6semk36550q 122624','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-26\", \"amount\": 33.56, \"org_id\": 1, \"raw_date\": \"12/26\", \"created_at\": \"2025-10-05T06:15:58.680842\", \"raw_amount\": \"33.56\", \"description\": \"SHS OF WEST MICH PAY 890258 6semk36550q 122624\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"SHS OF WEST MICH PAY 890258 6semk36550q 122624\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(238,1,'2024-12-30',227.00,'WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER V Patterson 123024','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-30\", \"amount\": 227.0, \"org_id\": 1, \"raw_date\": \"12/30\", \"created_at\": \"2025-10-05T06:15:58.680849\", \"raw_amount\": \"227.00\", \"description\": \"WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER V Patterson 123024\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER V Patterson 123024\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(239,1,'2024-12-30',3211.00,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-30\", \"amount\": 3211.0, \"org_id\": 1, \"raw_date\": \"12/30\", \"created_at\": \"2025-10-05T06:15:58.680857\", \"raw_amount\": \"3,211.00\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(240,1,'2024-12-31',344.00,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-12-31\", \"amount\": 344.0, \"org_id\": 1, \"raw_date\": \"12/31\", \"created_at\": \"2025-10-05T06:15:58.680865\", \"raw_amount\": \"344.00\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(241,1,'2024-01-02',416.00,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-02\", \"amount\": 416.0, \"org_id\": 1, \"raw_date\": \"01/02\", \"created_at\": \"2025-10-05T06:15:58.680872\", \"raw_amount\": \"416.00\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(242,1,'2024-01-03',1231.73,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-03\", \"amount\": 1231.73, \"org_id\": 1, \"raw_date\": \"01/03\", \"created_at\": \"2025-10-05T06:15:58.680880\", \"raw_amount\": \"1,231.73\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(243,1,'2024-01-03',1250.00,'5/3 ONLINE TRANSFER FROM CK: XXXXXX5938 REF  01080234599','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-03\", \"amount\": 1250.0, \"org_id\": 1, \"raw_date\": \"01/03\", \"created_at\": \"2025-10-05T06:15:58.680888\", \"raw_amount\": \"1,250.00\", \"description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX5938 REF # 01080234599\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"5/3 ONLINE TRANSFER FROM CK: XXXXXX5938 REF # 01080234599\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(244,1,'2024-01-06',2933.01,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-06\", \"amount\": 2933.01, \"org_id\": 1, \"raw_date\": \"01/06\", \"created_at\": \"2025-10-05T06:15:58.680895\", \"raw_amount\": \"2,933.01\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(245,1,'2024-01-09',84.00,'WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER R Patterson 010925','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-09\", \"amount\": 84.0, \"org_id\": 1, \"raw_date\": \"01/09\", \"created_at\": \"2025-10-05T06:15:58.680903\", \"raw_amount\": \"84.00\", \"description\": \"WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER R Patterson 010925\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"WEB INITIATED PAYMENT AT USAA EXT-INTRNT TRANSFER R Patterson 010925\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(246,1,'2024-01-09',411.00,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-09\", \"amount\": 411.0, \"org_id\": 1, \"raw_date\": \"01/09\", \"created_at\": \"2025-10-05T06:15:58.680911\", \"raw_amount\": \"411.00\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00'),(247,1,'2024-01-13',1665.00,'DEPOSIT','CREDIT',NULL,NULL,NULL,NULL,18,'{\"date\": \"2024-01-13\", \"amount\": 1665.0, \"org_id\": 1, \"raw_date\": \"01/13\", \"created_at\": \"2025-10-05T06:15:58.680917\", \"raw_amount\": \"1,665.00\", \"description\": \"DEPOSIT\", \"file_format\": \"PDF\", \"source_file\": \"/mnt/c/Users/NewUser/Downloads/Statement2025-01-15 (1)  rol.pdf\", \"raw_description\": \"DEPOSIT\", \"extraction_method\": \"docling\"}','2025-10-05 06:16:00','2025-10-05 06:16:00');
/*!40000 ALTER TABLE `transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `vw_account_transaction_summary`
--

DROP TABLE IF EXISTS `vw_account_transaction_summary`;
/*!50001 DROP VIEW IF EXISTS `vw_account_transaction_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_account_transaction_summary` AS SELECT 
 1 AS `org_id`,
 1 AS `account_number`,
 1 AS `total_transactions`,
 1 AS `total_credits`,
 1 AS `total_debits`,
 1 AS `total_transfers`,
 1 AS `net_amount`,
 1 AS `first_transaction_date`,
 1 AS `last_transaction_date`,
 1 AS `transaction_days`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_balance_by_org`
--

DROP TABLE IF EXISTS `vw_balance_by_org`;
/*!50001 DROP VIEW IF EXISTS `vw_balance_by_org`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_balance_by_org` AS SELECT 
 1 AS `org_id`,
 1 AS `org_name`,
 1 AS `org_type`,
 1 AS `total_payments`,
 1 AS `total_expenses`,
 1 AS `net_balance`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_daily_transaction_summary`
--

DROP TABLE IF EXISTS `vw_daily_transaction_summary`;
/*!50001 DROP VIEW IF EXISTS `vw_daily_transaction_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_daily_transaction_summary` AS SELECT 
 1 AS `org_id`,
 1 AS `transaction_date`,
 1 AS `transaction_type`,
 1 AS `transaction_count`,
 1 AS `total_amount`,
 1 AS `avg_amount`,
 1 AS `min_amount`,
 1 AS `max_amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_duplicate_analysis`
--

DROP TABLE IF EXISTS `vw_duplicate_analysis`;
/*!50001 DROP VIEW IF EXISTS `vw_duplicate_analysis`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_duplicate_analysis` AS SELECT 
 1 AS `flag_id`,
 1 AS `transaction_id`,
 1 AS `duplicate_transaction_id`,
 1 AS `confidence_score`,
 1 AS `flag_status`,
 1 AS `original_date`,
 1 AS `original_amount`,
 1 AS `original_description`,
 1 AS `duplicate_date`,
 1 AS `duplicate_amount`,
 1 AS `duplicate_description`,
 1 AS `date_difference_days`,
 1 AS `amount_difference`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_import_batch_summary`
--

DROP TABLE IF EXISTS `vw_import_batch_summary`;
/*!50001 DROP VIEW IF EXISTS `vw_import_batch_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_import_batch_summary` AS SELECT 
 1 AS `id`,
 1 AS `org_id`,
 1 AS `filename`,
 1 AS `file_format`,
 1 AS `import_date`,
 1 AS `total_transactions`,
 1 AS `successful_imports`,
 1 AS `failed_imports`,
 1 AS `duplicate_count`,
 1 AS `status`,
 1 AS `actual_transactions`,
 1 AS `total_debits`,
 1 AS `total_credits`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_import_performance`
--

DROP TABLE IF EXISTS `vw_import_performance`;
/*!50001 DROP VIEW IF EXISTS `vw_import_performance`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_import_performance` AS SELECT 
 1 AS `batch_id`,
 1 AS `org_id`,
 1 AS `filename`,
 1 AS `file_format`,
 1 AS `import_date`,
 1 AS `status`,
 1 AS `total_transactions`,
 1 AS `successful_imports`,
 1 AS `failed_imports`,
 1 AS `duplicate_count`,
 1 AS `success_rate`,
 1 AS `actual_db_records`,
 1 AS `data_consistency`,
 1 AS `earliest_transaction`,
 1 AS `latest_transaction`,
 1 AS `total_amount_imported`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_large_transactions`
--

DROP TABLE IF EXISTS `vw_large_transactions`;
/*!50001 DROP VIEW IF EXISTS `vw_large_transactions`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_large_transactions` AS SELECT 
 1 AS `id`,
 1 AS `org_id`,
 1 AS `transaction_date`,
 1 AS `amount`,
 1 AS `description`,
 1 AS `transaction_type`,
 1 AS `account_number`,
 1 AS `std_deviations_from_mean`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_monthly_balance_progression`
--

DROP TABLE IF EXISTS `vw_monthly_balance_progression`;
/*!50001 DROP VIEW IF EXISTS `vw_monthly_balance_progression`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_monthly_balance_progression` AS SELECT 
 1 AS `org_id`,
 1 AS `account_number`,
 1 AS `month_year`,
 1 AS `transaction_count`,
 1 AS `net_change`,
 1 AS `ending_balance`,
 1 AS `lowest_balance`,
 1 AS `avg_balance`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_monthly_expense_summary`
--

DROP TABLE IF EXISTS `vw_monthly_expense_summary`;
/*!50001 DROP VIEW IF EXISTS `vw_monthly_expense_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_monthly_expense_summary` AS SELECT 
 1 AS `org_name`,
 1 AS `month_start`,
 1 AS `category`,
 1 AS `total_amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_monthly_payment_summary`
--

DROP TABLE IF EXISTS `vw_monthly_payment_summary`;
/*!50001 DROP VIEW IF EXISTS `vw_monthly_payment_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_monthly_payment_summary` AS SELECT 
 1 AS `org_name`,
 1 AS `month_start`,
 1 AS `payment_type`,
 1 AS `total_amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_monthly_transaction_summary`
--

DROP TABLE IF EXISTS `vw_monthly_transaction_summary`;
/*!50001 DROP VIEW IF EXISTS `vw_monthly_transaction_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_monthly_transaction_summary` AS SELECT 
 1 AS `org_id`,
 1 AS `month_year`,
 1 AS `transaction_type`,
 1 AS `transaction_count`,
 1 AS `total_amount`,
 1 AS `avg_amount`,
 1 AS `min_amount`,
 1 AS `max_amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_recent_transactions`
--

DROP TABLE IF EXISTS `vw_recent_transactions`;
/*!50001 DROP VIEW IF EXISTS `vw_recent_transactions`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_recent_transactions` AS SELECT 
 1 AS `id`,
 1 AS `org_id`,
 1 AS `transaction_date`,
 1 AS `amount`,
 1 AS `description`,
 1 AS `transaction_type`,
 1 AS `account_number`,
 1 AS `bank_reference`,
 1 AS `balance_after`,
 1 AS `import_batch_id`,
 1 AS `created_at`,
 1 AS `days_ago`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_report_financials`
--

DROP TABLE IF EXISTS `vw_report_financials`;
/*!50001 DROP VIEW IF EXISTS `vw_report_financials`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_report_financials` AS SELECT 
 1 AS `report_id`,
 1 AS `title`,
 1 AS `start_date`,
 1 AS `end_date`,
 1 AS `nonprofit_expenses`,
 1 AS `personal_expenses`,
 1 AS `total_payments`,
 1 AS `donations`,
 1 AS `grants`,
 1 AS `net_all_orgs`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_transaction_patterns`
--

DROP TABLE IF EXISTS `vw_transaction_patterns`;
/*!50001 DROP VIEW IF EXISTS `vw_transaction_patterns`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_transaction_patterns` AS SELECT 
 1 AS `org_id`,
 1 AS `transaction_pattern`,
 1 AS `transaction_type`,
 1 AS `frequency`,
 1 AS `total_amount`,
 1 AS `avg_amount`,
 1 AS `min_amount`,
 1 AS `max_amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_weekly_transaction_summary`
--

DROP TABLE IF EXISTS `vw_weekly_transaction_summary`;
/*!50001 DROP VIEW IF EXISTS `vw_weekly_transaction_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_weekly_transaction_summary` AS SELECT 
 1 AS `org_id`,
 1 AS `year`,
 1 AS `week_number`,
 1 AS `week_start_date`,
 1 AS `transaction_type`,
 1 AS `transaction_count`,
 1 AS `total_amount`,
 1 AS `avg_amount`,
 1 AS `min_amount`,
 1 AS `max_amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `vw_account_transaction_summary`
--

/*!50001 DROP VIEW IF EXISTS `vw_account_transaction_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_account_transaction_summary` AS select `transactions`.`org_id` AS `org_id`,`transactions`.`account_number` AS `account_number`,count(0) AS `total_transactions`,sum((case when (`transactions`.`transaction_type` = 'CREDIT') then `transactions`.`amount` else 0 end)) AS `total_credits`,sum((case when (`transactions`.`transaction_type` = 'DEBIT') then `transactions`.`amount` else 0 end)) AS `total_debits`,sum((case when (`transactions`.`transaction_type` = 'TRANSFER') then `transactions`.`amount` else 0 end)) AS `total_transfers`,sum(`transactions`.`amount`) AS `net_amount`,min(`transactions`.`transaction_date`) AS `first_transaction_date`,max(`transactions`.`transaction_date`) AS `last_transaction_date`,count(distinct `transactions`.`transaction_date`) AS `transaction_days` from `transactions` where (`transactions`.`account_number` is not null) group by `transactions`.`org_id`,`transactions`.`account_number` order by `total_transactions` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_balance_by_org`
--

/*!50001 DROP VIEW IF EXISTS `vw_balance_by_org`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_balance_by_org` AS select `o`.`id` AS `org_id`,`o`.`name` AS `org_name`,`o`.`type` AS `org_type`,ifnull((select sum(`p`.`amount`) from `payments` `p` where (`p`.`org_id` = `o`.`id`)),0) AS `total_payments`,ifnull((select sum(`e`.`amount`) from `expenses` `e` where (`e`.`org_id` = `o`.`id`)),0) AS `total_expenses`,(ifnull((select sum(`p`.`amount`) from `payments` `p` where (`p`.`org_id` = `o`.`id`)),0) - ifnull((select sum(`e`.`amount`) from `expenses` `e` where (`e`.`org_id` = `o`.`id`)),0)) AS `net_balance` from `organizations` `o` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_daily_transaction_summary`
--

/*!50001 DROP VIEW IF EXISTS `vw_daily_transaction_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_daily_transaction_summary` AS select `transactions`.`org_id` AS `org_id`,`transactions`.`transaction_date` AS `transaction_date`,`transactions`.`transaction_type` AS `transaction_type`,count(0) AS `transaction_count`,sum(`transactions`.`amount`) AS `total_amount`,avg(`transactions`.`amount`) AS `avg_amount`,min(`transactions`.`amount`) AS `min_amount`,max(`transactions`.`amount`) AS `max_amount` from `transactions` group by `transactions`.`org_id`,`transactions`.`transaction_date`,`transactions`.`transaction_type` order by `transactions`.`transaction_date` desc,`transactions`.`transaction_type` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_duplicate_analysis`
--

/*!50001 DROP VIEW IF EXISTS `vw_duplicate_analysis`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_duplicate_analysis` AS select `df`.`id` AS `flag_id`,`df`.`transaction_id` AS `transaction_id`,`df`.`duplicate_transaction_id` AS `duplicate_transaction_id`,`df`.`confidence_score` AS `confidence_score`,`df`.`status` AS `flag_status`,`t1`.`transaction_date` AS `original_date`,`t1`.`amount` AS `original_amount`,`t1`.`description` AS `original_description`,`t2`.`transaction_date` AS `duplicate_date`,`t2`.`amount` AS `duplicate_amount`,`t2`.`description` AS `duplicate_description`,abs((to_days(`t1`.`transaction_date`) - to_days(`t2`.`transaction_date`))) AS `date_difference_days`,abs((`t1`.`amount` - `t2`.`amount`)) AS `amount_difference` from ((`duplicate_flags` `df` join `transactions` `t1` on((`df`.`transaction_id` = `t1`.`id`))) join `transactions` `t2` on((`df`.`duplicate_transaction_id` = `t2`.`id`))) order by `df`.`confidence_score` desc,`df`.`created_at` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_import_batch_summary`
--

/*!50001 DROP VIEW IF EXISTS `vw_import_batch_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_import_batch_summary` AS select `ib`.`id` AS `id`,`ib`.`org_id` AS `org_id`,`ib`.`filename` AS `filename`,`ib`.`file_format` AS `file_format`,`ib`.`import_date` AS `import_date`,`ib`.`total_transactions` AS `total_transactions`,`ib`.`successful_imports` AS `successful_imports`,`ib`.`failed_imports` AS `failed_imports`,`ib`.`duplicate_count` AS `duplicate_count`,`ib`.`status` AS `status`,count(`t`.`id`) AS `actual_transactions`,coalesce(sum((case when (`t`.`transaction_type` = 'DEBIT') then `t`.`amount` else 0 end)),0) AS `total_debits`,coalesce(sum((case when (`t`.`transaction_type` = 'CREDIT') then `t`.`amount` else 0 end)),0) AS `total_credits` from (`import_batches` `ib` left join `transactions` `t` on((`ib`.`id` = `t`.`import_batch_id`))) group by `ib`.`id`,`ib`.`org_id`,`ib`.`filename`,`ib`.`file_format`,`ib`.`import_date`,`ib`.`total_transactions`,`ib`.`successful_imports`,`ib`.`failed_imports`,`ib`.`duplicate_count`,`ib`.`status` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_import_performance`
--

/*!50001 DROP VIEW IF EXISTS `vw_import_performance`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_import_performance` AS select `ib`.`id` AS `batch_id`,`ib`.`org_id` AS `org_id`,`ib`.`filename` AS `filename`,`ib`.`file_format` AS `file_format`,`ib`.`import_date` AS `import_date`,`ib`.`status` AS `status`,`ib`.`total_transactions` AS `total_transactions`,`ib`.`successful_imports` AS `successful_imports`,`ib`.`failed_imports` AS `failed_imports`,`ib`.`duplicate_count` AS `duplicate_count`,round(((`ib`.`successful_imports` / `ib`.`total_transactions`) * 100),2) AS `success_rate`,count(`t`.`id`) AS `actual_db_records`,(case when (count(`t`.`id`) = `ib`.`successful_imports`) then 'Consistent' else 'Mismatch' end) AS `data_consistency`,min(`t`.`transaction_date`) AS `earliest_transaction`,max(`t`.`transaction_date`) AS `latest_transaction`,sum(`t`.`amount`) AS `total_amount_imported` from (`import_batches` `ib` left join `transactions` `t` on((`ib`.`id` = `t`.`import_batch_id`))) group by `ib`.`id`,`ib`.`org_id`,`ib`.`filename`,`ib`.`file_format`,`ib`.`import_date`,`ib`.`status`,`ib`.`total_transactions`,`ib`.`successful_imports`,`ib`.`failed_imports`,`ib`.`duplicate_count` order by `ib`.`import_date` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_large_transactions`
--

/*!50001 DROP VIEW IF EXISTS `vw_large_transactions`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_large_transactions` AS select `t`.`id` AS `id`,`t`.`org_id` AS `org_id`,`t`.`transaction_date` AS `transaction_date`,`t`.`amount` AS `amount`,`t`.`description` AS `description`,`t`.`transaction_type` AS `transaction_type`,`t`.`account_number` AS `account_number`,round(((`t`.`amount` - `stats`.`avg_amount`) / `stats`.`std_amount`),2) AS `std_deviations_from_mean` from (`transactions` `t` join (select avg(`transactions`.`amount`) AS `avg_amount`,std(`transactions`.`amount`) AS `std_amount` from `transactions` where (`transactions`.`org_id` = 1)) `stats`) where (`t`.`amount` > (`stats`.`avg_amount` + `stats`.`std_amount`)) order by `t`.`amount` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_monthly_balance_progression`
--

/*!50001 DROP VIEW IF EXISTS `vw_monthly_balance_progression`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_monthly_balance_progression` AS select `transactions`.`org_id` AS `org_id`,`transactions`.`account_number` AS `account_number`,date_format(`transactions`.`transaction_date`,'%Y-%m') AS `month_year`,count(0) AS `transaction_count`,sum(`transactions`.`amount`) AS `net_change`,max(`transactions`.`balance_after`) AS `ending_balance`,min(`transactions`.`balance_after`) AS `lowest_balance`,avg(`transactions`.`balance_after`) AS `avg_balance` from `transactions` where (`transactions`.`balance_after` is not null) group by `transactions`.`org_id`,`transactions`.`account_number`,date_format(`transactions`.`transaction_date`,'%Y-%m') order by `month_year` desc,`transactions`.`account_number` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_monthly_expense_summary`
--

/*!50001 DROP VIEW IF EXISTS `vw_monthly_expense_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_monthly_expense_summary` AS select `o`.`name` AS `org_name`,date_format(`e`.`expense_date`,'%Y-%m-01') AS `month_start`,`c`.`name` AS `category`,sum(`e`.`amount`) AS `total_amount` from ((`expenses` `e` join `organizations` `o` on((`o`.`id` = `e`.`org_id`))) join `categories` `c` on(((`c`.`id` = `e`.`category_id`) and (`c`.`kind` = 'EXPENSE')))) group by `o`.`name`,date_format(`e`.`expense_date`,'%Y-%m-01'),`c`.`name` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_monthly_payment_summary`
--

/*!50001 DROP VIEW IF EXISTS `vw_monthly_payment_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_monthly_payment_summary` AS select `o`.`name` AS `org_name`,date_format(`p`.`payment_date`,'%Y-%m-01') AS `month_start`,`p`.`type` AS `payment_type`,sum(`p`.`amount`) AS `total_amount` from (`payments` `p` join `organizations` `o` on((`o`.`id` = `p`.`org_id`))) group by `o`.`name`,date_format(`p`.`payment_date`,'%Y-%m-01'),`p`.`type` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_monthly_transaction_summary`
--

/*!50001 DROP VIEW IF EXISTS `vw_monthly_transaction_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_monthly_transaction_summary` AS select `transactions`.`org_id` AS `org_id`,date_format(`transactions`.`transaction_date`,'%Y-%m') AS `month_year`,`transactions`.`transaction_type` AS `transaction_type`,count(0) AS `transaction_count`,sum(`transactions`.`amount`) AS `total_amount`,avg(`transactions`.`amount`) AS `avg_amount`,min(`transactions`.`amount`) AS `min_amount`,max(`transactions`.`amount`) AS `max_amount` from `transactions` group by `transactions`.`org_id`,date_format(`transactions`.`transaction_date`,'%Y-%m'),`transactions`.`transaction_type` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_recent_transactions`
--

/*!50001 DROP VIEW IF EXISTS `vw_recent_transactions`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_recent_transactions` AS select `transactions`.`id` AS `id`,`transactions`.`org_id` AS `org_id`,`transactions`.`transaction_date` AS `transaction_date`,`transactions`.`amount` AS `amount`,`transactions`.`description` AS `description`,`transactions`.`transaction_type` AS `transaction_type`,`transactions`.`account_number` AS `account_number`,`transactions`.`bank_reference` AS `bank_reference`,`transactions`.`balance_after` AS `balance_after`,`transactions`.`import_batch_id` AS `import_batch_id`,`transactions`.`created_at` AS `created_at`,(to_days(curdate()) - to_days(`transactions`.`transaction_date`)) AS `days_ago` from `transactions` where (`transactions`.`transaction_date` >= (curdate() - interval 30 day)) order by `transactions`.`transaction_date` desc,`transactions`.`id` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_report_financials`
--

/*!50001 DROP VIEW IF EXISTS `vw_report_financials`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_report_financials` AS select `r`.`id` AS `report_id`,`r`.`title` AS `title`,`r`.`start_date` AS `start_date`,`r`.`end_date` AS `end_date`,(select ifnull(sum(`e`.`amount`),0) from (`expenses` `e` join `organizations` `o` on((`o`.`id` = `e`.`org_id`))) where ((`e`.`expense_date` between `r`.`start_date` and `r`.`end_date`) and (`o`.`type` = 'NONPROFIT'))) AS `nonprofit_expenses`,(select ifnull(sum(`e`.`amount`),0) from (`expenses` `e` join `organizations` `o` on((`o`.`id` = `e`.`org_id`))) where ((`e`.`expense_date` between `r`.`start_date` and `r`.`end_date`) and (`o`.`type` = 'PERSONAL'))) AS `personal_expenses`,(select ifnull(sum(`p`.`amount`),0) from `payments` `p` where (`p`.`payment_date` between `r`.`start_date` and `r`.`end_date`)) AS `total_payments`,(select ifnull(sum(`p`.`amount`),0) from `payments` `p` where ((`p`.`payment_date` between `r`.`start_date` and `r`.`end_date`) and (`p`.`type` = 'DONATION'))) AS `donations`,(select ifnull(sum(`p`.`amount`),0) from `payments` `p` where ((`p`.`payment_date` between `r`.`start_date` and `r`.`end_date`) and (`p`.`type` = 'GRANT'))) AS `grants`,((select ifnull(sum(`p`.`amount`),0) from `payments` `p` where (`p`.`payment_date` between `r`.`start_date` and `r`.`end_date`)) - (select ifnull(sum(`e`.`amount`),0) from `expenses` `e` where (`e`.`expense_date` between `r`.`start_date` and `r`.`end_date`))) AS `net_all_orgs` from `reports` `r` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_transaction_patterns`
--

/*!50001 DROP VIEW IF EXISTS `vw_transaction_patterns`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_transaction_patterns` AS select `transactions`.`org_id` AS `org_id`,(case when (`transactions`.`description` like '%ONLINE TRANSFER%') then 'Online Transfer' when (`transactions`.`description` like '%ONLINE PYMT%') then 'Online Payment' when (`transactions`.`description` like '%ATM%') then 'ATM Transaction' when (`transactions`.`description` like '%DEBIT CARD%') then 'Debit Card' when (`transactions`.`description` like '%CHECK%') then 'Check' when (`transactions`.`description` like '%DEPOSIT%') then 'Deposit' when ((`transactions`.`description` like '%FEE%') or (`transactions`.`description` like '%CHARGE%')) then 'Fee/Charge' when (`transactions`.`description` like '%INTEREST%') then 'Interest' else 'Other' end) AS `transaction_pattern`,`transactions`.`transaction_type` AS `transaction_type`,count(0) AS `frequency`,sum(`transactions`.`amount`) AS `total_amount`,avg(`transactions`.`amount`) AS `avg_amount`,min(`transactions`.`amount`) AS `min_amount`,max(`transactions`.`amount`) AS `max_amount` from `transactions` group by `transactions`.`org_id`,`transaction_pattern`,`transactions`.`transaction_type` having (`frequency` > 0) order by `frequency` desc,`total_amount` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_weekly_transaction_summary`
--

/*!50001 DROP VIEW IF EXISTS `vw_weekly_transaction_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`adamsl`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_weekly_transaction_summary` AS select `transactions`.`org_id` AS `org_id`,year(`transactions`.`transaction_date`) AS `year`,week(`transactions`.`transaction_date`,1) AS `week_number`,cast((`transactions`.`transaction_date` - interval weekday(`transactions`.`transaction_date`) day) as date) AS `week_start_date`,`transactions`.`transaction_type` AS `transaction_type`,count(0) AS `transaction_count`,sum(`transactions`.`amount`) AS `total_amount`,avg(`transactions`.`amount`) AS `avg_amount`,min(`transactions`.`amount`) AS `min_amount`,max(`transactions`.`amount`) AS `max_amount` from `transactions` group by `transactions`.`org_id`,year(`transactions`.`transaction_date`),week(`transactions`.`transaction_date`,1),`transactions`.`transaction_type` order by `year` desc,`week_number` desc,`transactions`.`transaction_type` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-01  1:39:12
