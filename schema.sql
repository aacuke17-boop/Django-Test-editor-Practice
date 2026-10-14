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

-- Questions of a form; order is defined by position
CREATE TABLE questions (
    question_id   INT           NOT NULL AUTO_INCREMENT,
    form_id       INT           NOT NULL,
    question_text TEXT          NOT NULL,
    points        DECIMAL(5, 2) NOT NULL DEFAULT 0,
    position      INT           NOT NULL DEFAULT 0,
    PRIMARY KEY (question_id),
    CONSTRAINT fk_questions_form
        FOREIGN KEY (form_id) REFERENCES forms (form_id)
        ON DELETE CASCADE
) ENGINE = InnoDB;

-- Answer options of a question; several can be correct
CREATE TABLE answer_options (
    option_id   INT          NOT NULL AUTO_INCREMENT,
    question_id INT          NOT NULL,
    option_text VARCHAR(500) NOT NULL,
    is_correct  TINYINT(1)   NOT NULL DEFAULT 0,
    position    INT          NOT NULL DEFAULT 0,
    PRIMARY KEY (option_id),
    CONSTRAINT fk_options_question
        FOREIGN KEY (question_id) REFERENCES questions (question_id)
        ON DELETE CASCADE
) ENGINE = InnoDB;

-- Access to restricted forms, granted by the author to registered users
CREATE TABLE access (
    form_id    INT         NOT NULL,
    user_id    INT         NOT NULL,
    granted_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (form_id, user_id),
    CONSTRAINT fk_access_form
        FOREIGN KEY (form_id) REFERENCES forms (form_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_access_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE
) ENGINE = InnoDB;

-- Attempts to take a form; user_id is NULL after the user is deleted
CREATE TABLE attempts (
    attempt_id   INT           NOT NULL AUTO_INCREMENT,
    form_id      INT           NOT NULL,
    user_id      INT           NULL,
    started_at   DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    completed_at DATETIME(6)   NULL DEFAULT NULL,
    score        DECIMAL(8, 2) NULL DEFAULT NULL,
    status       ENUM ('in_progress', 'completed') NOT NULL DEFAULT 'in_progress',
    PRIMARY KEY (attempt_id),
    CONSTRAINT fk_attempts_form
        FOREIGN KEY (form_id) REFERENCES forms (form_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_attempts_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE SET NULL
) ENGINE = InnoDB;

-- Options selected in an attempt (one row per selected option)
CREATE TABLE user_answers (
    answer_id   INT NOT NULL AUTO_INCREMENT,
    attempt_id  INT NOT NULL,
    question_id INT NOT NULL,
    option_id   INT NOT NULL,
    PRIMARY KEY (answer_id),
    UNIQUE KEY uq_user_answers_attempt_option (attempt_id, option_id),
    CONSTRAINT fk_user_answers_attempt
        FOREIGN KEY (attempt_id) REFERENCES attempts (attempt_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_answers_question
        FOREIGN KEY (question_id) REFERENCES questions (question_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_answers_option
        FOREIGN KEY (option_id) REFERENCES answer_options (option_id)
        ON DELETE CASCADE
) ENGINE = InnoDB;

-- Service user for anonymous attempts
-- email '-' is not a valid address and password '!' is an unusable password in Django,
-- so nobody can register or log in as Anonymous
INSERT INTO users (username, email, password_hash, is_staff)
VALUES ('Anonymous', '-', '!', 0);