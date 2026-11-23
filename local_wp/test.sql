
-- CREATE Queries
CREATE TABLE pmn_municipality (
  municipalityId BIGINT(20) UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  municipalityName VARCHAR UNIQUE,
  sourceUrl VARCHAR,
  usesAPI BOOL DEFAULT true,
  active BOOL
);

CREATE TABLE pmn_meeting (
  meetingId BIGINT(20) UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  municipalityId BIGINT NOT NULL,
  committeeId BIGINT NOT NULL,
  meet_date DATETIME,
  title VARCHAR,
  meet_location VARCHAR,
  agendaURL VARCHAR,
  agendaSummarySource VARCHAR
  FOREIGN KEY (municipalityId) REFERENCES pmn_municipality (municipalityId)
  FOREIGN KEY (committeeId) REFERENCES pmn_committee (committeeId)
);

CREATE TABLE pmn_committee (
  committeeId BIGINT(20) UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  com_name VARCHAR NOT NULL
);

-- INSERT Queries
INSERT INTO pmn_municipality (
  municipalityName,
  sourceUrl
)
VALUES (

)
