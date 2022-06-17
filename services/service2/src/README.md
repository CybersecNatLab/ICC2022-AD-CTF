# CyberUniversity infrastructure

The modern CyberUni has adopted a Single Sign-On authentication model for all of its applications!

In order to interact with each of the three applications you will need a token, which can be obtained from the central Authentication Service.

## Authentication Service

The central AuthService lets you register users and get login tokens for all the other applications. There is an example client for reference using the pwntools Python's library, but you are free to create your own.

The core library for authentication is authlib, provided for all python versions from 3.8 to 3.11.

## ExamNotes

This application, after authentication with the token, let you save, read and list plaintext notes, that will be accessible only to you.

## EncryptedNotes

This is an application that lets you run functions on encrypted data. After logging in, you can set some private keyword and data, or run functions with other users' keywords as input.

You can find an example client that sets up a user, or evaluates the two functions.

## ExamPortal

This is the website where online exams are graded. After logging in with the token, you can take part in an exam and answer its questions; the exam will be passed only if you answer correctly to all the questions.
