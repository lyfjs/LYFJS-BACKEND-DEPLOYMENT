CREATE TABLE users(
    id  INT AUTO_INCREMENT PRIMARY KEY,
	first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50) NOT NULL,
    lrn_number INT(12) NOT NULL,
    phone_number INT(12) NOT NULL,
    email VARCHAR(55) NOT NULL,
	facebook_link VARCHAR(155) NOT NULL,
    grade_level VARCHAR(12) NOT NULL,
    section VARCHAR(12) NOT NULL,
    adviser_name VARCHAR(50) NOT NULL,
    parent_phone_number VARCHAR(12) NOT NULL,
    parent_facebook_link VARCHAR(155) NOT NULL
    

);

CREATE TABLE admin(
    id  INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    password VARCHAR(30) NOT NULL
);


CREATE TABLE books(
	id  INT AUTO_INCREMENT PRIMARY KEY,
    level INT(2),
    bookType  VARCHAR(30),
    genre VARCHAR(30),
    strand VARCHAR(30),
    title VARCHAR(55),
    qtr VARCHAR(12),
    description VARCHAR(50),
    quantity INT(12),
    publisher VARCHAR(24),
    cover VARCHAR(155),
    link VARCHAR(155)
);