-- Questionnaires management system: database schema

CREATE DATABASE IF NOT EXISTS questionnaires
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE questionnaires;

-- Users (also used by Django as the custom user table)
-- user_id is INT without UNSIGNED on purpose: Django's own tables
-- (e.g. django_admin_log) reference it with a signed INT
CREATE TABLE users (
    user_id           INT          NOT NULL AUTO_INCREMENT,
    username          VARCHAR(150) NOT NULL,
    email             VARCHAR(254) NOT NULL,
    password_hash     VARCHAR(128) NOT NULL,
    registration_date DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    is_staff          TINYINT(1)   NOT NULL DEFAULT 0,
    last_login        DATETIME(6)  NULL DEFAULT NULL,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_email (email)
) ENGINE = InnoDB;

-- Forms: surveys and tests
CREATE TABLE forms (
    form_id           INT          NOT NULL AUTO_INCREMENT,
    creator_id        INT          NULL,
    title             VARCHAR(255) NOT NULL,
    is_test           TINYINT(1)   NOT NULL DEFAULT 0,
    description       TEXT         NULL,
    restricted_access TINYINT(1)   NOT NULL DEFAULT 0,
    creation_time     DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    update_time       DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                   ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (form_id),
    CONSTRAINT fk_forms_creator
        FOREIGN KEY (creator_id) REFERENCES users (user_id)
        ON DELETE SET NULL
) ENGINE = InnoDB;