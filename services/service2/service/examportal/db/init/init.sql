USE examportal;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(30) NOT NULL UNIQUE,
    2fa VARCHAR(10)
);

CREATE TABLE exams(
    id INT PRIMARY KEY AUTO_INCREMENT,
    owner INT NOT NULL,
    name VARCHAR(100),
    questions TEXT,
    answers TEXT,
    correct VARCHAR(500),
    prize VARCHAR(32),
    FOREIGN KEY (owner) REFERENCES users(id)
);
