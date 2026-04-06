#  Event Booking and Notification System


## Project Setups :- 

#### clone repository : 

    git clone https://github.com/suchit-hirani-python-ak/Event-Booking-Notification-System.git

    cd Event-Booking-Notification-System

## Project docker commands : 

    docker compose up -d --build

    docker compose logs -f 

### Folder structure 

#### app/api 

- This contains four files for different routers.


    1. user route : This contain register endpoint , login endpoint and refresh endpoint for refresh token, super admin, delete account.

    2. event route : In this admin can able to create event , update event, delete event. Wheres event all, event by id is open for all.

    3. booking route : This route contain 2 endpoints can able to book event and can see his/her own bookings .

#### app/core

- This contains 3 files. 

    1. congifg.py : This file contain all information related to env file.

    2. security.py : This file contain redis server, oauth2scheme bearer, generate access and refresh token.

### app/depandencies

- This contain depandency file

    1. depandency.py: This file contain dependancy of redis, role checker and get current user

#### app/db 

- This conatains 2 db related files.

    1. base.py : Conatins base class for database schemas so there is no error of circular import.

    2. session.py : Contains async mongoclient connection

#### app/exception 

- This contains custom exception classes.

    1. exceptions.py : Contains custom exception classes.

### app/middlerware
- This contains 2 files

    1. ratelimiting.py: Implemented rate limiting by redis and algorithm is sliding window

    2. request_logs.py: implement logs using celery 

#### app/repository

- This contain all collection with queries ajd interaction of database 



#### app/schemas

- It has pydentic schemas for request and response model.

#### app/service

- It conatain business logic and exception handling.

### app/utils

- It contain all nacessary helper function like celery, redis, retry notification

### app/utils/templates

- It contain template related to login and event booking notification

### app/tests

- In this i followed unit testing of each file by using magic mock and async mock 

- test coverage is 92%

### To run test cases

    pytest --cov

### Some important logics of functionalities.

- Refresh token : 

    *  Validation: Upon receiving a refresh token, the system verifies its authenticity and confirms the token_type is explicitly set to refresh.

    *   Concurrency & Security: The system performs a version check in database. If the stored token_version is greater than the version in the user's token, the request is rejected (this prevents the use of compromised or old tokens).

    *   Rotation: If the version matches, the system invalidates the current session by incrementing the version in the database and issuing a brand-new pair of Access and Refresh tokens.

- Redis-Backed Account Lockout :


    *   Real-time Tracking: Failed login attempts are tracked in Redis using a combination of the user's identifier and a failure counter(Maximum 5 attempts).

    *   Threshold Enforcement: During login, the system checks the Redis counter. If the max_attempts threshold is reached, a TTL (Time-To-Live) on the Redis key enforces the lockout period.

    *   Auto-Reset: Once the lockout duration expires, Redis automatically clears the key. A successful login also triggers an explicit reset of the failure counter(10 minutes cooldown).

    *   Used redis caching for fast response from user

- Retry Notification Machenacism :


    *   Real time notification sending and try to send 3 times by retry mechanism

- Docker compose :
    *   Architecture: The entire stack is Docker Compose, ensuring a consistent environment for the FastAPI and Redis.

    *   Security: Sensitive credentials are managed via a .env file that is injected into the containers at runtime but excluded from the image build (via .dockerignore) to prevent credential leakage.

    *   Reliability: The application service uses depends_on health checks to ensure the Redis and Database services are fully operational before the API starts accepting traffic(on single change it add data in db at 60sec so, data can be persistant).
