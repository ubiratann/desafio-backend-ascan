DROP DATABASE IF EXISTS subscriptions;

CREATE DATABASE subscriptions;

USE subscriptions;

CREATE TABLE user(
    id        INT NOT NULL AUTO_INCREMENT,
    full_name VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE status(
    id          INT NOT NULL AUTO_INCREMENT,
    status_name VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE subscription(
    id         INT NOT NULL AUTO_INCREMENT,
    user_id    INT NOT NULL,
    status_id  INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL DEFAULT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(user_id) 
        REFERENCES user(id)
        ON DELETE CASCADE,
    FOREIGN KEY(status_id)
         REFERENCES status(id)
         ON DELETE CASCADE
);


CREATE TABLE event_history(
    id              INT NOT NULL AUTO_INCREMENT,
    subscription_id INT NOT NULL,
    type            VARCHAR(255) NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id),
    FOREIGN KEY(subscription_id)
        REFERENCES subscription(id)
        ON DELETE CASCADE
);